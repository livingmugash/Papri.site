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
        self.search_task = SearchTask.objects.get(id=self.papri_search_task_id) # For updating status/results

        # Initialize the agents
        self.q_agent = QueryUnderstandingAgent()
        self.soi_agent = SourceOrchestrationAgent()
        # self.ca_agent = ContentAnalysisAgent() # Initialize when ready
        # self.rar_agent = ResultAggregationAgent() # Initialize when ready

        print(f"Orchestrator initialized for SearchTask ID: {self.papri_search_task_id}")

    def execute_search(self, search_params):
        """
        Main method to execute the video search process.
        search_params: dict containing 'query_text', 'query_image_ref', 'applied_filters', etc.
        """
        print(f"Orchestrator: Executing search with params: {search_params}")
        processed_query_data = None
        raw_video_data_from_sources = []

        try:
            # 1. Understand the Query (QAgent)
            if search_params.get('query_text'):
                processed_query_data = self.q_agent.process_text_query(search_params['query_text'])
            elif search_params.get('query_image_ref'): # query_image_ref is the path to the temp image
                processed_query_data = self.q_agent.process_image_query(search_params['query_image_ref'])
            else:
                print("Orchestrator: No query text or image reference provided.")
                self.search_task.error_message = "No query input."
                self.search_task.status = 'failed'
                self.search_task.save()
                return {"error": "No query input.", "results": []}

            if not processed_query_data:
                print("Orchestrator: Query processing failed.")
                self.search_task.error_message = "Query understanding failed."
                self.search_task.status = 'failed'
                self.search_task.save()
                return {"error": "Query understanding failed.", "results": []}

            print(f"Orchestrator: Processed query data: {processed_query_data}")

            # 2. Fetch Content from Sources (SOIAgent)
            # SOI Agent will use processed_query_data (especially 'processed_query' or 'intent')
            # and API keys (accessed via Django settings within the agent).
            raw_video_data_from_sources = self.soi_agent.fetch_content_from_sources(processed_query_data)
            print(f"Orchestrator: SOI Agent fetched {len(raw_video_data_from_sources)} raw items.")

            # 3. Content Analysis (CAAgent) - Placeholder for now
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
        
            # 4. Aggregate and Rank Results (RARAgent) - Placeholder for now
            # ranked_results = self.rar_agent.aggregate_and_rank(analyzed_content, processed_query_data)
            # For now, simple ranking or just passing through
            # We also need to save these results to our Django models (Video, VideoSource)
            
            saved_video_sources = self._save_results_to_db(analyzed_content)
            print(f"Orchestrator: Saved/Updated {len(saved_video_sources)} video sources to DB.")

            # The RARAgent would produce the final list of Video objects (or their IDs) to be returned.
             ranked_papri_video_ids = []
        if persisted_video_source_objects: # Pass the Django objects
            try:
                # RARAgent needs the query keywords and the analysis data (which contains extracted keywords)
                ranked_papri_video_ids = self.ra_agent.aggregate_and_rank_results(
                    persisted_video_source_objects, 
                    processed_query_data,
                    all_analysis_data 
                )
                print(f"Orchestrator: RARAgent returned {len(ranked_papri_video_ids)} ranked Papri Video IDs.")
            except Exception as e:
                print(f"Orchestrator: Error in Result Aggregation Agent: {e}")
                # Fallback: use unranked IDs if ranking fails
                ranked_papri_video_ids = [vs_obj.video.id for vs_obj in persisted_video_source_objects if vs_obj.video]
        else: # No sources fetched or persisted
             print(f"Orchestrator: No persisted video sources to rank.")


        return {
            "message": "Search, analysis, and ranking orchestrated.",
            "items_processed_from_sources": len(raw_video_data_from_sources),
            "items_analyzed_for_content": len(all_analysis_data),
            "persisted_video_ids": ranked_papri_video_ids, # Return RANKED Papri Video IDs
        }

    @transaction.atomic
    def _persist_basic_video_info(self, video_data_list):
        # ... (This method remains the same as defined in the previous step)
        # It returns a list of VideoSource Django model instances.
        created_or_updated_sources = []
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
                # Simplified Video creation/linking. Needs robust de-duplication strategy for Video model later.
                # For now, create a new Video if no existing one is linked to this source,
                # or if creating one based on title (or other de-dupe key) doesn't find one.
                # This might lead to multiple Papri Video objects for the same conceptual video if it appears
                # on different sources with slightly different metadata.
                # A proper deduplication_hash on Video model is crucial here.
                temp_title = item_data.get('title', 'Untitled Video')
                
                # Attempt to find by a potential deduplication_hash if SOIAgent could provide one
                # For now, this is a simplification and might create duplicate Video entries.
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
                        except ValueError: pass # Silently ignore if date format is unparseable for defaults

                papri_video, video_created = Video.objects.get_or_create(
                    title=temp_title, # Using title as a weak de-dupe key for Video object for now.
                                      # This IS NOT ROBUST. Replace with a proper deduplication_hash.
                    defaults=video_defaults
                )
                if video_created:
                    print(f"Orchestrator Persist: Created NEW Papri Video ID: {papri_video.id} for title '{papri_video.title}'")
                video_source.video = papri_video # Link source to this video
                video_is_newly_associated = True


            # Update Video fields (idempotently)
            papri_video.title = item_data.get('title') or papri_video.title # Ensure title is set
            papri_video.description = item_data.get('description') or papri_video.description
            papri_video.duration_seconds = item_data.get('duration_seconds') or papri_video.duration_seconds
            papri_video.primary_thumbnail_url = item_data.get('thumbnail_url') or papri_video.primary_thumbnail_url
            pub_date_str = item_data.get('publication_date')
            current_pub_date = papri_video.publication_date
            if pub_date_str:
                try: new_pub_date = timezone.datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except ValueError:
                    try: new_pub_date = timezone.datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError: new_pub_date = None; print(f"Could not parse publication_date: {pub_date_str}")
                if new_pub_date and (not current_pub_date or new_pub_date != current_pub_date) : # Check before assigning
                    papri_video.publication_date = new_pub_date
            papri_video.save()

            # Update VideoSource fields
            video_source.platform_name = platform_name 
            video_source.platform_video_id = platform_video_id
            video_source.embed_url = item_data.get('embed_url')
            video_source.source_metadata_json = item_data 
            video_source.last_scraped_at = timezone.now()
            if video_is_newly_associated: # Save if video was just linked
                 video_source.save()
            else: # Else, save only if there were other changes to video_source itself
                 video_source.save(update_fields=['platform_name', 'platform_video_id', 'embed_url', 'source_metadata_json', 'last_scraped_at'])

            created_or_updated_sources.append(video_source)
        
        return created_or_updated_sources


            # Update search task with a summary (e.g., number of results)
            # self.search_task.result_summary_json = {"items_found": len(final_results_for_response)}
            # self.search_task.save(update_fields=['result_summary_json'])

            return {"message": "Search executed", "results_data": final_results_for_response}

        except Exception as e:
            error_msg = f"Orchestrator error during search execution: {str(e)}"
            print(error_msg)
            self.search_task.error_message = error_msg[:1000] # Truncate
            self.search_task.status = 'failed'
            self.search_task.save()
            # Potentially re-raise or handle more gracefully
            return {"error": error_msg, "results_data": []}

    def _save_results_to_db(self, video_data_list):
        """
        Saves or updates video data fetched from sources into the Papri database.
        video_data_list: A list of dictionaries, where each dict has keys like
                         'platform_name', 'platform_video_id', 'title', 'original_url', etc.
        Returns a list of saved/updated VideoSource objects.
        """
        saved_sources = []
        for item_data in video_data_list:
            if not item_data.get('original_url') or not item_data.get('platform_name') or not item_data.get('platform_video_id'):
                print(f"Skipping item due to missing essential data: {item_data.get('title', 'N/A')}")
                continue
            
            try:
                # Check if VideoSource already exists
                video_source, created_vs = VideoSource.objects.get_or_create(
                    original_url=item_data['original_url'],
                    defaults={
                        'platform_name': item_data['platform_name'],
                        'platform_video_id': item_data['platform_video_id'],
                        # 'video' will be set below
                    }
                )

                # If VideoSource is new, or if its related Video doesn't exist or needs update
                # This logic needs to be robust for deduplicating Video entries.
                # For now, a simple approach: if vs is new, create video. If vs exists, update its video.
                # A better approach uses a deduplication_hash on the Video model.

                video_defaults = {
                    'title': item_data.get('title', 'Untitled Video'),
                    'description': item_data.get('description'),
                    'duration_seconds': item_data.get('duration_seconds'),
                    'publication_date': item_data.get('publication_date'), # Ensure this is datetime
                    'primary_thumbnail_url': item_data.get('thumbnail_url'),
                    # 'deduplication_hash': generate_video_dedup_hash(item_data) # TODO
                }
                
                # Attempt to find an existing Video based on some criteria (e.g. title+duration, or a future dedup hash)
                # This is a simplified deduplication.
                # A more robust deduplication would involve checking the deduplication_hash
                # or more complex matching if multiple sources point to the same conceptual video.
                related_video = None
                if not created_vs and video_source.video: # VideoSource existed, use its video
                    related_video = video_source.video
                    # Update existing video details if new data is better/more complete
                    for key, value in video_defaults.items():
                        if value is not None: # Only update if new value is provided
                             setattr(related_video, key, value)
                    related_video.save()
                else: # New VideoSource, or existing one without a video, try to find or create Video
                    # This part is tricky without a good global video identifier or robust deduplication_hash
                    # For now, let's assume we create a new Video if the VideoSource is new.
                    # If you have a strong `deduplication_hash` logic for the Video model:
                    # video_dedup_hash = generate_video_dedup_hash(item_data)
                    # related_video, created_video = Video.objects.update_or_create(
                    #     deduplication_hash=video_dedup_hash,
                    #     defaults=video_defaults
                    # )
                    # For now, let's just create a new video if the source is new.
                    # This will lead to duplicates if the same video is on multiple platforms and we don't have a global ID.
                    if created_vs:
                        related_video = Video.objects.create(**video_defaults)
                    elif not video_source.video: # VS existed but had no video somehow
                         related_video = Video.objects.create(**video_defaults)


                if related_video:
                    video_source.video = related_video
                
                # Update other VideoSource fields
                video_source.platform_name = item_data['platform_name']
                video_source.platform_video_id = item_data['platform_video_id']
                video_source.embed_url = item_data.get('embed_url')
                video_source.source_metadata_json = item_data # Store the whole raw item
                video_source.last_scraped_at = timezone.now()
                video_source.save()
                saved_sources.append(video_source)

            except Exception as e:
                print(f"Orchestrator: Error saving item '{item_data.get('title', 'N/A')}' to DB: {e}")
        
        return saved_sources


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
