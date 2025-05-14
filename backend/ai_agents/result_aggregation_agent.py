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
        print(f"RARAgent: Aggregating. Query keywords: {processed_query_data.get('keywords')}, Has Embedding: {bool(processed_query_data.get('query_embedding'))}")

        query_keywords = set(k.lower() for k in processed_query_data.get('keywords', []))
        query_embedding = processed_query_data.get('query_embedding')

        # --- 1. Semantic Search (if query_embedding exists) ---
        semantic_scores_by_video_id = defaultdict(float)
        if query_embedding:
            # This search returns transcript_ids and their scores. We need to map them to Papri Video IDs.
            semantic_hits = self._search_vector_db(query_embedding, top_k=50) # Search top K
            
            for hit in semantic_hits:
                transcript_id = hit['transcript_id']
                video_papri_id_from_vec_db = hit.get('video_papri_id') # If stored in vector DB
                semantic_score = hit['semantic_score']

                if video_papri_id_from_vec_db:
                     # Prioritize the video_papri_id retrieved directly from vector DB if available
                    # Aggregate scores if multiple transcripts from same video match (e.g., take max)
                    semantic_scores_by_video_id[video_papri_id_from_vec_db] = max(semantic_scores_by_video_id[video_papri_id_from_vec_db], semantic_score)
                else:
                    # Fallback: Find VideoSource -> Video via transcript_id from Django DB if not in vector DB results
                    try:
                        transcript = Transcript.objects.select_related('video_source__video').get(id=transcript_id)
                        if transcript.video_source and transcript.video_source.video:
                            video_id = transcript.video_source.video.id
                            semantic_scores_by_video_id[video_id] = max(semantic_scores_by_video_id[video_id], semantic_score)
                    except Transcript.DoesNotExist:
                        print(f"RARAgent: Transcript ID {transcript_id} from semantic search not found in DB.")


        # --- 2. Keyword Scoring & Combining with Semantic Scores ---
        final_ranked_items = [] # Will store dicts of {'video_id': X, 'combined_score': Y}

        # Create a map of Papri Video ID to its sources for quick lookup
        video_id_to_sources_map = defaultdict(list)
        for vs_obj in persisted_video_source_objects:
            if vs_obj.video:
                video_id_to_sources_map[vs_obj.video.id].append(vs_obj)
        
        # Get unique Papri Video objects to score
        unique_papri_videos = {vs_obj.video for vs_obj in persisted_video_source_objects if vs_obj.video}

        for papri_video in unique_papri_videos:
            keyword_score = 0
            video_collected_keywords = set()

            # Iterate through all sources of this canonical Papri Video
            for vs_obj in video_id_to_sources_map.get(papri_video.id, []):
                # Get keywords from transcript analysis for this source
                analysis_data_for_source = all_analysis_data.get(vs_obj.id, {})
                transcript_analysis = analysis_data_for_source.get('transcript_analysis', {})
                if transcript_analysis and transcript_analysis.get('status') == 'processed':
                    video_collected_keywords.update(k.lower() for k in transcript_analysis.get('keywords', []))

            # Add keywords from the canonical Video's title and description
            if papri_video.title:
                video_collected_keywords.update(word.lower() for word in papri_video.title.split())
            if papri_video.description:
                video_collected_keywords.update(word.lower() for word in papri_video.description.split()[:50])

            # Calculate keyword score
            if query_keywords:
                matching_keywords = query_keywords.intersection(video_collected_keywords)
                keyword_score = len(matching_keywords)
                if processed_query_data.get('processed_query') and papri_video.title and \
                   processed_query_data['processed_query'].lower() in papri_video.title.lower():
                    keyword_score += 5 # Title phrase match bonus

            # Get semantic score for this papri_video.id
            semantic_score_for_video = semantic_scores_by_video_id.get(papri_video.id, 0.0)

            # --- Combine Scores (Example: weighted sum) ---
            # Weights can be tuned. E.g., semantic score might be 0.0 to 1.0, keyword_score is count.
            # Normalize keyword score or use semantic score as a multiplier/boost.
            # Simple combination for now:
            combined_score = (keyword_score * 0.4) + (semantic_score_for_video * 0.6 * 10) # Scale semantic score contribution
            
            # Add publication date for tie-breaking
            pub_date = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)

            final_ranked_items.append({
                'video_id': papri_video.id,
                'combined_score': combined_score,
                'keyword_score': keyword_score,
                'semantic_score': semantic_score_for_video,
                'publication_date': pub_date
            })

        # Sort by combined_score (desc), then publication_date (desc)
        final_ranked_items.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        
        ranked_papri_video_ids = [item['video_id'] for item in final_ranked_items]
        
        if not ranked_papri_video_ids and not query_keywords and not query_embedding and persisted_video_source_objects:
             # Fallback to just date sort if no query terms at all AND some videos were persisted
            print("RARAgent: No query terms for ranking, falling back to date sort of persisted videos.")
            sorted_sources_by_date = sorted(
                [p_vid for p_vid in unique_papri_videos if p_vid.publication_date is not None],
                key=lambda v: v.publication_date,
                reverse=True
            )
            ranked_papri_video_ids.extend([v.id for v in sorted_sources_by_date])
            # Add videos with no publication date at the end
            ranked_papri_video_ids.extend([v.id for v in unique_papri_videos if v.publication_date is None and v.id not in ranked_papri_video_ids])


        print(f"RARAgent: Ranking complete. Scores combined. Returning {len(ranked_papri_video_ids)} unique Papri Video IDs.")
        if len(final_ranked_items) < 5: # Log details for small result sets
            for item in final_ranked_items[:5]:
                print(f"  Ranked Item: VideoID={item['video_id']}, CombinedScore={item['combined_score']:.2f} (K:{item['keyword_score']}, S:{item['semantic_score']:.2f}), Date:{item['publication_date']}")

        return ranked_papri_video_ids

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
