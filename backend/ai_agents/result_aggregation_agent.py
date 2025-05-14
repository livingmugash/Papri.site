# backend/ai_agents/result_aggregation_agent.py
from collections import Counter, defaultdict # Add defaultdict
from django.conf import settings # For Vector DB settings
from api.models import VideoSource, Video, Transcript # For type hinting and accessing related models

# Example Milvus client - adapt if using another Vector DB
from pymilvus import Collection, connections 

class ResultAggregationAgent:
    def __init__(self):
         self.vector_db_collection_name = "papri_transcript_embeddings" # From TranscriptAnalyzer
         self.milvus_alias = "default"
         try:
             if not connections.has_connection(self.milvus_alias):
                 connections.connect(alias=self.milvus_alias, host=settings.VECTOR_DB_HOST, port=settings.VECTOR_DB_PORT)
             self.milvus_collection = Collection(self.vector_db_collection_name, using=self.milvus_alias)
             self.milvus_collection.load() # Ensure it's loaded (often done in _ensure_milvus_collection_exists)
             print("RARAgent: Milvus connection established and collection accessed.")
        except Exception as e:
             print(f"RARAgent: CRITICAL - Failed to connect to Milvus or access collection: {e}")
             self.milvus_collection = None
        pass # Milvus connection logic moved to a helper method for on-demand use or if using Django signals

    def _search_vector_db(self, query_embedding, top_k=20):
        if not self.milvus_collection or not query_embedding:
             return []
         try:
             search_params = {
                 "metric_type": "L2", # Or "IP"
                 "params": {"nprobe": 10}, # Adjust based on index type (e.g., "nprobe" for IVF_FLAT)
             }
 
             results = self.milvus_collection.search(
                 data=[query_embedding],
                 anns_field="embedding",
                 param=search_params,
                 limit=top_k,
                 expr=None, # Optional: filter expression (e.g., "video_papri_id in [1,2,3]")
                 output_fields=['transcript_db_id', 'video_papri_id'] # Fields to retrieve
             )
    
             semantic_hits = []
             for hits_for_query in results:
                 for hit in hits_for_query:
                     semantic_hits.append({
                         'transcript_id': hit.id, # This is the Transcript.id from Django
                         'video_papri_id': hit.entity.get('video_papri_id'), # Retrieve this if stored
                         'semantic_score': 1.0 - hit.distance if search_params["metric_type"] == "L2" else hit.distance, # Normalize L2 to similarity
                     })
             print(f"RARAgent: Vector DB search found {len(semantic_hits)} semantic hits.")
             return semantic_hits
         except Exception as e:
             print(f"RARAgent: Error searching Vector DB: {e}")
             return []
        print("RARAgent: _search_vector_db (Vector DB search) is currently a STUB.")
        return [] # Stub for now

    def aggregate_and_rank_results(self, persisted_video_source_objects, processed_query_data, all_analysis_data):
        # ... (query_keywords, query_embedding, semantic_scores_by_video_id calculation as before) ...
        query_keywords = set(k.lower() for k in processed_query_data.get('keywords', []))
        query_embedding = processed_query_data.get('query_embedding')
        semantic_scores_by_video_id = defaultdict(float)
        candidate_video_papri_ids = list(set(vs.video.id for vs in persisted_video_source_objects if vs.video))

        if query_embedding:
            ids_for_qdrant_filter = candidate_video_papri_ids if candidate_video_papri_ids else None
            semantic_hits = self._search_qdrant_db(query_embedding, top_k=50, video_papri_ids_filter_list=ids_for_qdrant_filter)
            for hit in semantic_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    semantic_scores_by_video_id[video_id] = max(semantic_scores_by_video_id[video_id], hit['semantic_score'])

        final_ranked_items_with_scores = [] # THIS WILL BE RETURNED
        
        unique_papri_video_ids_to_score = set(candidate_video_papri_ids)
        unique_papri_video_ids_to_score.update(semantic_scores_by_video_id.keys())

        if not unique_papri_video_ids_to_score:
            print("RARAgent: No candidate videos to rank.")
            return [] # Return empty list of dicts

        videos_to_score = Video.objects.filter(id__in=list(unique_papri_video_ids_to_score)).prefetch_related(
            'sources__transcripts__keywords' # Prefetch for keyword gathering
        )

        for papri_video in videos_to_score:
            # ... (keyword_score calculation as before) ...
            keyword_score = 0
            video_collected_keywords = set()
            for vs_obj in papri_video.sources.all():
                analysis_for_this_source = all_analysis_data.get(vs_obj.id)
                if analysis_for_this_source and analysis_for_this_source.get('transcript_analysis', {}).get('status') == 'processed':
                    video_collected_keywords.update(k.lower() for k in analysis_for_this_source['transcript_analysis'].get('keywords', []))
                # Fallback to DB if not in all_analysis_data (though ideally it should be)
                elif not analysis_for_this_source:
                    for transcript in vs_obj.transcripts.filter(processing_status='processed'):
                         video_collected_keywords.update(kw.keyword_text.lower() for kw in transcript.keywords.all())

            if papri_video.title: video_collected_keywords.update(word.lower() for word in papri_video.title.split())
            if papri_video.description: video_collected_keywords.update(word.lower() for word in papri_video.description.split()[:50])

            if query_keywords:
                matching_keywords = query_keywords.intersection(video_collected_keywords)
                keyword_score = len(matching_keywords)
                if processed_query_data.get('processed_query') and papri_video.title and \
                   processed_query_data['processed_query'].lower() in papri_video.title.lower():
                    keyword_score += 5

            semantic_score_for_video = semantic_scores_by_video_id.get(papri_video.id, 0.0)
            
            KW_WEIGHT = 0.4; SEM_WEIGHT = 0.6 
            combined_score = (keyword_score * KW_WEIGHT) + (float(semantic_score_for_video) * 10 * SEM_WEIGHT)
            pub_date = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)
            
            final_ranked_items_with_scores.append({ # Store dict with score
                'video_id': papri_video.id, 
                'combined_score': combined_score,
                'keyword_score': keyword_score, 
                'semantic_score': float(semantic_score_for_video),
                'publication_date': pub_date # Keep for sorting
            })

        # Sort by combined_score, then publication_date
        final_ranked_items_with_scores.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        
        # Fallback sort if no scores (e.g., no query terms, no semantic hits)
        if not any(item['combined_score'] > 0 for item in final_ranked_items_with_scores) and not query_keywords and not query_embedding:
            print("RARAgent: No scores for ranking, attempting fallback date sort.")
            # We already have Video objects in videos_to_score
            sorted_videos_by_date = sorted(
                [v for v in videos_to_score if v.publication_date is not None],
                key=lambda v: v.publication_date, reverse=True
            )
            # Rebuild final_ranked_items_with_scores based on this date sort
            temp_ranked_items = [{'video_id': v.id, 'combined_score': 0, 'publication_date': v.publication_date} for v in sorted_videos_by_date]
            temp_ranked_items.extend(
                {'video_id': v.id, 'combined_score': 0, 'publication_date': timezone.datetime.min.replace(tzinfo=timezone.utc)}
                for v in videos_to_score if v.publication_date is None and v.id not in {item['video_id'] for item in temp_ranked_items}
            )
            final_ranked_items_with_scores = temp_ranked_items


        print(f"RARAgent: Ranking complete. Returning {len(final_ranked_items_with_scores)} items with scores.")
        for item in final_ranked_items_with_scores[:5]:
             print(f"  Ranked Item: VideoID={item['video_id']}, CombinedScore={item['combined_score']:.2f} (K:{item['keyword_score']}, S:{item['semantic_score']:.2f})")
        
        return final_ranked_items_with_scores # Return list of dicts

    def perform_deduplication(self, video_source_objects):
        """
        Placeholder for more advanced deduplication.
        Currently, deduplication is handled at the VideoSource level by original_url
        and the linking to canonical Video objects in the orchestrator.
        This method could implement content-based deduplication later.
        """
        print(f"RARAgent: Deduplication (placeholder) called for {len(video_source_objects)} sources.")
        # For now, assume orchestrator's _persist_basic_video_info handles basic Video linking.
        # Return unique Video objects based on the linking in persisted_video_source_objects.
        unique_videos = {} # papri_video_id -> video_source_object (first one encountered)
        for vs_obj in video_source_objects:
            if vs_obj.video and vs_obj.video.id not in unique_videos:
                unique_videos[vs_obj.video.id] = vs_obj
        
        return list(unique_videos.values())
