# backend/ai_agents/main_orchestrator.py

from .query_understanding_agent import QueryUnderstandingAgent
from .source_orchestration_agent import SourceOrchestrationAgent
# from .content_analysis_agent import ContentAnalysisAgent # We'll create this later
# from .result_aggregation_agent import ResultAggregationAgent # And this later

from api.models import SearchTask, Video, VideoSource # To save results

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
            # analyzed_content = self.ca_agent.analyze_content(raw_video_data_from_sources, processed_query_data)
            # For now, let's assume raw_video_data_from_sources is what we'll try to save/rank.
            # This means we're doing a basic metadata search first. Transcript/Image analysis comes next.
            analyzed_content = raw_video_data_from_sources # Direct pass-through for initial implementation

            # 4. Aggregate and Rank Results (RARAgent) - Placeholder for now
            # ranked_results = self.rar_agent.aggregate_and_rank(analyzed_content, processed_query_data)
            # For now, simple ranking or just passing through
            # We also need to save these results to our Django models (Video, VideoSource)
            
            saved_video_sources = self._save_results_to_db(analyzed_content)
            print(f"Orchestrator: Saved/Updated {len(saved_video_sources)} video sources to DB.")

            # The RARAgent would produce the final list of Video objects (or their IDs) to be returned.
            # For now, let's just return the saved_video_sources as a proxy for ranked_results.
            # This would actually be a list of serialized Video data.
            final_results_for_response = [
                {
                    "id": vs.video.id,
                    "title": vs.video.title,
                    "description": vs.video.description,
                    "publication_date": vs.video.publication_date.isoformat() if vs.video.publication_date else None,
                    "primary_thumbnail_url": vs.video.primary_thumbnail_url,
                    "sources": [{
                        "platform_name": vs.platform_name,
                        "original_url": vs.original_url,
                        "embed_url": vs.embed_url
                    }]
                } for vs in saved_video_sources
            ]


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
