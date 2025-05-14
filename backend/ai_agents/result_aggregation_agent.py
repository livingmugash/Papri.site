# backend/ai_agents/result_aggregation_agent.py
from collections import Counter, defaultdict # Add defaultdict
from django.conf import settings # For Vector DB settings
from api.models import VideoSource, Video, Transcript # For type hinting and accessing related models

# Example Milvus client - adapt if using another Vector DB
from pymilvus import Collection, connections 

class ResultAggregationAgent:
    def __init__(self):
        # ... (Qdrant client for transcripts as before) ...
        self.qdrant_transcript_collection_name = settings.QDRANT_COLLECTION_TRANSCRIPTS
        self.qdrant_visual_collection_name = settings.QDRANT_COLLECTION_VISUAL # For visual
        self.qdrant_client = None
        try:
            self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=10)
            self.qdrant_client.health_check()
            print(f"RARAgent: Connected to Qdrant at {settings.QDRANT_URL}")
        except Exception as e:
            print(f"RARAgent: CRITICAL - Failed to connect to Qdrant: {e}")

        print("ResultAggregationAgent initialized.")

def _search_qdrant_visual_db(self, query_cnn_embedding, top_k=20):
        """Searches Qdrant visual collection for similar CNN embeddings."""
        if not self.qdrant_client or not query_cnn_embedding:
            print("RARAgent: Qdrant client (visual) or query CNN embedding not available.")
            return []
        try:
            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_visual_collection_name,
                query_vector=query_cnn_embedding,
                limit=top_k,
                with_payload=True # To get video_papri_id, timestamp_ms, phash etc.
            )
            visual_hits = []
            for hit in search_results: # hit is ScoredPoint
                if hit.payload:
                    visual_hits.append({
                        'video_frame_feature_id': hit.id, # Django VideoFrameFeature.id
                        'video_papri_id': hit.payload.get('video_papri_id'),
                        'timestamp_ms': hit.payload.get('timestamp_ms'),
                        'visual_cnn_score': hit.score, # Cosine similarity
                        'phash_from_payload': hit.payload.get('phash') 
                    })
            print(f"RARAgent: Qdrant visual CNN search found {len(visual_hits)} hits.")
            return visual_hits
        except Exception as e:
            print(f"RARAgent: Error searching Qdrant visual DB: {e}")
            return []

    def _search_perceptual_hashes_in_db(self, query_hashes, hash_threshold=5):
        """Searches Django DB for matching perceptual hashes."""
        if not query_hashes or not (query_hashes.get('phash') or query_hashes.get('dhash')):
            print("RARAgent: No query perceptual hashes provided.")
            return []
        
        # This will be slow for many VideoFrameFeature entries if not indexed well for similarity.
        # For true perceptual hash similarity search at scale, a specialized index or approach is better.
        # For now, a simple exact match or hamming distance for pHash if imagehash is used to compare.
        
        # Example: Exact match on phash (simplistic)
        # More advanced: iterate and calculate Hamming distance with imagehash.
        phash_query = query_hashes.get('phash')
        # dhash_query = query_hashes.get('dhash') # Can use this too

        db_hits = []
        if phash_query:
            # This finds exact phash matches.
            # For Hamming distance search, you'd fetch candidates and compute distance.
            matched_frames = VideoFrameFeature.objects.filter(hash_value=phash_query).select_related('video_source__video')
            for frame in matched_frames:
                if frame.video_source and frame.video_source.video:
                    db_hits.append({
                        'video_frame_feature_id': frame.id,
                        'video_papri_id': frame.video_source.video.id,
                        'timestamp_ms': frame.timestamp_in_video_ms,
                        'visual_phash_score': 1.0, # Exact match = perfect score
                        'phash_from_db': frame.hash_value
                    })
            print(f"RARAgent: Perceptual hash (exact phash) DB search found {len(db_hits)} hits.")
        return db_hits


    def aggregate_and_rank_results(self, persisted_video_source_objects, processed_query_data, all_analysis_data):
        # ... (query_keywords, query_text_embedding setup as before) ...
        query_keywords = set(k.lower() for k in processed_query_data.get('keywords', []))
        query_text_embedding = processed_query_data.get('query_embedding') # For text part of query
        query_visual_features = processed_query_data.get('visual_features') # For image part of query

        # Scores for each canonical Papri Video ID
        final_scores_by_video_id = defaultdict(lambda: {
            'keyword_score': 0.0,
            'semantic_text_score': 0.0,
            'visual_cnn_score': 0.0,
            'visual_phash_score': 0.0,
            'combined_score': 0.0,
            'publication_date': timezone.datetime.min.replace(tzinfo=timezone.utc),
            'sources_count': 0 # To count how many ranking signals hit this video
        })

        # --- 1. Text Semantic Search (Qdrant Transcripts) ---
        if query_text_embedding:
            # ... (call _search_qdrant_db for transcripts as before, populate semantic_scores_by_video_id)
            # For consistency, let's rename it to reflect text:
            text_semantic_hits = self._search_qdrant_db( # Assuming this is the transcript search method
                query_text_embedding, top_k=50, 
                # video_papri_ids_filter_list=candidate_video_papri_ids # Optional filter
            ) 
            for hit in text_semantic_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['semantic_text_score'] = max(
                        final_scores_by_video_id[video_id]['semantic_text_score'], 
                        hit['semantic_score']
                    )
                    final_scores_by_video_id[video_id]['sources_count'] += 0.5 # Indicate a type of hit


        # --- 2. Visual Semantic Search (Qdrant Visual Embeddings) ---
        if query_visual_features and query_visual_features.get('cnn_embedding'):
            query_cnn_embedding = query_visual_features['cnn_embedding']
            visual_cnn_hits = self._search_qdrant_visual_db(query_cnn_embedding, top_k=30)
            for hit in visual_cnn_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['visual_cnn_score'] = max(
                        final_scores_by_video_id[video_id]['visual_cnn_score'],
                        hit['visual_cnn_score']
                    )
                    final_scores_by_video_id[video_id]['sources_count'] += 1 # Stronger signal


        # --- 3. Visual Perceptual Hash Search (Django DB) ---
        if query_visual_features and query_visual_features.get('perceptual_hashes'):
            query_hashes = query_visual_features['perceptual_hashes']
            phash_hits = self._search_perceptual_hashes_in_db(query_hashes)
            for hit in phash_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['visual_phash_score'] = max(
                        final_scores_by_video_id[video_id]['visual_phash_score'],
                        hit['visual_phash_score'] # Will be 1.0 for exact match
                    )
                    final_scores_by_video_id[video_id]['sources_count'] += 2 # Very strong signal

        # --- 4. Keyword Scoring (for all candidate videos) ---
        # Candidate videos are those fetched by SOIAgent OR identified by any visual/semantic search
        all_candidate_video_ids = set(vs.video.id for vs in persisted_video_source_objects if vs.video)
        all_candidate_video_ids.update(final_scores_by_video_id.keys()) # Add IDs from semantic/visual hits

        if not all_candidate_video_ids:
            print("RARAgent: No candidate videos from any source to rank.")
            return []

        # Fetch video objects if not already available (e.g. if semantic search found new ones)
        # This requires Video objects to exist in DB for these IDs.
        videos_to_score_qset = Video.objects.filter(id__in=list(all_candidate_video_ids)).prefetch_related('sources__transcripts__keywords')
        
        # Populate publication dates and perform keyword scoring
        for papri_video in videos_to_score_qset:
            video_id = papri_video.id
            final_scores_by_video_id[video_id]['publication_date'] = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)

            if query_keywords: # Only do keyword scoring if there are query keywords
                keyword_score = 0
                video_collected_keywords = set()
                # ... (keyword collection logic from transcripts, title, description as before) ...
                for vs_obj in papri_video.sources.all():
                    analysis_for_this_source = all_analysis_data.get(vs_obj.id) # Use data from current run if available
                    if analysis_for_this_source and analysis_for_this_source.get('transcript_analysis', {}).get('status') == 'processed':
                        video_collected_keywords.update(k.lower() for k in analysis_for_this_source['transcript_analysis'].get('keywords', []))
                    else: # Fallback to DB (less efficient if CAAgent output is comprehensive)
                        for transcript in vs_obj.transcripts.filter(processing_status='processed'):
                            video_collected_keywords.update(kw.keyword_text.lower() for kw in transcript.keywords.all())
                if papri_video.title: video_collected_keywords.update(word.lower() for word in papri_video.title.split())
                if papri_video.description: video_collected_keywords.update(word.lower() for word in papri_video.description.split()[:70]) # Slightly more words

                matching_keywords = query_keywords.intersection(video_collected_keywords)
                keyword_score = len(matching_keywords)
                if processed_query_data.get('processed_query') and papri_video.title and \
                   processed_query_data['processed_query'].lower() in papri_video.title.lower():
                    keyword_score += 5 # Title phrase match bonus
                
                final_scores_by_video_id[video_id]['keyword_score'] = keyword_score
                final_scores_by_video_id[video_id]['sources_count'] += 0.25


        # --- 5. Combine all scores and Rank ---
        final_ranked_items_with_scores = []
        for video_id, scores_dict in final_scores_by_video_id.items():
            # Define weights (these need extensive tuning!)
            KW_TEXT_WEIGHT = 0.30
            SEM_TEXT_WEIGHT = 0.35
            VIS_CNN_WEIGHT = 0.25
            VIS_PHASH_WEIGHT = 0.10 # pHash is more for exact match, less for general relevance

            # Normalize or scale scores if necessary.
            # Semantic scores (cosine) are ~0 to 1. pHash is 0 or 1 here. CNN score also ~0 to 1. Keyword is count.
            # Simple scaling for keyword score (e.g., max expected keywords ~20-30)
            normalized_kw_score = min(scores_dict['keyword_score'] / 20.0, 1.0) 

            combined_score = (
                normalized_kw_score * KW_TEXT_WEIGHT +
                scores_dict['semantic_text_score'] * SEM_TEXT_WEIGHT +
                scores_dict['visual_cnn_score'] * VIS_CNN_WEIGHT +
                scores_dict['visual_phash_score'] * VIS_PHASH_WEIGHT 
            )
            # Boost if multiple signals hit
            if scores_dict['sources_count'] > 1:
                combined_score *= (1 + (scores_dict['sources_count'] -1) * 0.1) # e.g. 10% boost per extra signal type

            final_ranked_items_with_scores.append({
                'video_id': video_id, 
                'combined_score': combined_score,
                'kw_score': scores_dict['keyword_score'], # Store raw scores for inspection
                'sem_text_score': scores_dict['semantic_text_score'],
                'vis_cnn_score': scores_dict['visual_cnn_score'],
                'vis_phash_score': scores_dict['visual_phash_score'],
                'publication_date': scores_dict['publication_date']
            })

        final_ranked_items_with_scores.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        
        ranked_papri_video_ids = [item['video_id'] for item in final_ranked_items_with_scores]

        print(f"RARAgent: Multi-modal ranking complete. Returning {len(ranked_papri_video_ids)} unique Papri Video IDs.")
        for item in final_ranked_items_with_scores[:5]:
             print(f"  Ranked: VID={item['video_id']}, Score={item['combined_score']:.3f} (K:{item['kw_score']}, ST:{item['sem_text_score']:.2f}, VC:{item['vis_cnn_score']:.2f}, VP:{item['vis_phash_score']:.2f})")
        
        # This method should return the structure expected by the orchestrator,
        # which is currently a list of dicts: [{'video_id': id, 'score': combined_score}, ...]
        # Or simply the list of ranked_papri_video_ids if the orchestrator only needs IDs.
        # Let's adapt to match the Orchestrator's current expectation for its "results_with_scores"
        return final_ranked_items_with_scores # Return list of dicts with scores

    # Renamed method from previous version for clarity
    def _search_qdrant_transcript_db(self, query_embedding, top_k=50, video_papri_ids_filter_list=None):
        if not self.qdrant_client or not query_embedding: return []
        try:
            # ... (Qdrant search logic for transcript collection as defined before) ...
            # This method should be identical to the one previously named _search_qdrant_db
            # Ensure it uses self.qdrant_transcript_collection_name
            query_filter_qdrant = None
            if video_papri_ids_filter_list:
                query_filter_qdrant = qdrant_models.Filter(must=[qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))])
            
            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_transcript_collection_name,
                query_vector=query_embedding, query_filter=query_filter_qdrant, limit=top_k,
                with_payload=True, with_vectors=False
            )
            semantic_hits = []
            for hit in search_results:
                if hit.payload:
                    semantic_hits.append({'transcript_id': hit.id, 'video_papri_id': hit.payload.get('video_papri_id'), 'semantic_score': hit.score})
            print(f"RARAgent: Qdrant Transcript DB search found {len(semantic_hits)} hits.")
            return semantic_hits
        except Exception as e: print(f"RARAgent: Error searching Qdrant Transcript DB: {e}"); return []
        
        return list(unique_videos.values())
