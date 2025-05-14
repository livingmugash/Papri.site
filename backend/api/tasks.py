# backend/api/tasks.py

from celery import shared_task
from django.utils import timezone
import time # For simulating work
from .models import SearchTask #, Video, VideoSource, Transcript, etc. - import as needed by the task
from backend.ai_agents.main_orchestrator import PapriAIAgentOrchestrator # Assuming orchestrator is in backend/ai_agents
import subprocess
import tempfile

@shared_task(bind=True, name='api.index_video_visual_features', acks_late=True, time_limit=1800) # Added acks_late and time_limit
def index_video_visual_features(self, video_source_id):
    print(f"Celery Task: Starting visual feature indexing for VideoSource ID {video_source_id}")
    try:
        video_source = VideoSource.objects.select_related('video').get(id=video_source_id)
        if not video_source.video:
            # ... (handle error: not linked to Papri Video) ...
            return {"status": "skipped", "reason": "Not linked to Papri Video"}

        video_url = video_source.original_url
        with tempfile.TemporaryDirectory(prefix="papri_vid_dl_", dir=settings.MEDIA_ROOT) as tmpdir_path: # Use MEDIA_ROOT for temp
            # Ensure tmpdir_path is accessible by Celery worker
            # Using a smaller video format for faster processing during indexing.
            # Consider 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]'
            # Or 'worstvideo[ext=mp4]' if speed is paramount and visual quality for indexing can be lower.
            # --restrict-filenames for safer filenames.
            output_template = os.path.join(tmpdir_path, "%(id)s.%(ext)s") # Use video ID from platform as filename
            
            # yt-dlp options:
            # - Slower but more compatible: 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'
            # - Faster for processing: 'worstvideo[ext=mp4][height<=360]' (small, fast)
            # - Limit duration for testing: '--download-sections', '*0-2:00' (first 2 minutes)
            ydl_opts = [
                '-f', 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]/mp4', # Prefer mp4, up to 480p
                '--output', output_template,
                '--no-playlist',
                '--max-filesize', '200M', # Max 200MB download
                '--socket-timeout', '30', # Timeout for connections
                # '--retries', '3', # Number of retries
                '--fragment-retries', '3',
                '--restrict-filenames', # For safer filenames
                '--progress', # Show progress from yt-dlp
                # '--download-sections', '*0-3:00', # Example: only first 3 minutes
                '--extractor-args', 'youtube:player_client=web', # Helps with some YouTube downloads
            ]
            print(f"VisualIndexTask: Downloading {video_url} with yt-dlp opts: {' '.join(ydl_opts)}")
            
            process = subprocess.run(['yt-dlp'] + ydl_opts + [video_url], capture_output=True, text=True, check=False, encoding='utf-8')

            downloaded_file_path = None
            if process.returncode == 0:
                # Try to find the file based on platform_video_id
                # yt-dlp output template uses %(id)s which is platform_video_id
                expected_filename_base = video_source.platform_video_id
                for f_name in os.listdir(tmpdir_path):
                    if f_name.startswith(expected_filename_base):
                        downloaded_file_path = os.path.join(tmpdir_path, f_name)
                        break
                if not downloaded_file_path: # Fallback if filename pattern is different
                     for f_name in os.listdir(tmpdir_path): # Find first video-like file
                        if any(f_name.endswith(ext) for ext in ['.mp4', '.mkv', '.webm', '.mov', '.avi']):
                            downloaded_file_path = os.path.join(tmpdir_path, f_name)
                            break
                if downloaded_file_path:
                    print(f"VisualIndexTask: Downloaded to {downloaded_file_path}. Size: {os.path.getsize(downloaded_file_path)} bytes.")
                else:
                    print(f"VisualIndexTask: yt-dlp success but could not find downloaded file. stdout: {process.stdout}, stderr: {process.stderr}")
                    return {"status": "failed_download", "error": "Downloaded file not found after successful download."}
            else:
                print(f"VisualIndexTask: yt-dlp failed for {video_url}. ReturnCode: {process.returncode}. Error: {process.stderr[-500:]}. Stdout: {process.stdout[-500:]}")
                # Log failure for this video_source if needed
                return {"status": "failed_download", "error": process.stderr[-500:]} # Store last 500 chars of error

            analyzer = VisualAnalyzer()
            result = analyzer.index_video_frames(video_source, downloaded_file_path)
            
            # Cleanup: The TemporaryDirectory context manager handles directory removal.
            print(f"VisualIndexTask: VisualAnalyzer result for {video_source_id}: {result}")
            # Update video_source status: e.g., video_source.visual_indexing_status = 'completed' / 'failed'
            # video_source.last_visual_indexed_at = timezone.now()
            # video_source.save()
            return {"status": "completed_visual_indexing", "result": result}

    except VideoSource.DoesNotExist: # ... (error handling)
        return {"status": "error", "reason": "VideoSource not found"}
    except Exception as e: # ... (error handling)
        # Log the full traceback for unexpected errors
        import traceback
        print(f"VisualIndexTask: UNEXPECTED error processing video {video_source_id}: {e}\n{traceback.format_exc()}")
        return {"status": "error_unexpected", "reason": str(e)}


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
