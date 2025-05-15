# backend/ai_agents/main_orchestrator.py

from .query_understanding_agent import QueryUnderstandingAgent
from .source_orchestration_agent import SourceOrchestrationAgent
from .content_analysis_agent import ContentAnalysisAgent # We'll create this later
from .result_aggregation_agent import ResultAggregationAgent # And this later
from api.models import SearchTask, Video, VideoSource # To save results
from api.models import Video, VideoSource, Transcript # For saving results
from django.utils import timezone
from django.db import transaction # For atomic database operations

class PapriAIAgentOrchestrator:
    def __init__(self, papri_search_task_id):
        self.papri_search_task_id = papri_search_task_id
        self.q_agent = QueryUnderstandingAgent()
        self.so_agent = SourceOrchestrationAgent()
        self.ca_agent = ContentAnalysisAgent()
        self.ra_agent = ResultAggregationAgent()
        print(f"Orchestrator initialized for SearchTask ID: {self.papri_search_task_id}")

    def execute_search(self, search_parameters):
        # ... (1. Query Understanding -> processed_query_data)
        # ... (2. Source Orchestration -> raw_video_data_from_sources)
        # ... (3. Persist Basic Video Info -> persisted_video_source_objects)
        # ... (4. Content Analysis -> all_analysis_data)
        # (Code for steps 1-4 largely remains the same from Step 25 / previous versions)
        # 5. Result Aggregation & Ranking
        ranked_results_details = []
        try:
            # Pass the filters from the initial search parameters
            # RARAgent will also need processed_query_data for query terms/embeddings
            # and all_analysis_data for keywords from transcripts of currently fetched videos
            current_filters = search_parameters.get('applied_filters', {})

            ranked_results_details = self.ra_agent.aggregate_and_rank_results(
                persisted_video_source_objects, 
                processed_query_data,
                all_analysis_data,
                filters=current_filters # NEW: Pass filters
            )
        except Exception as e:
            # ... (fallback) ...
            logger.error(f"Orchestrator: Error in RARAgent: {e}", exc_info=True)
            ranked_results_details = [{'video_id': vs.video.id, 'combined_score': 0.0, 'match_types': ['fallback_fetch'], 'best_match_timestamp_ms': None} for vs in persisted_video_source_objects if vs.video]

        final_ranked_video_ids = [item['video_id'] for item in ranked_results_details]
        # ... (return dict as before, including "results_data_detailed": ranked_results_details) ...
        return {
            "message": "Search orchestrated.",
            "items_fetched_from_sources": len(raw_video_data_from_sources if 'raw_video_data_from_sources' in locals() else []),
            "items_analyzed_for_content": len(all_analysis_data if 'all_analysis_data' in locals() else {}),
            "ranked_video_count": len(final_ranked_video_ids),
            "persisted_video_ids_ranked": final_ranked_video_ids,
            "results_data_detailed": ranked_results_details
        }

        try:
            if search_parameters.get('query_text') and search_parameters.get('query_image_ref'):
                text_data = self.q_agent.process_text_query(search_parameters['query_text'])
                image_data = self.q_agent.process_image_query(search_parameters['query_image_ref'])
                processed_query_data = {**text_data, **image_data, 'intent': 'hybrid_text_visual_search'}
            elif search_parameters.get('query_text'): processed_query_data = self.q_agent.process_text_query(search_parameters['query_text'])
            elif search_parameters.get('query_image_ref'): processed_query_data = self.q_agent.process_image_query(search_parameters['query_image_ref'])
            else: return {"error": "No query input.", "status_code": 400}
            if not processed_query_data: return {"error": "Query understanding failed.", "status_code": 500}
        except Exception as e: return {"error": f"Query understanding failed: {e}", "status_code": 500}

        raw_video_data_from_sources = []
        if processed_query_data.get('intent') != 'visual_similarity_search':
            try: raw_video_data_from_sources = self.so_agent.fetch_content_from_sources(processed_query_data)
            except Exception as e: print(f"Orchestrator: Warning - SOIAgent error: {e}")
        
        persisted_video_source_objects = []
        if raw_video_data_from_sources:
            try: persisted_video_source_objects = self._persist_basic_video_info(raw_video_data_from_sources)
            except Exception as e: print(f"Orchestrator: Error persisting basic video info: {e}")

        all_analysis_data = {} 
        if persisted_video_source_objects:
            for vs_obj in persisted_video_source_objects:
                raw_data = next((item for item in raw_video_data_from_sources if item.get('original_url') == vs_obj.original_url), None)
                if vs_obj and raw_data and vs_obj.video:
                    try:
                        analysis_output = self.ca_agent.analyze_video_content(vs_obj, raw_data) # Mainly transcript analysis
                        if analysis_output: all_analysis_data[vs_obj.id] = analysis_output
                    except Exception as e: print(f"Orchestrator: Error CAAgent for source {vs_obj.id}: {e}")


         # 5. Result Aggregation & Ranking (RARAgent)
        ranked_results_details = [] # Expects list of dicts from RARAgent
        try:
            ranked_results_details = self.ra_agent.aggregate_and_rank_results(
                persisted_video_source_objects, 
                processed_query_data,
                all_analysis_data 
            )
        except Exception as e:
            # ... (fallback as before) ...
            print(f"Orchestrator: Error in Result Aggregation Agent: {e}")
            ranked_results_details = [{'video_id': vs.video.id, 'combined_score': 0.0, 'match_types': ['fallback_fetch'], 'best_match_timestamp_ms': None} for vs in persisted_video_source_objects if vs.video]

        final_ranked_video_ids = [item['video_id'] for item in ranked_results_details]


        return {
            "message": "Search orchestrated with multi-modal ranking.",
            "items_fetched_from_sources": len(raw_video_data_from_sources),
            "items_analyzed_for_content": len(all_analysis_data),
            "ranked_video_count": len(final_ranked_video_ids),
            "persisted_video_ids_ranked": final_ranked_video_ids, # For SearchTask.result_video_ids_json
            "results_data_detailed": ranked_results_with_scores_and_types 
        }

    # ... (_persist_basic_video_info method remains the same) ...
 

    @transaction.atomic
    def _persist_basic_video_info(self, video_data_list):
        # ... (This method remains mostly the same as defined in Step 17/18)
        # Ensure it correctly links VideoSource to a canonical Video object.
        # The key challenge here is robust Video object deduplication.
        # For now, it uses title as a weak de-dupe key for Video.
        # Ideally, it would use a content-based deduplication_hash if available.
        created_or_updated_sources = []
        video_map_by_title = {} # Simple cache to reduce DB hits for Video with same title in this batch

        for item_data in video_data_list:
            original_url = item_data.get('original_url')
            if not original_url: continue
            platform_name = item_data.get('platform_name')
            platform_video_id = item_data.get('platform_video_id')
            if not platform_name or not platform_video_id: continue

            video_source, source_created = VideoSource.objects.get_or_create(
                original_url=original_url,
                defaults={
                    'platform_name': platform_name,
                    'platform_video_id': platform_video_id,
                }
            )

            papri_video = video_source.video
            video_is_newly_associated = False

            if not papri_video:
                temp_title = item_data.get('title', 'Untitled Video')
                # Attempt to find an existing Video by title (weak de-dupe)
                if temp_title in video_map_by_title:
                    papri_video = video_map_by_title[temp_title]
                else:
                    video_defaults = {
                        'description': item_data.get('description'),
                        'duration_seconds': item_data.get('duration_seconds'),
                        'primary_thumbnail_url': item_data.get('thumbnail_url'),
                    }
                    pub_date_str_defaults = item_data.get('publication_date')
                    if pub_date_str_defaults:
                        try: video_defaults['publication_date'] = timezone.datetime.fromisoformat(pub_date_str_defaults.replace('Z', '+00:00'))
                        except ValueError:
                            try: video_defaults['publication_date'] = timezone.datetime.strptime(pub_date_str_defaults, "%Y-%m-%dT%H:%M:%S.%fZ")
                            except ValueError: pass

                    # get_or_create for Video based on title.
                    # THIS IS STILL A WEAK DEDUPLICATION for the canonical Video object.
                    # A content-based hash on the Video model is the proper way.
                    papri_video, video_created = Video.objects.get_or_create(
                        title=temp_title, 
                        defaults=video_defaults
                    )
                    video_map_by_title[temp_title] = papri_video # Cache it for this batch
                    if video_created:
                        print(f"Orchestrator Persist: Created NEW Papri Video ID: {papri_video.id} for title '{papri_video.title}'")
                
                video_source.video = papri_video # Link source to this video
                video_is_newly_associated = True

            # Update Video fields if new data is more complete or different
            # (Idempotent updates)
            changed_video_fields = []
            if item_data.get('title') and item_data.get('title') != papri_video.title:
                papri_video.title = item_data.get('title'); changed_video_fields.append('title')
            if item_data.get('description') and item_data.get('description') != papri_video.description:
                papri_video.description = item_data.get('description'); changed_video_fields.append('description')
            if item_data.get('duration_seconds') is not None and item_data.get('duration_seconds') != papri_video.duration_seconds:
                papri_video.duration_seconds = item_data.get('duration_seconds'); changed_video_fields.append('duration_seconds')
            if item_data.get('thumbnail_url') and item_data.get('thumbnail_url') != papri_video.primary_thumbnail_url:
                papri_video.primary_thumbnail_url = item_data.get('thumbnail_url'); changed_video_fields.append('primary_thumbnail_url')
            
            pub_date_str = item_data.get('publication_date')
            if pub_date_str:
                try: new_pub_date = timezone.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except ValueError:
                    try: new_pub_date = timezone.datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError: new_pub_date = None
                if new_pub_date and new_pub_date != papri_video.publication_date:
                    papri_video.publication_date = new_pub_date; changed_video_fields.append('publication_date')
            
            if changed_video_fields:
                papri_video.save(update_fields=changed_video_fields)

            # Update VideoSource fields
            video_source.platform_name = platform_name 
            video_source.platform_video_id = platform_video_id
            video_source.embed_url = item_data.get('embed_url')
            video_source.source_metadata_json = item_data 
            video_source.last_scraped_at = timezone.now()
            if video_is_newly_associated or source_created: # Save if video was just linked or source is new
                 video_source.save() 
            else: # Else, save only if there were other changes to video_source itself
                 video_source.save(update_fields=['platform_name', 'platform_video_id', 'video', 'embed_url', 'source_metadata_json', 'last_scraped_at'])
            
            created_or_updated_sources.append(video_source)
        
        return created_or_updated_sources


