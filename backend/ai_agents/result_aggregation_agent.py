# backend/ai_agents/result_aggregation_agent.py
from collections import Counter, defaultdict # Add defaultdict
from django.conf import settings # For Vector DB settings
from api.models import VideoSource, Video, Transcript # For type hinting and accessing related models
from api.models import VideoFrameFeature # Ensure this is imported
from pymilvus import Collection, connections 


class ResultAggregationAgent:
    def __init__(self):
        # ... (Qdrant client setup as before) ...
        self.qdrant_transcript_collection_name = settings.QDRANT_COLLECTION_TRANSCRIPTS
        self.qdrant_visual_collection_name = settings.QDRANT_COLLECTION_VISUAL
        self.qdrant_client = None
        try:
            self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=10)
            self.qdrant_client.health_check(); print(f"RARAgent: Connected to Qdrant.")
        except Exception as e: print(f"RARAgent: CRITICAL - Qdrant connection failed: {e}")
        print("ResultAggregationAgent initialized.")


    def _search_qdrant_transcript_db(self, query_embedding, top_k=50, video_papri_ids_filter_list=None):
        # ... (Implementation from Step 23 - Qdrant search for transcript embeddings) ...
        # Returns list of {'transcript_id': id, 'video_papri_id': id, 'semantic_score': score}
        if not self.qdrant_client or not query_embedding: return []
        try:
            filter_ = None
            if video_papri_ids_filter_list: filter_ = qdrant_models.Filter(must=[qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))])
            results = self.qdrant_client.search(collection_name=self.qdrant_transcript_collection_name, query_vector=query_embedding, query_filter=filter_, limit=top_k, with_payload=True)
            return [{'transcript_id': h.id, 'video_papri_id': h.payload.get('video_papri_id') if h.payload else None, 'semantic_score': h.score} for h in results if h.payload]
        except Exception as e: print(f"RARAgent: Error Qdrant Transcript Search: {e}"); return []


    def _search_qdrant_visual_db(self, query_cnn_embedding, top_k=30, video_papri_ids_filter_list=None): # Added filter list
        # ... (Implementation from Step 23 - Qdrant search for visual CNN embeddings) ...
        # Returns list of {'video_frame_feature_id': id, 'video_papri_id': id, 'timestamp_ms': ms, 'visual_cnn_score': score, 'phash_from_payload': hash}
        if not self.qdrant_client or not query_cnn_embedding: return []
        try:
            filter_ = None
            if video_papri_ids_filter_list: filter_ = qdrant_models.Filter(must=[qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))])
            results = self.qdrant_client.search(collection_name=self.qdrant_visual_collection_name, query_vector=query_cnn_embedding, query_filter=filter_, limit=top_k, with_payload=True)
            return [{'video_frame_feature_id': h.id, 'video_papri_id': h.payload.get('video_papri_id'), 'timestamp_ms': h.payload.get('timestamp_ms'), 'visual_cnn_score': h.score, 'phash_from_payload': h.payload.get('phash')} for h in results if h.payload]
        except Exception as e: print(f"RARAgent: Error Qdrant Visual Search: {e}"); return []


    def _search_perceptual_hashes_in_db(self, query_hashes, hash_threshold=5, video_papri_ids_filter_list=None):
        # ... (Implementation from Step 23 - Django DB search for pHash) ...
        # Returns list of {'video_frame_feature_id': id, 'video_papri_id': id, 'timestamp_ms': ms, 'visual_phash_score': score, 'phash_from_db': hash}
        # Consider adding hamming distance calculation here.
        if not query_hashes or not query_hashes.get('phash'): return []
        import imagehash # Ensure imported
        phash_query_str = query_hashes.get('phash')
        query_phash_obj = imagehash.hex_to_hash(phash_query_str)
        
        candidate_frames = VideoFrameFeature.objects.select_related('video_source__video')
        if video_papri_ids_filter_list:
            candidate_frames = candidate_frames.filter(video_source__video__id__in=video_papri_ids_filter_list)
        
        db_hits = []
        for frame in candidate_frames.exclude(hash_value__isnull=True).exclude(hash_value__exact=''):
            try:
                db_phash_obj = imagehash.hex_to_hash(frame.hash_value)
                distance = query_phash_obj - db_phash_obj
                if distance <= hash_threshold:
                    if frame.video_source and frame.video_source.video:
                        db_hits.append({
                            'video_frame_feature_id': frame.id,
                            'video_papri_id': frame.video_source.video.id,
                            'timestamp_ms': frame.timestamp_in_video_ms,
                            'visual_phash_score': 1.0 - (distance / (hash_threshold + 1.0)), # Normalized score
                            'phash_from_db': frame.hash_value,
                            'phash_distance': distance
                        })
            except Exception as e:
                print(f"RARAgent: Error comparing pHash for VFF ID {frame.id}: {e}")
        print(f"RARAgent: pHash search found {len(db_hits)} hits within threshold {hash_threshold}.")
        return db_hits


    def aggregate_and_rank_results(self, persisted_video_source_objects, processed_query_data, all_analysis_data):
        query_intent = processed_query_data.get('intent', 'general_video_search')
        query_keywords = set(k.lower() for k in processed_query_data.get('keywords', []))
        query_text_embedding = processed_query_data.get('query_embedding')
        query_visual_features = processed_query_data.get('visual_features')

        # Scores for each canonical Papri Video ID
        # Adding match_type_flags to track how a video was matched
        final_scores_by_video_id = defaultdict(lambda: {
            'keyword_score': 0.0, 'semantic_text_score': 0.0,
            'visual_cnn_score': 0.0, 'visual_phash_score': 0.0,
            'combined_score': 0.0, 
            'publication_date': timezone.datetime.min.replace(tzinfo=timezone.utc),
            'match_type_flags': set() # e.g., {'text_kw', 'text_sem', 'vis_cnn', 'vis_phash'}
        })

        # Candidate Papri Video IDs from sources fetched in *this* session by SOIAgent
        # These are primary candidates for keyword scoring using fresh analysis data.
        current_session_video_ids = set(vs.video.id for vs in persisted_video_source_objects if vs.video)

        # --- 1. Text Semantic Search (Qdrant Transcripts) ---
        if query_text_embedding:
            text_semantic_hits = self._search_qdrant_transcript_db(query_text_embedding, top_k=50) # Broader search
            for hit in text_semantic_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['semantic_text_score'] = max(final_scores_by_video_id[video_id]['semantic_text_score'], hit['semantic_score'])
                    final_scores_by_video_id[video_id]['match_type_flags'].add('text_sem')

        # --- 2. Visual Semantic Search (Qdrant Visual CNN Embeddings) ---
        if query_visual_features and query_visual_features.get('cnn_embedding'):
            query_cnn_embedding = query_visual_features['cnn_embedding']
            visual_cnn_hits = self._search_qdrant_visual_db(query_cnn_embedding, top_k=30)
            for hit in visual_cnn_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['visual_cnn_score'] = max(final_scores_by_video_id[video_id]['visual_cnn_score'], hit['visual_cnn_score'])
                    final_scores_by_video_id[video_id]['match_type_flags'].add('vis_cnn')

        # --- 3. Visual Perceptual Hash Search (Django DB) ---
        if query_visual_features and query_visual_features.get('perceptual_hashes'):
            query_hashes = query_visual_features['perceptual_hashes']
            # More targeted pHash search: Filter by video_ids already found by CNN if available
            phash_candidate_ids = list(final_scores_by_video_id.keys()) if final_scores_by_video_id else None
            phash_hits = self._search_perceptual_hashes_in_db(query_hashes, video_papri_ids_filter_list=phash_candidate_ids)
            for hit in phash_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['visual_phash_score'] = max(final_scores_by_video_id[video_id]['visual_phash_score'], hit['visual_phash_score'])
                    final_scores_by_video_id[video_id]['match_type_flags'].add('vis_phash')
        
        # --- 4. Keyword Scoring (for videos that had any hit OR were fetched by SOIAgent) ---
        all_potential_video_ids = set(current_session_video_ids)
        all_potential_video_ids.update(final_scores_by_video_id.keys())

        if not all_potential_video_ids: return [] # No videos to rank

        videos_to_process_qset = Video.objects.filter(id__in=list(all_potential_video_ids)).prefetch_related('sources__transcripts__keywords')
        
        for papri_video in videos_to_process_qset:
            video_id = papri_video.id
            final_scores_by_video_id[video_id]['publication_date'] = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)

            if query_keywords: # Only do keyword scoring if text query was part of input
                keyword_score = 0
                # ... (keyword collection logic as before - from all_analysis_data for current session, or DB for others) ...
                # This part needs to efficiently get keywords for papri_video.id
                # For simplicity, we assume all_analysis_data is comprehensive for current_session_video_ids
                # and for others, we'd rely on pre-indexed keywords if this method was broader.
                # For now, focus on keywords from current_session_video_ids via all_analysis_data.
                video_collected_keywords = set()
                for vs_obj in papri_video.sources.all(): # This uses prefetched sources for this papri_video
                    analysis_for_this_source = all_analysis_data.get(vs_obj.id)
                    if analysis_for_this_source and analysis_for_this_source.get('transcript_analysis', {}).get('status') == 'processed':
                        video_collected_keywords.update(k.lower() for k in analysis_for_this_source['transcript_analysis'].get('keywords', []))
                if papri_video.title: video_collected_keywords.update(word.lower() for word in papri_video.title.split())
                if papri_video.description: video_collected_keywords.update(word.lower() for word in papri_video.description.split()[:70])
                
                matching_keywords = query_keywords.intersection(video_collected_keywords)
                keyword_score = len(matching_keywords)
                if processed_query_data.get('processed_query', '').lower() in (papri_video.title.lower() if papri_video.title else ''):
                    keyword_score += 5 
                
                final_scores_by_video_id[video_id]['keyword_score'] = keyword_score
                if keyword_score > 0: final_scores_by_video_id[video_id]['match_type_flags'].add('text_kw')


        # --- 5. Combine all scores and Rank ---
        final_ranked_list = []
        for video_id, scores in final_scores_by_video_id.items():
            # Define weights - THESE NEED EXTENSIVE TUNING!
            W_KW = 0.30       # Keyword score
            W_SEM_TEXT = 0.30 # Text semantic score
            W_VIS_CNN = 0.25  # Visual CNN embedding score
            W_VIS_PHASH = 0.15# Visual Perceptual Hash score (higher implies exact match)
            
            # If it's a pure image search, visual weights should be higher.
            # If it's a pure text search, text weights should be higher.
            # Hybrid needs careful balancing.
            
            # Normalize keyword score (e.g., 0-1 range, assuming max ~20 keywords match)
            norm_kw_score = min(scores['keyword_score'] / 20.0, 1.0) if scores['keyword_score'] > 0 else 0.0
            
            combined_score = 0
            if 'text_kw' in scores['match_type_flags'] or 'text_sem' in scores['match_type_flags']: # If any text match
                combined_score += norm_kw_score * W_KW
                combined_score += scores['semantic_text_score'] * W_SEM_TEXT
            
            if 'vis_cnn' in scores['match_type_flags'] or 'vis_phash' in scores['match_type_flags']: # If any visual match
                combined_score += scores['visual_cnn_score'] * W_VIS_CNN
                combined_score += scores['visual_phash_score'] * W_VIS_PHASH # pHash score is already 0-1

            # Intent-based boosting (example)
            if query_intent == 'visual_similarity_search' and ('vis_cnn' in scores['match_type_flags'] or 'vis_phash' in scores['match_type_flags']):
                combined_score *= 1.2 # Boost visual matches for pure visual query
            elif query_intent == 'general_video_search' and ('text_kw' in scores['match_type_flags'] or 'text_sem' in scores['match_type_flags']):
                combined_score *= 1.1 # Slight boost for text matches in text query
            elif query_intent == 'hybrid_text_visual_search':
                if ('text_kw' in scores['match_type_flags'] or 'text_sem' in scores['match_type_flags']) and \
                   ('vis_cnn' in scores['match_type_flags'] or 'vis_phash' in scores['match_type_flags']):
                    combined_score *= 1.3 # Boost if both modalities match for hybrid query


            final_ranked_list.append({
                'video_id': video_id, 'combined_score': combined_score,
                'kw_score': scores['keyword_score'], 'sem_text_score': scores['semantic_text_score'],
                'vis_cnn_score': scores['visual_cnn_score'], 'vis_phash_score': scores['visual_phash_score'],
                'publication_date': scores['publication_date'],
                'match_types': list(scores['match_type_flags']) # For frontend display
            })

        final_ranked_list.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        
        # Fallback if all scores are zero or very low (e.g. pure text query with no keyword/semantic hits)
        if not final_ranked_list or all(item['combined_score'] < 0.001 for item in final_ranked_list):
            if not query_keywords and not query_text_embedding and not query_visual_features: # Absolutely no query input
                 return [] # Should not happen if QAgent validates
            
            print("RARAgent: All combined scores are zero/low. Attempting fallback sort (e.g. by date of persisted videos).")
            # This fallback should use videos_to_process_qset or similar if available
            # to avoid re-querying DB unnecessarily.
            # For now, simplified:
            fallback_sorted_videos = sorted(
                [v for v in videos_to_process_qset if v.publication_date is not None],
                key=lambda v: v.publication_date, reverse=True
            )
            final_ranked_list = [{'video_id': v.id, 'combined_score': 0, 'publication_date':v.publication_date, 'match_types':['fallback_date']} for v in fallback_sorted_videos]
            final_ranked_list.extend(
                 {'video_id': v.id, 'combined_score': 0, 'publication_date':timezone.datetime.min.replace(tzinfo=timezone.utc), 'match_types':['fallback_date']}
                for v in videos_to_process_qset if v.publication_date is None and v.id not in {item['video_id'] for item in final_ranked_list}
            )


        print(f"RARAgent: Multi-modal ranking complete. Returning {len(final_ranked_list)} items.")
        for item in final_ranked_list[:5]:
             print(f"  Ranked: VID={item['video_id']}, Score={item['combined_score']:.3f} (KW:{item['kw_score']}, ST:{item['sem_text_score']:.2f}, VC:{item['vis_cnn_score']:.2f}, VP:{item['vis_phash_score']:.2f}) Types: {item['match_types']}")
        
        return final_ranked_list # Return list of dicts with scores and match_types
