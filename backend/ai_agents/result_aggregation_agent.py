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

    def _apply_qdrant_payload_filter(self, existing_qdrant_filter, filters_from_api):
        """
        Helper to build or extend Qdrant filter based on API filter parameters.
        """
        qdrant_filter_conditions = []
        if existing_qdrant_filter and hasattr(existing_qdrant_filter, 'must') and existing_qdrant_filter.must:
            qdrant_filter_conditions.extend(existing_qdrant_filter.must)

        # Example: Platform filter (if platform_name is in Qdrant payload for visual/transcript points)
        # This is less likely for transcripts, more for visual if frame associated with platform.
        # For now, platform is better handled post-DB query in SearchResultsView or on VideoSource.

        # Example: Date filter (if publication_date_timestamp_ms is in Qdrant payload)
        date_after_str = filters_from_api.get('date_after') # YYYY-MM-DD
        if date_after_str:
            dt_after = parse_datetime(date_after_str + "T00:00:00Z") # Convert to datetime
            if dt_after:
                qdrant_filter_conditions.append(qdrant_models.FieldCondition(
                    key="publication_timestamp_ms", # Assuming you store this in payload
                    range=qdrant_models.Range(gte=int(dt_after.timestamp() * 1000))
                ))
        # (Similar for date_before)

        if qdrant_filter_conditions:
            return qdrant_models.Filter(must=qdrant_filter_conditions)
        return None


    def _search_qdrant_transcript_db(self, query_embedding, top_k=50, video_papri_ids_filter_list=None, api_filters=None):
        if not self.qdrant_client or not query_embedding: return []
        try:
            # Initial filter (e.g., by video_papri_ids if provided)
            current_qdrant_filter = None
            if video_papri_ids_filter_list:
                current_qdrant_filter = qdrant_models.Filter(must=[
                    qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))
                ])
            
            # Augment with filters from API if applicable to Qdrant payload
            if api_filters:
                current_qdrant_filter = self._apply_qdrant_payload_filter(current_qdrant_filter, api_filters)

            results = self.qdrant_client.search(
                collection_name=self.qdrant_transcript_collection_name, 
                query_vector=query_embedding, 
                query_filter=current_qdrant_filter, # Apply combined filter
                limit=top_k, 
                with_payload=True
            )
            # ... (process results as before) ...
            return [{'transcript_id': h.id, 'video_papri_id': h.payload.get('video_papri_id'), 'semantic_score': h.score} for h in results if h.payload]
        except Exception as e: logger.error(f"RARAgent: Error Qdrant Transcript Search with filters: {e}", exc_info=True); return []


    def _search_qdrant_visual_db(self, query_cnn_embedding, top_k=30, video_papri_ids_filter_list=None, api_filters=None):
        if not self.qdrant_client or not query_cnn_embedding: return []
        try:
            current_qdrant_filter = None
            if video_papri_ids_filter_list:
                current_qdrant_filter = qdrant_models.Filter(must=[
                    qdrant_models.FieldCondition(key="video_papri_id", match=qdrant_models.MatchAny(any=video_papri_ids_filter_list))
                ])
            if api_filters:
                current_qdrant_filter = self._apply_qdrant_payload_filter(current_qdrant_filter, api_filters)

            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_visual_collection_name,
                query_vector=query_cnn_embedding,
                query_filter=current_qdrant_filter, # Apply combined filter
                limit=top_k,
                with_payload=True,
                score_threshold=0.5 
            )
            # ... (process results as before) ...
            return [{'video_frame_feature_id': h.id, 'video_papri_id': h.payload.get('video_papri_id'), 'timestamp_ms': h.payload.get('timestamp_ms'), 'visual_cnn_score': h.score, 'phash_from_payload': h.payload.get('phash')} for h in search_results if h.payload]
        except Exception as e: logger.error(f"RARAgent: Error Qdrant Visual Search with filters: {e}", exc_info=True); return []

    # _search_perceptual_hashes_in_db remains mostly a Django query. 
    # API filters like date/duration would be applied by SearchResultsView on the Video objects.
    # Platform filter for pHash could be done by filtering candidate_frames_qs by video_source__platform_name.

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


    def _generate_text_snippet(self, full_text, query_keywords_set, matched_semantic_text_segment=None, max_length=200):
        """
        Generates a relevant text snippet around query keywords or a semantic segment.
        """
        if not full_text:
            return None

        best_snippet = None
        highest_keyword_overlap = -1

        # Option 1: If a specific semantic text segment was highly relevant (e.g., from chunked embeddings later)
        if matched_semantic_text_segment:
            # For now, this is a placeholder. If we implement transcript chunking and semantic search returns
            # the best chunk, that chunk itself is the best snippet.
            # For V1 with full transcript embeddings, this part is less direct.
            pass 

        # Option 2: Find snippet around keyword occurrences
        if query_keywords_set:
            # Simple approach: find the first occurrence of any query keyword
            # A better approach: find a window with the most query keywords
            
            # Let's find a window with high density of keywords
            words = re.split(r'(\s+)', full_text) # Split by space, keeping spaces to reconstruct
            text_words_lower = [w.lower() for w in words]
            
            # Consider a window of N words
            window_size_words = 30 # Approx number of words for a snippet
            best_window_start = -1

            for i in range(len(text_words_lower) - window_size_words + 1):
                current_window_text_lower = text_words_lower[i : i + window_size_words]
                # Count unique query keywords in this window
                overlap_count = len(query_keywords_set.intersection(set(current_window_text_lower)))
                
                if overlap_count > highest_keyword_overlap:
                    highest_keyword_overlap = overlap_count
                    best_window_start = i
                elif overlap_count == highest_keyword_overlap and overlap_count > 0:
                    # Prefer windows earlier in the text if scores are equal
                    pass 

            if best_window_start != -1 and highest_keyword_overlap > 0:
                snippet_words = words[best_window_start : best_window_start + window_size_words]
                best_snippet = "".join(snippet_words).strip()
                
                # Trim to max_length, trying to keep context
                if len(best_snippet) > max_length:
                    # Find the first keyword in the snippet to center around if possible
                    first_kw_pos = -1
                    for kw in query_keywords_set:
                        try:
                            pos = best_snippet.lower().index(kw)
                            if first_kw_pos == -1 or pos < first_kw_pos:
                                first_kw_pos = pos
                        except ValueError:
                            continue
                    
                    if first_kw_pos != -1:
                        start = max(0, first_kw_pos - (max_length // 3))
                        best_snippet = best_snippet[start : start + max_length]
                    else: # No keyword found in the best window (shouldn't happen if highest_keyword_overlap > 0)
                        best_snippet = best_snippet[:max_length]
                
                # Add ellipsis if snippet was cut or doesn't start/end at sentence boundary (simplified)
                if best_window_start > 0: best_snippet = "... " + best_snippet
                if (best_window_start + window_size_words) < len(words): best_snippet += " ..."
                best_snippet = best_snippet.strip()

        # Fallback if no keywords matched but there was semantic score (or if it's just a description)
        if not best_snippet and (final_scores_by_video_id[video_id]['semantic_text_score'] > 0.1 or not query_keywords_set): # check semantic score condition
            best_snippet = full_text[:max_length]
            if len(full_text) > max_length:
                best_snippet += "..."
        
        return best_snippet


    def aggregate_and_rank_results(self, persisted_video_source_objects, processed_query_data, all_analysis_data):
        # ... (query_intent, query_keywords, query_text_embedding, query_visual_features extraction) ...
        # ... (final_scores_by_video_id defaultdict setup with 'best_match_timestamp_ms' and 'text_snippet')
        final_scores_by_video_id = defaultdict(lambda: {
            'keyword_score': 0.0, 'semantic_text_score': 0.0,
            'visual_cnn_score': 0.0, 'visual_phash_score': 0.0,
            'combined_score': 0.0, 
            'publication_date': timezone.datetime.min.replace(tzinfo=timezone.utc),
            'match_type_flags': set(),
            'best_match_timestamp_ms': None,
            'text_snippet': None # NEW field for text snippet
        })
        # ... (current_session_video_ids, Text Semantic Search, Visual CNN Search, Visual pHash Search as before) ...
        # These searches populate scores and match_type_flags in final_scores_by_video_id

        # --- Keyword Scoring & Snippet Generation ---
        all_potential_video_ids = set(vs.video.id for vs in persisted_video_source_objects if vs.video)
        all_potential_video_ids.update(final_scores_by_video_id.keys())

        if not all_potential_video_ids: return []

        videos_to_process_qset = Video.objects.filter(id__in=list(all_potential_video_ids)).prefetch_related(
            'sources__transcripts' # Prefetch transcripts for snippet generation
        )
        
        video_transcript_texts = {} # Cache transcript texts for videos {video_id: "full transcript text"}
        for papri_video in videos_to_process_qset:
            video_id = papri_video.id
            # ... (Populate publication_date as before) ...
            final_scores_by_video_id[video_id]['publication_date'] = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)

            full_transcript_for_snippet = ""
            # Collect keywords and transcript text for this canonical video
            if query_keywords: # Only do keyword scoring and snippeting if text query was part of input
                keyword_score = 0; video_collected_keywords = set()
                
                # Get transcript text for snippet generation
                # Prioritize analysis_data if available (from current session processing)
                # This assumes all_analysis_data has 'transcript_text_content' if transcript was processed.
                # Or fetch from DB if transcript exists.
                
                for vs_obj in papri_video.sources.all(): # Iterate this video's sources
                    analysis_for_this_source = all_analysis_data.get(vs_obj.id, {}).get('transcript_analysis', {})
                    if analysis_for_this_source.get('status') == 'processed':
                        video_collected_keywords.update(k.lower() for k in analysis_for_this_source.get('keywords', []))
                        # Try to get full transcript from analysis data if it stored it, else from DB
                        # For now, let's assume we need to fetch from DB for snippet generation
                    
                    # Fetch latest 'processed' transcript text for snippet generation for this source
                    # (could be from any language, or prioritize English)
                    if not full_transcript_for_snippet: # Only fetch once per canonical video
                        transcript_record = vs_obj.transcripts.filter(processing_status='processed').order_by('-updated_at').first()
                        if transcript_record:
                            full_transcript_for_snippet = transcript_record.transcript_text_content
                            video_transcript_texts[video_id] = full_transcript_for_snippet # Cache it
                            # Also add its keywords if not in all_analysis_data for some reason
                            if not analysis_for_this_source: # If no fresh analysis data for keywords
                                 video_collected_keywords.update(kw.keyword_text.lower() for kw in transcript_record.keywords.all())


                if papri_video.title: video_collected_keywords.update(w.lower() for w in papri_video.title.split())
                if papri_video.description: video_collected_keywords.update(w.lower() for w in papri_video.description.split()[:70])
                
                matching_keywords = query_keywords.intersection(video_collected_keywords)
                keyword_score = len(matching_keywords)
                processed_q_text = processed_query_data.get('processed_query', '').lower()
                if processed_q_text and papri_video.title and processed_q_text in papri_video.title.lower(): keyword_score += 5
                
                final_scores_by_video_id[video_id]['keyword_score'] = keyword_score
                if keyword_score > 0: final_scores_by_video_id[video_id]['match_type_flags'].add('text_kw')

            # Generate snippet if there was a text match (keyword or semantic)
            # Use cached full_transcript_for_snippet or video's description as fallback
            text_for_snippet = video_transcript_texts.get(video_id, papri_video.description or "")
            if ('text_kw' in final_scores_by_video_id[video_id]['match_type_flags'] or \
                final_scores_by_video_id[video_id]['semantic_text_score'] > 0.1) and text_for_snippet: # Condition to generate snippet
                final_scores_by_video_id[video_id]['text_snippet'] = self._generate_text_snippet(
                    text_for_snippet, 
                    query_keywords # Pass the original query keywords for highlighting
                )

        # --- Combine all scores and Rank (as before) ---
        # ... The final_ranked_list_output should now include 'text_snippet' in each item dict ...
        final_ranked_list_output = []
        for video_id, scores in final_scores_by_video_id.items():
            # ... (combined_score calculation as in Step 32) ...
            # Define weights - THESE NEED EXTENSIVE TUNING!
            W_KW = 0.25; W_SEM_TEXT = 0.30; W_VIS_CNN = 0.25; W_VIS_PHASH = 0.20 
            norm_kw_score = min(scores['keyword_score'] / 20.0, 1.0)
            combined_score = (norm_kw_score * W_KW + scores['semantic_text_score'] * W_SEM_TEXT +
                              scores['visual_cnn_score'] * W_VIS_CNN + scores['visual_phash_score'] * W_VIS_PHASH)
            # ... (intent-based boosting) ...
            if query_intent == 'visual_similarity_search' and scores['match_type_flags'] & {'vis_cnn', 'vis_phash'}: combined_score *= 1.3
            elif query_intent == 'general_video_search' and scores['match_type_flags'] & {'text_kw', 'text_sem'}: combined_score *= 1.1
            elif query_intent == 'hybrid_text_visual_search' and (scores['match_type_flags'] & {'text_kw', 'text_sem'}) and \
                                                               (scores['match_type_flags'] & {'vis_cnn', 'vis_phash'}): combined_score *= 1.5
            
            final_ranked_list_output.append({
                'video_id': video_id, 'combined_score': combined_score,
                'kw_score': scores['keyword_score'], 'sem_text_score': scores['semantic_text_score'],
                'vis_cnn_score': scores['visual_cnn_score'], 'vis_phash_score': scores['visual_phash_score'],
                'publication_date': scores['publication_date'], 
                'match_types': list(scores['match_type_flags']),
                'best_match_timestamp_ms': scores.get('best_match_timestamp_ms'),
                'text_snippet': scores.get('text_snippet') # Add snippet to output
            })
        # ... (sorting and fallback as in Step 32) ...
        final_ranked_list_output.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        # ... (Fallback logic for empty results if needed) ...

        logger.info(f"RARAgent: Multi-modal ranking with snippets. Returning {len(final_ranked_list_output)} items.")
        for item in final_ranked_list_output[:3]: # Log top 3 with snippet
             logger.debug(f"  Ranked: VID={item['video_id']}, Score={item['combined_score']:.3f}, Snippet: {item.get('text_snippet', 'N/A')[:50]}...")
        
        return final_ranked_list_output # List of dicts including text_snippet
        # --- Text Semantic Search (Pass API filters) ---
        if query_text_embedding:
            text_semantic_hits = self._search_qdrant_transcript_db(
                query_text_embedding, top_k=50, 
                video_papri_ids_filter_list=current_session_video_ids, # Optionally filter by current session
                api_filters=filters # Pass API filters
            )
            # ... (populate final_scores_by_video_id as before) ...
            for hit in text_semantic_hits:
                video_id = hit.get('video_papri_id');
                if video_id is not None:
                    final_scores_by_video_id[video_id]['semantic_text_score'] = max(final_scores_by_video_id[video_id]['semantic_text_score'], hit['semantic_score'])
                    final_scores_by_video_id[video_id]['match_type_flags'].add('text_sem')


        # --- Visual CNN Semantic Search (Pass API filters) ---
        if query_visual_features and query_visual_features.get('cnn_embedding'):
            query_cnn_embedding = query_visual_features['cnn_embedding']
            visual_cnn_hits = self._search_qdrant_visual_db(
                query_cnn_embedding, top_k=30,
                # video_papri_ids_filter_list=current_session_video_ids, # Could also filter here
                api_filters=filters # Pass API filters
            )
            # ... (populate final_scores_by_video_id as before) ...
            for hit in visual_cnn_hits:
                video_id = hit.get('video_papri_id');
                if video_id is not None:
                    current_max_score = final_scores_by_video_id[video_id]['visual_cnn_score']
                    if hit['visual_cnn_score'] > current_max_score:
                        final_scores_by_video_id[video_id]['visual_cnn_score'] = hit['visual_cnn_score']
                        final_scores_by_video_id[video_id]['best_match_timestamp_ms'] = hit.get('timestamp_ms')
                    final_scores_by_video_id[video_id]['match_type_flags'].add('vis_cnn')


        # ... (Visual Perceptual Hash Search - can also use filters for candidate_frames_qs) ...
        # ... (Keyword Scoring - this happens on Video objects, filters from API are applied by SearchResultsView on Video queryset) ...
        # ... (Combine all scores and Rank - as before) ...
        # ... (Return list of dicts with scores and match_types) ...

        # The rest of the method for keyword scoring, combining scores, and final ranking
        # remains largely the same as in Step 32 / previous. The main change is passing
        # 'filters' to the Qdrant search methods.
        # The actual DB-level filtering for Video model properties (duration, date) is still
        # best handled in SearchResultsView after RARAgent provides the initial ranked list of IDs.
        # Platform filter in SearchResultsView also remains effective there.

        # This structure allows RARAgent's Qdrant searches to be potentially pre-filtered
        # if filters applicable to Qdrant payload are passed.
        # For now, _apply_qdrant_payload_filter is a stub. You'd implement conditions for
        # date ranges, etc., IF you store corresponding data (like publication_timestamp_ms)
        # in your Qdrant point payloads for transcripts and visual frames.

        # For V1, the filters applied in SearchResultsView on the Video objects is the primary filtering mechanism.
        # This change makes RARAgent "aware" of filters for future optimization.

        # (The rest of the ranking and result formatting logic from Step 32)
        # ... (all_potential_video_ids, videos_to_process_qset, keyword scoring loop, score combination, sorting, fallback) ...
        all_ids_to_score_details_for = set(current_session_video_ids); all_ids_to_score_details_for.update(final_scores_by_video_id.keys())
        if not all_ids_to_score_details_for: return []
        videos_to_process_qset = Video.objects.filter(id__in=list(all_ids_to_score_details_for)).prefetch_related('sources__transcripts__keywords')
        for papri_video in videos_to_process_qset: # ... (populate pub_date, keyword score, text snippet) ...
            video_id = papri_video.id; final_scores_by_video_id[video_id]['publication_date'] = papri_video.publication_date if papri_video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)
            # ... (keyword scoring for final_scores_by_video_id[video_id]['keyword_score'] & match_type_flags) ...
            # ... (text snippet generation for final_scores_by_video_id[video_id]['text_snippet']) ...
            if query_keywords:
                kw_score = 0; vid_kws = set()
                for vs_obj in papri_video.sources.all(): # ... get keywords ...
                    analysis = all_analysis_data.get(vs_obj.id, {}).get('transcript_analysis', {})
                    if analysis.get('status') == 'processed': vid_kws.update(k.lower() for k in analysis.get('keywords',[]))
                if papri_video.title: vid_kws.update(w.lower() for w in papri_video.title.split())
                if papri_video.description: vid_kws.update(w.lower() for w in papri_video.description.split()[:70])
                matching_kws = query_keywords.intersection(vid_kws); kw_score = len(matching_kws)
                if processed_query_data.get('processed_query', '').lower() in (papri_video.title.lower() if papri_video.title else ''): kw_score += 5
                final_scores_by_video_id[video_id]['keyword_score'] = kw_score
                if kw_score > 0: final_scores_by_video_id[video_id]['match_type_flags'].add('text_kw')
            
            text_for_snippet = (next((t.transcript_text_content for vs in papri_video.sources.all() for t in vs.transcripts.filter(processing_status='processed').order_by('-updated_at') if t.transcript_text_content), None) or papri_video.description or "")
            if ('text_kw' in final_scores_by_video_id[video_id]['match_type_flags'] or final_scores_by_video_id[video_id]['semantic_text_score'] > 0.05) and text_for_snippet:
                final_scores_by_video_id[video_id]['text_snippet'] = self._generate_text_snippet(text_for_snippet, query_keywords)


        final_ranked_list_output = []; 
        for video_id, scores in final_scores_by_video_id.items(): # ... (combine scores, append to final_ranked_list_output) ...
            # ... (weights and combined_score calc from Step 32)
             W_KW = 0.25; W_SEM_TEXT = 0.30; W_VIS_CNN = 0.25; W_VIS_PHASH = 0.20 
             norm_kw_score = min(scores['keyword_score'] / 20.0, 1.0)
             combined_score = (norm_kw_score * W_KW + scores['semantic_text_score'] * W_SEM_TEXT +
                               scores['visual_cnn_score'] * W_VIS_CNN + scores['visual_phash_score'] * W_VIS_PHASH)
             # ... (intent boosting) ...
             final_ranked_list_output.append({
                'video_id': video_id, 'combined_score': combined_score, # ... other scores ...
                'kw_score': scores['keyword_score'], 'sem_text_score': scores['semantic_text_score'],
                'vis_cnn_score': scores['visual_cnn_score'], 'vis_phash_score': scores['visual_phash_score'],
                'publication_date': scores['publication_date'], 'match_types': list(scores['match_type_flags']),
                'best_match_timestamp_ms': scores.get('best_match_timestamp_ms'),
                'text_snippet': scores.get('text_snippet')
            })
        final_ranked_list_output.sort(key=lambda x: (x['combined_score'], x['publication_date']), reverse=True)
        # ... (Fallback logic for empty results if needed) ...
        logger.info(f"RARAgent: Rank/Filter. In: {len(persisted_video_source_objects)} sources. Out: {len(final_ranked_list_output)} items.")
        return final_ranked_list_output