class PapriAIAgentOrchestrator:
    def __init__(self, papri_search_task_id):
        self.papri_search_task_id = papri_search_task_id
        self.q_agent = QueryUnderstandingAgent()
        self.so_agent = SourceOrchestrationAgent()
        # self.ca_agent = ContentAnalysisAgent() # To be implemented
        # self.ra_agent = ResultAggregationAgent() # To be implemented
        print(f"Orchestrator initialized for SearchTask ID: {self.papri_search_task_id}")

    def execute_search(self, search_parameters):
        """
        Main method to execute the full search and analysis pipeline.
        search_parameters: dict containing 'query_text', 'query_image_ref', 'applied_filters', etc.
        """
        print(f"Orchestrator: Executing search with params: {search_parameters}")
        processed_query_data = None
        raw_video_data_from_sources = []
        aggregated_and_ranked_results = []

        # 1. Query Understanding
        try:
            if search_parameters.get('query_text'):
                processed_query_data = self.q_agent.process_text_query(search_parameters['query_text'])
            elif search_parameters.get('query_image_ref'):
                # For now, image query understanding might be simpler or directly lead to visual search
                processed_query_data = self.q_agent.process_image_query(search_parameters['query_image_ref'])
            else:
                print("Orchestrator: No query text or image reference provided.")
                return {"error": "No query input."}
            
            print(f"Orchestrator: Processed query data: {processed_query_data}")
        except Exception as e:
            print(f"Orchestrator: Error in Query Understanding Agent: {e}")
            return {"error": f"Query understanding failed: {e}"}

        # 2. Source Orchestration & Interfacing (Fetching raw data)
        # For now, let's assume we only act on text queries for API fetching.
        # Image queries will later involve fetching frames from candidate videos or searching an image index.
        if processed_query_data and processed_query_data.get('intent') == 'general_video_search':
            try:
                # SOAgent fetches data from YouTube, Vimeo, Dailymotion based on processed_query_data
                # For the first step, SOAgent will primarily use 'processed_query_data.get("processed_query")'
                raw_video_data_from_sources = self.so_agent.fetch_content_from_sources(processed_query_data)
                print(f"Orchestrator: SOIAgent fetched {len(raw_video_data_from_sources)} raw items.")
            except Exception as e:
                print(f"Orchestrator: Error in Source Orchestration Agent: {e}")
                # Continue with any data fetched, or return error if critical
                # return {"error": f"Source orchestration failed: {e}"}
        elif processed_query_data and processed_query_data.get('intent') == 'visual_similarity_search':
            # For image search, the flow will be different.
            # CAAgent would be more directly involved in comparing image features.
            # SOAgent might be used to get candidate videos if text context is also provided.
            print(f"Orchestrator: Visual similarity search intent noted. CA & RA agents will handle specific logic later.")
            # For now, we won't fetch from external sources for pure image search via this path.
            # This will primarily search our own indexed visual features.

     persisted_video_source_objects = []
        if raw_video_data_from_sources:
            persisted_video_source_objects = self._persist_basic_video_info(raw_video_data_from_sources)
            print(f"Orchestrator: Persisted basic info for {len(persisted_video_source_objects)} video sources.")


        # 3. Content Analysis (Stubbed for now)
       all_analysis_data = {} # Stores output from CAAgent, keyed by video_source_obj.id
        if persisted_video_source_objects:
            for video_source_obj in persisted_video_source_objects:
                raw_data_item_for_source = next(
                    (item for item in raw_video_data_from_sources if item.get('original_url') == video_source_obj.original_url), None
                )
                if video_source_obj and raw_data_item_for_source: # raw_data_item needed for platforms without direct transcript API
                    try:
                        analysis_output = self.ca_agent.analyze_video_content(video_source_obj, raw_data_item_for_source)
                        if analysis_output:
                            all_analysis_data[video_source_obj.id] = analysis_output
                    except Exception as e:
                        print(f"Orchestrator: Error calling CAAgent for source {video_source_obj.id}: {e}")
        print(f"Orchestrator: Content Analysis completed. Processed {len(all_analysis_data)} sources for analysis.")
        

        # 4. Result Aggregation & Ranking (Simplified for now)
        # RA Agent would:
        # - Normalize data from different sources.
        # - Perform deduplication.
        # - Rank results based on relevance, recency, etc.
        # For now, let's just save the fetched data to our DB models.
        try:
            persisted_results_summary = self._persist_results(analyzed_content_data)
            aggregated_and_ranked_results = persisted_results_summary # Simplified
            print(f"Orchestrator: Results persisted. Summary: {persisted_results_summary}")
        except Exception as e:
            print(f"Orchestrator: Error in Result Aggregation/Persistence: {e}")
            return {"error": f"Result processing failed: {e}"}


        # 5. Return final results (or a summary/pointer to them)
        # The Celery task will use this to update the SearchTask model.
        return {
            "message": "Search orchestrated successfully.",
            "items_processed_from_sources": len(raw_video_data_from_sources),
            "items_persisted_count": persisted_results_summary.get("saved_videos_count", 0),
            "persisted_video_ids": persisted_results_summary.get("saved_video_ids", []),
            # In future, could return a list of serialized Video objects or just IDs
        }

    @transaction.atomic # Ensure database operations are atomic
    def _persist_results(self, video_data_list):
        """
        Saves or updates video data fetched from sources into the database.
        Performs basic deduplication based on original_url.
        """
        saved_videos_count = 0
        newly_created_videos = 0
        updated_videos = 0
        saved_video_ids = [] # Store Papri Video object IDs

        for item_data in video_data_list:
            original_url = item_data.get('original_url')
            if not original_url:
                print(f"Orchestrator Persist: Skipping item due to missing original_url: {item_data.get('title')}")
                continue

            platform_name = item_data.get('platform_name')
            platform_video_id = item_data.get('platform_video_id')

            if not platform_name or not platform_video_id:
                print(f"Orchestrator Persist: Skipping item due to missing platform info: {item_data.get('title')}")
                continue

            try:
                # Check if this specific VideoSource already exists
                video_source, source_created = VideoSource.objects.get_or_create(
                    original_url=original_url,
                    defaults={
                        'platform_name': platform_name,
                        'platform_video_id': platform_video_id,
                        # 'video' will be set below
                    }
                )

                # Now handle the canonical Video object
                # For simplicity, we try to find an existing Video via the video_source if it existed,
                # or create a new Video. More sophisticated deduplication needed later.
                papri_video = None
                if not source_created and video_source.video:
                    papri_video = video_source.video
                    # Update existing canonical Video fields if new data is better/more complete
                    papri_video.title = item_data.get('title') or papri_video.title
                    papri_video.description = item_data.get('description') or papri_video.description
                    papri_video.duration_seconds = item_data.get('duration_seconds') or papri_video.duration_seconds
                    papri_video.primary_thumbnail_url = item_data.get('thumbnail_url') or papri_video.primary_thumbnail_url
                    
                    pub_date_str = item_data.get('publication_date')
                    if pub_date_str:
                        try:
                            papri_video.publication_date = timezone.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        except ValueError:
                            try: # Handle cases like YouTube's format which might be slightly different or other timestamps
                                papri_video.publication_date = timezone.datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                            except ValueError:
                                print(f"Could not parse publication_date: {pub_date_str}")
                                # Keep existing if parse fails
                    papri_video.save()
                    updated_videos +=1
                else: # New source or source existed but had no linked video (should not happen with get_or_create logic)
                    papri_video = Video.objects.create(
                        title=item_data.get('title', 'Untitled Video'),
                        description=item_data.get('description'),
                        duration_seconds=item_data.get('duration_seconds'),
                        primary_thumbnail_url=item_data.get('thumbnail_url')
                    )
                    pub_date_str = item_data.get('publication_date')
                    if pub_date_str:
                        try:
                            papri_video.publication_date = timezone.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        except ValueError:
                             try:
                                papri_video.publication_date = timezone.datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                             except ValueError:
                                print(f"Could not parse publication_date: {pub_date_str}")
                    papri_video.save()
                    newly_created_videos +=1
                
                # Link VideoSource to the canonical Video and update other VideoSource fields
                video_source.video = papri_video
                video_source.platform_name = platform_name
                video_source.platform_video_id = platform_video_id
                video_source.embed_url = item_data.get('embed_url')
                # video_source.source_metadata_json = item_data # Store the whole raw item if needed
                video_source.last_scraped_at = timezone.now()
                video_source.save()
                
                saved_videos_count += 1
                saved_video_ids.append(papri_video.id)

            except Exception as e:
                print(f"Orchestrator Persist: Error saving item '{item_data.get('title')}': {e}")
                # Continue to next item

        print(f"Orchestrator Persist: Total saved/updated sources: {saved_videos_count} (New Videos: {newly_created_videos}, Updated Videos linked to existing sources: {updated_videos})")
        return {
            "saved_videos_count": saved_videos_count,
            "newly_created_videos": newly_created_videos,
            "updated_video_sources": updated_videos, # This counts source updates more than video object updates
            "saved_video_ids": saved_video_ids
        }

    def _normalize_text_for_hash(self, text):
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text) # Remove punctuation
        text = re.sub(r'\s+', ' ', text).strip() # Normalize whitespace
        # Optional: stemming or lemmatization here for more robustness
        return text

    def _generate_metadata_deduplication_hash(self, title, duration_seconds, uploader_name=None):
        """
        Generates a deduplication hash based on normalized title and duration.
        Duration is bucketed to allow for slight variations.
        """
        if not title or duration_seconds is None:
            return None # Cannot generate hash without essential components

        norm_title = self._normalize_text_for_hash(title)
        
        # Bucket duration to allow for minor discrepancies (e.g., +/- 5 seconds)
        # This is a simple bucketing strategy.
        duration_bucket = (duration_seconds // 10) * 10 if duration_seconds is not None else -1 

        # Include normalized uploader name if available and considered stable
        norm_uploader = self._normalize_text_for_hash(uploader_name) if uploader_name else ""

        # Combine the normalized components
        # Order matters for consistency.
        hash_string = f"title:{norm_title}|duration_bucket:{duration_bucket}|uploader:{norm_uploader}"
        
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()


    @transaction.atomic
    def _persist_basic_video_info(self, video_data_list):
        created_or_updated_sources = []
        processed_video_ids_in_batch = set() # To avoid processing the same canonical video multiple times within this batch

        for item_data in video_data_list:
            original_url = item_data.get('original_url')
            if not original_url: continue
            platform_name = item_data.get('platform_name')
            platform_video_id = item_data.get('platform_video_id')
            if not platform_name or not platform_video_id: continue

            # --- Step 1: Generate Deduplication Hash for the incoming item ---
            video_title = item_data.get('title')
            video_duration = item_data.get('duration_seconds') # Expecting integer seconds
            video_uploader = item_data.get('uploader_name') # Scrapers/APIs need to provide this

            # Ensure duration is an int if it's a string
            if isinstance(video_duration, str) and video_duration.isdigit():
                video_duration = int(video_duration)
            elif not isinstance(video_duration, int):
                video_duration = self._parse_duration_str(str(item_data.get('duration_str'))) # Use existing helper if duration_seconds not direct

            current_item_dedup_hash = self._generate_metadata_deduplication_hash(
                video_title, video_duration, video_uploader
            )
            
            # print(f"Orchestrator Persist: Item '{video_title}' URL '{original_url}' DedupHash: {current_item_dedup_hash}")


            # --- Step 2: Find or Create the Canonical Video object using the dedup_hash ---
            papri_video = None
            video_created_in_db = False
            if current_item_dedup_hash:
                try:
                    papri_video = Video.objects.get(deduplication_hash=current_item_dedup_hash)
                    # print(f"Orchestrator Persist: Found existing Papri Video ID {papri_video.id} by hash {current_item_dedup_hash}")
                except Video.DoesNotExist:
                    # If not found by hash, create it
                    try:
                        video_defaults = {
                            'description': item_data.get('description'),
                            'duration_seconds': video_duration, # Use parsed/validated duration
                            'primary_thumbnail_url': item_data.get('thumbnail_url'),
                            'deduplication_hash': current_item_dedup_hash # Set the hash
                        }
                        pub_date_str_defaults = item_data.get('publication_date') # This might be a string from API/scraper
                        if pub_date_str_defaults:
                            parsed_date = self._parse_publication_date_to_datetime(pub_date_str_defaults)
                            if parsed_date: video_defaults['publication_date'] = parsed_date
                        
                        papri_video = Video.objects.create(title=video_title or "Untitled Video", **video_defaults)
                        video_created_in_db = True
                        print(f"Orchestrator Persist: Created NEW Papri Video ID {papri_video.id} (Hash: {current_item_dedup_hash}) for title '{papri_video.title}'")
                    except Exception as e_create: # Catch potential IntegrityError if somehow hash was created by parallel process
                        print(f"Orchestrator Persist: Error creating Video with hash {current_item_dedup_hash}: {e_create}. Trying get again.")
                        try: papri_video = Video.objects.get(deduplication_hash=current_item_dedup_hash) # Try get again
                        except Video.DoesNotExist:
                            print(f"Orchestrator Persist: Still could not get/create video for hash {current_item_dedup_hash}. Skipping item.")
                            continue # Skip this item if canonical video cannot be established
            else: # No valid title/duration to generate a hash, less ideal scenario
                print(f"Orchestrator Persist: Could not generate dedup_hash for item '{video_title}'. Will try to link source by URL only.")
                # In this case, VideoSource linking might be problematic if it needs a Video FK immediately.
                # For now, we might skip items that can't form a dedup_hash.
                # Or, as a last resort, create a Video object without a dedup_hash (not recommended as it defeats de-dupe).
                # Let's skip for now if hash cannot be made
                continue


            if not papri_video: # If video still not found or created (e.g. error during create)
                print(f"Orchestrator Persist: Failed to establish canonical Video for item '{video_title}'. Skipping source linking.")
                continue


            # --- Step 3: Create or Update the VideoSource object and link to canonical Video ---
            video_source, source_created = VideoSource.objects.update_or_create(
                original_url=original_url, # original_url should be unique for VideoSource
                defaults={
                    'video': papri_video, # Link to the canonical Video
                    'platform_name': platform_name,
                    'platform_video_id': platform_video_id,
                    'embed_url': item_data.get('embed_url'),
                    'source_metadata_json': item_data, # Store all raw data from this source
                    'last_scraped_at': timezone.now()
                }
            )
            if source_created:
                print(f"Orchestrator Persist: Created VideoSource ID {video_source.id} for URL {original_url}, linked to Papri Video ID {papri_video.id}")
            else:
                # If source existed, ensure its video FK is correct if our dedup logic found a better canonical video
                if video_source.video_id != papri_video.id:
                    print(f"Orchestrator Persist: Re-linking existing VideoSource ID {video_source.id} from old Video ID {video_source.video_id} to new/correct canonical Video ID {papri_video.id}")
                    video_source.video = papri_video
                    video_source.save(update_fields=['video', 'last_scraped_at']) # And other fields if they changed
                # print(f"Orchestrator Persist: Updated VideoSource ID {video_source.id} for URL {original_url}")


            # --- Step 4: Update Canonical Video details if this source provides better/newer info ---
            # (Only if this canonical video hasn't been fully processed in this batch yet)
            if papri_video.id not in processed_video_ids_in_batch:
                changed_video_fields = []
                # Prefer longer description, more recent publication date, etc.
                if item_data.get('description') and (not papri_video.description or len(item_data.get('description')) > len(papri_video.description)):
                    papri_video.description = item_data.get('description'); changed_video_fields.append('description')
                
                if video_duration is not None and (papri_video.duration_seconds is None or abs(video_duration - papri_video.duration_seconds) > 5) : # Update if significantly different or not set
                    papri_video.duration_seconds = video_duration; changed_video_fields.append('duration_seconds')

                if item_data.get('thumbnail_url') and (not papri_video.primary_thumbnail_url or item_data.get('thumbnail_url') != papri_video.primary_thumbnail_url): # Update if new or different
                    papri_video.primary_thumbnail_url = item_data.get('thumbnail_url'); changed_video_fields.append('primary_thumbnail_url')
                
                new_pub_date_str = item_data.get('publication_date')
                if new_pub_date_str:
                    new_pub_datetime = self._parse_publication_date_to_datetime(new_pub_date_str)
                    if new_pub_datetime and (not papri_video.publication_date or new_pub_datetime > papri_video.publication_date): # Prefer newer date
                        papri_video.publication_date = new_pub_datetime; changed_video_fields.append('publication_date')
                
                if not papri_video.title and video_title: # Ensure title is set if it was None
                     papri_video.title = video_title; changed_video_fields.append('title')

                if changed_video_fields:
                    # print(f"Orchestrator Persist: Updating canonical Video ID {papri_video.id} with fields: {changed_video_fields}")
                    papri_video.save(update_fields=changed_video_fields)
                
                processed_video_ids_in_batch.add(papri_video.id)
            
            created_or_updated_sources.append(video_source)
        
        return created_or_updated_sources

    def _parse_publication_date_to_datetime(self, date_str): # Helper
        if not date_str: return None
        from dateutil import parser # Ensure 'pip install python-dateutil'
        try:
            dt_obj = parser.parse(date_str)
            if dt_obj.tzinfo is None or dt_obj.tzinfo.utcoffset(dt_obj) is None: # If naive
                return timezone.make_aware(dt_obj, timezone.get_default_timezone())
            return dt_obj.astimezone(timezone.utc) # Convert to UTC
        except (ValueError, TypeError, OverflowError):
            # print(f"Orchestrator: Could not parse date string robustly: {date_str}")
            return None # Fallback if robust parsing fails

    # Add _parse_duration_str to orchestrator if not already there or import from SOIAgent
    def _parse_duration_str(self, duration_str): # Helper from SOIAgent
        if not duration_str: return None
        import re
        # ... (same robust duration parsing logic from SOIAgent)
        duration_str_upper = str(duration_str).upper()
        if duration_str_upper.startswith("PT"): 
            h,m,s = 0,0,0
            h_match = re.search(r'(\d+)H', duration_str_upper); h = int(h_match.group(1)) if h_match else 0
            m_match = re.search(r'(\d+)M', duration_str_upper); m = int(m_match.group(1)) if m_match else 0
            s_match = re.search(r'(\d+)S', duration_str_upper); s = int(s_match.group(1)) if s_match else 0
            return h * 3600 + m * 60 + s
        else: 
            parts = [int(p) for p in str(duration_str).split(':') if p.isdigit()]
            if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
            if len(parts) == 2: return parts[0]*60 + parts[1]
            if len(parts) == 1 and str(duration_str).isdigit(): return parts[0]
        return None
