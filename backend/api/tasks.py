# backend/api/tasks.py

from celery import shared_task
from django.utils import timezone
import time # For simulating work
from .models import SearchTask #, Video, VideoSource, Transcript, etc. - import as needed by the task
from backend.ai_agents.main_orchestrator import PapriAIAgentOrchestrator # Assuming orchestrator is in backend/ai_agents
import subprocess
import tempfile

@shared_task(bind=True, name='api.index_video_visual_features')
def index_video_visual_features(self, video_source_id):
    print(f"Celery Task: Starting visual feature indexing for VideoSource ID {video_source_id}")
    try:
        video_source = VideoSource.objects.select_related('video').get(id=video_source_id)
        if not video_source.video: # Ensure linked to a canonical video
            print(f"VisualIndexTask: VideoSource {video_source_id} not linked to a Papri Video. Skipping.")
            return {"status": "skipped", "reason": "Not linked to Papri Video"}

        # 1. Download the video using yt-dlp to a temporary location
        video_url = video_source.original_url
        # Create a temporary directory for the download
        with tempfile.TemporaryDirectory(prefix="papri_video_download_") as tmpdir:
            # -f bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4 chooses best MP4 or merges.
            # --output specifies template for filename. We want a predictable name or just one file.
            # Using %(id)s.%(ext)s to get platform_video_id as filename.
            # Or just a fixed name like 'video.mp4' inside tmpdir.
            output_template = os.path.join(tmpdir, "downloaded_video.%(ext)s")
            # Limit download duration for testing/sanity (e.g., first 5 minutes) using --download-sections
            # For full analysis, remove or adjust time limits.
            # Example: "*0-5:00" for first 5 minutes.
            # ydl_opts = ['-f', 'best[ext=mp4]/mp4', '--output', output_template, '--download-sections', '*0-1:00'] # First 1 min for testing
            ydl_opts = ['-f', 'worstvideo[ext=mp4][height<=480]/mp4', # Get smaller video for faster processing
                        '--output', output_template,
                        '--no-playlist', # Ensure only single video if URL is part of playlist
                        '--max-filesize', '100M', # Limit filesize
                        '--extractor-args', 'youtube:player_client=web'] # Helps with some YT downloads

            print(f"VisualIndexTask: Downloading {video_url} with yt-dlp to {tmpdir}...")

            process = subprocess.run(['yt-dlp'] + ydl_opts + [video_url], capture_output=True, text=True, check=False)

            if process.returncode != 0:
                print(f"VisualIndexTask: yt-dlp failed for {video_url}. Error: {process.stderr}")
                # Update VideoSource or a VisualProcessingLog model to indicate download failure
                return {"status": "failed_download", "error": process.stderr}

            # Find the downloaded file (yt-dlp might add video ID to filename)
            downloaded_file_path = None
            for f_name in os.listdir(tmpdir):
                if f_name.startswith("downloaded_video"):
                    downloaded_file_path = os.path.join(tmpdir, f_name)
                    break

            if not downloaded_file_path:
                print(f"VisualIndexTask: Could not find downloaded video file in {tmpdir} for {video_url}.")
                return {"status": "failed_download", "error": "Downloaded file not found."}

            print(f"VisualIndexTask: Downloaded to {downloaded_file_path}. Size: {os.path.getsize(downloaded_file_path)} bytes.")

            # 2. Call VisualAnalyzer to process this downloaded video
            analyzer = VisualAnalyzer() # Instantiates CNN, Qdrant client etc.
            result = analyzer.index_video_frames(video_source, downloaded_file_path)

            print(f"VisualIndexTask: VisualAnalyzer result for {video_source_id}: {result}")
            # Optionally, update a status on VideoSource or Video model indicating visual indexing complete/failed
            return {"status": "completed", "result": result}

    except VideoSource.DoesNotExist:
        print(f"VisualIndexTask: VideoSource ID {video_source_id} not found.")
        return {"status": "error", "reason": "VideoSource not found"}
    except Exception as e:
        print(f"VisualIndexTask: Error processing video {video_source_id}: {e}")
        # Optionally, mark the video_source as failed visual processing
        return {"status": "error", "reason": str(e)}


@shared_task(bind=True, name='api.process_search_query')
def process_search_query(self, search_task_id):
    # ... (try block, fetching search_task, search_parameters prep) ...
    try:
        # ...
        orchestrator = PapriAIAgentOrchestrator(papri_search_task_id=search_task_id)
        orchestration_result = orchestrator.execute_search(search_parameters) # Returns dict

        if orchestration_result and "error" not in orchestration_result:
            search_task.status = 'completed'
            ranked_ids = orchestration_result.get("persisted_video_ids_ranked", [])
            search_task.result_video_ids_json = ranked_ids 
            
            # Optionally store the detailed scores and match types
            # Add a new JSONField to SearchTask model: e.g., detailed_ranking_info_json
            # search_task.detailed_ranking_info_json = orchestration_result.get("results_data_detailed")
        else:
            # ... (error handling) ...
        
        search_task.updated_at = timezone.now()
        update_fields = ['status', 'error_message', 'updated_at', 'result_video_ids_json']
        # if 'detailed_ranking_info_json' in locals(): update_fields.append('detailed_ranking_info_json')
        search_task.save(update_fields=update_fields)
        # ... (return dict)
