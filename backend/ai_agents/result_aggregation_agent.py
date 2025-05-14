# backend/ai_agents/result_aggregation_agent.py
from collections import Counter, defaultdict # Add defaultdict
from django.conf import settings # For Vector DB settings
from api.models import VideoSource, Video, Transcript # For type hinting and accessing related models
from api.models import VideoFrameFeature # Ensure this is imported
from pymilvus import Collection, connections 


class ResultAggregationAgent:
    def __init__(self):
        # ... (Qdrant client setup for both transcript and visual collections) ...
        self.qdrant_transcript_collection_name = settings.QDRANT_COLLECTION_TRANSCRIPTS
        self.qdrant_visual_collection_name = settings.QDRANT_COLLECTION_VISUAL
        self.qdrant_client = None
        try:
            self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=10)
            self.qdrant_client.health_check()
            print(f"RARAgent: Connected to Qdrant.")
            # Collections are ensured by their respective analyzers (TranscriptAnalyzer, VisualAnalyzer)
        except Exception as e:
            print(f"RARAgent: CRITICAL - Qdrant connection failed: {e}")
        print("ResultAggregationAgent initialized.")

    def _search_qdrant_transcript_db(self, query_embedding, top_k=50, video_papri_ids_filter_list=None):
        # ... (Implementation from Step 25 - remains the same) ...
        if not self.qdrant_client or not query_embedding: return []
        # ... (rest of the logic)
        try:
            filter_ = None
            if video_papri_ids_filter_list: filter_ = qdrant_models.Filter(must=[qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))])
            results = self.qdrant_client.search(collection_name=self.qdrant_transcript_collection_name, query_vector=query_embedding, query_filter=filter_, limit=top_k, with_payload=True)
            return [{'transcript_id': h.id, 'video_papri_id': h.payload.get('video_papri_id') if h.payload else None, 'semantic_score': h.score} for h in results if h.payload]
        except Exception as e: print(f"RARAgent: Error Qdrant Transcript Search: {e}"); return []


    def _search_qdrant_visual_db(self, query_cnn_embedding, top_k=30, video_papri_ids_filter_list=None):
        if not self.qdrant_client or not query_cnn_embedding:
            print("RARAgent: Qdrant client (visual) or query CNN embedding not available for visual search.")
            return []
        try:
            filter_ = None
            if video_papri_ids_filter_list:
                filter_ = qdrant_models.Filter(
                    must=[qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))]
                )
            
            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_visual_collection_name,
                query_vector=query_cnn_embedding,
                query_filter=filter_,
                limit=top_k,
                with_payload=True,
                score_threshold=0.5 # Optional: Minimum similarity score for CNN matches (0.0 to 1.0 for Cosine) - tune this!
            )
            visual_hits = []
            for hit in search_results:
                if hit.payload:
                    visual_hits.append({
                        'video_frame_feature_id': hit.id, 
                        'video_papri_id': hit.payload.get('video_papri_id'),
                        'timestamp_ms': hit.payload.get('timestamp_ms'),
                        'visual_cnn_score': hit.score, 
                        'phash_from_payload': hit.payload.get('phash') 
                    })
            print(f"RARAgent: Qdrant visual CNN search found {len(visual_hits)} hits (top_k={top_k}).")
            return visual_hits
        except Exception as e:
            print(f"RARAgent: Error searching Qdrant visual DB: {e}")
            return []

    def _search_perceptual_hashes_in_db(self, query_hashes, hash_threshold=8, video_papri_ids_filter_list=None): # Increased threshold slightly
        if not query_hashes or not query_hashes.get('phash'):
            print("RARAgent: No query pHash provided for perceptual hash search.")
            return []
        
        phash_query_str = query_hashes.get('phash')
        try:
            query_phash_obj = imagehash.hex_to_hash(phash_query_str)
        except ValueError:
            print(f"RARAgent: Invalid query pHash string format: {phash_query_str}")
            return []

        candidate_frames_qs = VideoFrameFeature.objects.select_related('video_source__video').exclude(hash_value__isnull=True).exclude(hash_value__exact='')
        if video_papri_ids_filter_list:
            candidate_frames_qs = candidate_frames_qs.filter(video_source__video__id__in=video_papri_ids_filter_list)
        
        # Limiting the number of frames to compare against for performance if not filtered by video_ids
        if not video_papri_ids_filter_list:
            # This is not ideal for large DBs, but a placeholder for a more optimized approach
            # Perhaps filter by recently indexed or some other heuristic if candidate_frames_qs is too large
            candidate_frames_qs = candidate_frames_qs.order_by('-updated_at')[:2000] # Compare against last 2000 pHashes
            print(f"RARAgent: pHash search comparing against up to 2000 recent frame hashes due to no video ID filter.")


        db_hits = []
        for frame in candidate_frames_qs:
            try:
                db_phash_obj = imagehash.hex_to_hash(frame.hash_value)
                distance = query_phash_obj - db_phash_obj # Hamming distance
                if distance <= hash_threshold:
                    if frame.video_source and frame.video_source.video:
                        # Score: 1.0 for exact match (dist 0), decreasing to near 0 at threshold
                        phash_similarity_score = max(0, 1.0 - (distance / (hash_threshold + 1.0)))
                        db_hits.append({
                            'video_frame_feature_id': frame.id,
                            'video_papri_id': frame.video_source.video.id,
                            'timestamp_ms': frame.timestamp_in_video_ms,
                            'visual_phash_score': phash_similarity_score,
                            'phash_from_db': frame.hash_value,
                            'phash_distance': distance
                        })
            except ValueError: # Invalid hash string in DB
                print(f"RARAgent: Invalid pHash string in DB for VFF ID {frame.id}: '{frame.hash_value}'")
            except Exception as e:
                print(f"RARAgent: Error comparing pHash for VFF ID {frame.id}: {e}")
        
        # Sort by distance (ascending) then take top N if many matches, or by score (descending)
        db_hits.sort(key=lambda x: x['phash_distance'])
        print(f"RARAgent: pHash search found {len(db_hits)} hits within threshold {hash_threshold}.")
        return db_hits[:30] # Return top N pHash matches


    def aggregate_and_rank_results(self, persisted_video_source_objects, processed_query_data, all_analysis_data):
        query_intent = processed_query_data.get('intent', 'general_video_search')
        query_keywords = set(k.lower() for k in processed_query_data.get('keywords', []))
        query_text_embedding = processed_query_data.get('query_embedding')
        query_visual_features = processed_query_data.get('visual_features') # dict with 'cnn_embedding', 'perceptual_hashes'

        final_scores_by_video_id = defaultdict(lambda: {
            'keyword_score': 0.0, 'semantic_text_score': 0.0,
            'visual_cnn_score': 0.0, 'visual_phash_score': 0.0,
            'combined_score': 0.0, 
            'publication_date': timezone.datetime.min.replace(tzinfo=timezone.utc), # Default for sorting
            'match_type_flags': set(),
            'best_match_timestamp_ms': None # For visual matches, store the timestamp of the best matching frame
        })

        current_session_video_ids = set(vs.video.id for vs in persisted_video_source_objects if vs.video)
        all_candidate_video_ids_for_filtering = list(current_session_video_ids) if current_session_video_ids else None


        # --- 1. Text Semantic Search ---
        if query_text_embedding:
            text_semantic_hits = self._search_qdrant_transcript_db(
                query_text_embedding, top_k=50, 
                video_papri_ids_filter_list=all_candidate_video_ids_for_filtering # Optionally filter by current session videos
            )
            for hit in text_semantic_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    final_scores_by_video_id[video_id]['semantic_text_score'] = max(final_scores_by_video_id[video_id]['semantic_text_score'], hit['semantic_score'])
                    final_scores_by_video_id[video_id]['match_type_flags'].add('text_sem')

        # --- 2. Visual CNN Semantic Search ---
        if query_visual_features and query_visual_features.get('cnn_embedding'):
            query_cnn_embedding = query_visual_features['cnn_embedding']
            visual_cnn_hits = self._search_qdrant_visual_db(query_cnn_embedding, top_k=30) # Broader search initially
            for hit in visual_cnn_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    current_max_score = final_scores_by_video_id[video_id]['visual_cnn_score']
                    if hit['visual_cnn_score'] > current_max_score:
                        final_scores_by_video_id[video_id]['visual_cnn_score'] = hit['visual_cnn_score']
                        final_scores_by_video_id[video_id]['best_match_timestamp_ms'] = hit.get('timestamp_ms')
                    final_scores_by_video_id[video_id]['match_type_flags'].add('vis_cnn')
                    all_candidate_video_ids_for_filtering = list(set(all_candidate_video_ids_for_filtering or []) | {video_id}) # Add to candidates

        # --- 3. Visual Perceptual Hash Search (potentially filtered by CNN hits) ---
        if query_visual_features and query_visual_features.get('perceptual_hashes'):
            query_hashes = query_visual_features['perceptual_hashes']
            # Filter pHash search by video_ids that got a CNN hit, if any, or current session videos
            phash_filter_ids = list(final_scores_by_video_id.keys()) if any(s['visual_cnn_score'] > 0 for s in final_scores_by_video_id.values()) else all_candidate_video_ids_for_filtering
            
            phash_hits = self._search_perceptual_hashes_in_db(query_hashes, video_papri_ids_filter_list=phash_filter_ids)
            for hit in phash_hits:
                video_id = hit.get('video_papri_id')
                if video_id is not None:
                    current_max_score = final_scores_by_video_id[video_id]['visual_phash_score']
                    if hit['visual_phash_score'] > current_max_score:
                        final_scores_by_video_id[video_id]['visual_phash_score'] = hit['visual_phash_score']
                        # Update best_match_timestamp if this pHash match is for a better frame or a new video
                        if final_scores_by_video_id[video_id]['best_match_timestamp_ms'] is None or hit['visual_phash_score'] > final_scores_by_video_id[video_id]['visual_cnn_score']: # crude check
                           final_scores_by_video_id[video_id]['best_match_timestamp_ms'] = hit.get('timestamp_ms')
                    final_scores_by_video_id[video_id]['match_type_flags'].add('vis_phash')
        
        # --- 4. Keyword Scoring ---
        all_ids_to_score_details_for = set(current_session_video_ids) # Start with session videos
        all_ids_to_score_details_for.update(final_scores_by_video_id.keys()) # Add any from semantic/visual hits

        if not all_ids_to_score_details_for: return []

        videos_to_process_qset = Video.objects.filter(id__in=list(all_ids_to_score_details_for)).prefetch_related('sources__transcripts__keywords')
        
        for papri_video in videos_to_process_qset:
            video_id = papri_video.id
            # Ensure pub_date is set for all considered videos
            final_scores_by_video_id[video_id]['publication_date'] = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)
            
            if query_keywords: # Keyword scoring only if text query part exists
                # ... (keyword collection and scoring logic as before) ...
                keyword_score = 0; video_collected_keywords = set()
                for vs_obj in papri_video.sources.all():
                    analysis = all_analysis_data.get(vs_obj.id, {}).get('transcript_analysis', {})
                    if analysis.get('status') == 'processed': video_collected_keywords.update(k.lower() for k in analysis.get('keywords',[]))
                if papri_video.title: video_collected_keywords.update(w.lower() for w in papri_video.title.split())
                if papri_video.description: video_collected_keywords.update(w.lower() for w in papri_video.description.split()[:70])
                
                matching_keywords = query_keywords.intersection(video_collected_keywords)
                keyword_score = len(matching_keywords)
                processed_q_text = processed_query_data.get('processed_query', '').lower()
                if processed_q_text and papri_video.title and processed_q_text in papri_video.title.lower(): keyword_score += 5
                
                final_scores_by_video_id[video_id]['keyword_score'] = keyword_score
                if keyword_score > 0: final_scores_by_video_id[video_id]['match_type_flags'].add('text_kw')

        # --- 5. Combine all scores and Rank ---
        # ... (Score combination logic as before, using final_scores_by_video_id) ...
        # ... (Sorting and fallback logic as before) ...
        final_ranked_list_output = []
        for video_id, scores in final_scores_by_video_id.items():
            W_KW = 0.25; W_SEM_TEXT = 0.25; W_VIS_CNN = 0.30; W_VIS_PHASH = 0.20 # Adjusted weights
            norm_kw_score = min(scores['keyword_score'] / 20.0, 1.0)
            combined_score = (norm_kw_score * W_KW + scores['semantic_text_score'] * W_SEM_TEXT +
                              scores['visual_cnn_score'] * W_VIS_CNN + scores['visual_phash_score'] * W_VIS_PHASH)
            if query_intent == 'visual_similarity_search' and scores['match_type_flags'] & {'vis_cnn', 'vis_phash'}: combined_score *= 1.3
            elif query_intent == 'general_video_search' and scores['match_type_flags'] & {'text_kw', 'text_sem'}: combined_score *= 1.1
            elif query_intent == 'hybrid_text_visual_search' and (scores['match_type_flags'] & {'text_kw', 'text_sem'}) and \
                                                               (scores['match_type_flags'] & {'vis_cnn', 'vis_phash'}): combined_score *= 1.5
            
            final_ranked_list_output.append({
                'video_id': video_id, 'combined_score': combined_score,
                'kw_score': scores['keyword_score'], 'sem_text_score': scores['semantic_text_score'],
                'vis_cnn_score': scores['visual_cnn_score'], 'vis_phash_score': scores['visual_phash_score'],
                'publication_date': scores['publication_date'], 'match_types': list(scores['match_type_flags']),
                'best_match_timestamp_ms': scores.get('best_match_timestamp_ms') # Add this
            })
        final_ranked_list_output.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        # ... (Fallback logic for empty results if needed) ...

        print(f"RARAgent: Multi-modal ranking. Returning {len(final_ranked_list_output)} items.")
        # ... (logging of top results) ...
        return final_ranked_list_output
