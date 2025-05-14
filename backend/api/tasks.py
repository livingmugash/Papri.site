# backend/api/tasks.py

from celery import shared_task
from django.utils import timezone
import time # For simulating work
from .models import SearchTask #, Video, VideoSource, Transcript, etc. - import as needed by the task
from backend.ai_agents.main_orchestrator import PapriAIAgentOrchestrator # Assuming orchestrator is in backend/ai_agents
from django.conf import settings
import subprocess
import tempfile
from api.models import VideoSource # Assuming models are in api.models
from .analyzer_instances import visual_analyzer_instance # Using a shared instance

# Create backend/api/analyzer_instances.py:
# from backend.ai_agents.visual_analyzer import VisualAnalyzer
# visual_analyzer_instance = VisualAnalyzer() # Instantiate once
# T

@shared_task(bind=True, name='api.index_video_visual_features', acks_late=True, time_limit=1800, max_retries=1)
def index_video_visual_features(self, video_source_id):
    print(f"Celery VisualIndex: Starting for VSID {video_source_id}")
    try:
        video_source = VideoSource.objects.select_related('video').get(id=video_source_id)
        if not video_source.video:
            print(f"Celery VisualIndex: VSID {video_source_id} not linked to a Papri Video. Skipping.")
            # Optionally update a status on video_source to prevent retries for this reason
            return {"status": "skipped_no_papri_video_link"}
        if not video_source.original_url:
            print(f"Celery VisualIndex: VSID {video_source_id} has no original_url. Skipping.")
            return {"status": "skipped_no_original_url"}

        video_url = video_source.original_url
        
        # Create a temporary directory within MEDIA_ROOT if possible for easier cleanup/management
        # Ensure MEDIA_ROOT is writable by Celery worker.
        # Fallback to system temp if MEDIA_ROOT is not suitable or configured.
        temp_download_basedir = os.path.join(settings.MEDIA_ROOT, "temp_video_downloads")
        os.makedirs(temp_download_basedir, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix=f"papri_dl_{video_source_id}_", dir=temp_download_basedir) as tmpdir_path:
            output_template = os.path.join(tmpdir_path, f"{video_source.platform_video_id or video_source_id}.%(ext)s")
            
            # Refined yt-dlp options
            ydl_opts = [
                '-f', 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]/mp4',
                '--output', output_template,
                '--no-playlist', '--max-filesize', '250M', # Increased slightly
                '--socket-timeout', '60', '--retries', '2', '--fragment-retries', '2',
                '--restrict-filenames', '--no-warnings', # Suppress yt-dlp warnings if too noisy
                '--extractor-args', 'youtube:player_client=web;youtube:skip=hls,dash', # Try to force progressive for YT
                # '--verbose' # For extreme debugging of yt-dlp
            ]
            print(f"Celery VisualIndex: Downloading {video_url} with yt-dlp...")
            
            process = subprocess.run(['yt-dlp'] + ydl_opts + [video_url], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')

            downloaded_file_path = None
            if process.returncode == 0:
                # Find the downloaded file, yt-dlp might slightly alter filename based on title if %(id)s not unique enough
                for f_name in sorted(os.listdir(tmpdir_path)): # Sort to get a predictable first if multiple (shouldn't happen with good template)
                    if any(f_name.endswith(ext) for ext in ['.mp4', '.mkv', '.webm', '.avi', '.mov']):
                        downloaded_file_path = os.path.join(tmpdir_path, f_name)
                        break
                if downloaded_file_path:
                    print(f"Celery VisualIndex: Downloaded to {downloaded_file_path}. Size: {os.path.getsize(downloaded_file_path)} bytes.")
                else: # yt-dlp said success but file not found
                    print(f"Celery VisualIndex: yt-dlp success (code 0) but downloaded file not found in {tmpdir_path}. stdout: {process.stdout[-1000:]}")
                    # Try to list files for debugging
                    print(f"Files in tmpdir: {os.listdir(tmpdir_path)}")
                    return {"status": "failed_download_file_missing", "error": "Downloaded file not found post-yt-dlp."}
            else: # yt-dlp failed
                error_output = f"yt-dlp failed (code {process.returncode}).\nStderr: {process.stderr[-1000:]}\nStdout: {process.stdout[-1000:]}"
                print(f"Celery VisualIndex: {error_output}")
                # Update VideoSource with failure status
                video_source.meta_visual_processing_status = 'download_failed' # Add this field to VideoSource model
                video_source.meta_visual_processing_error = error_output[:500]
                video_source.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])
                return {"status": "failed_download", "error": error_output}

            # Call VisualAnalyzer using the shared instance
            # This analyzer_instances.py pattern is good for heavy objects in Celery.
            result = visual_analyzer_instance.index_video_frames(video_source, downloaded_file_path)
            
            print(f"Celery VisualIndex: VisualAnalyzer result for {video_source_id}: {result}")
            if result.get("error"):
                video_source.meta_visual_processing_status = 'analysis_failed'
                video_source.meta_visual_processing_error = result["error"][:500]
            else:
                video_source.meta_visual_processing_status = 'completed'
                video_source.meta_visual_processing_error = None # Clear previous errors
                video_source.last_visual_indexed_at = timezone.now() # Add this field to VideoSource
            video_source.save()

            return {"status": video_source.meta_visual_processing_status, "result": result}
            # TemporaryDirectory context manager handles cleanup of tmpdir_path

    except VideoSource.DoesNotExist:
        print(f"Celery VisualIndex: VSID {video_source_id} not found.")
        return {"status": "error_vs_not_found"}
    except Exception as e:
        import traceback
        error_full = f"UNEXPECTED error processing VSID {video_source_id}: {e}\n{traceback.format_exc()}"
        print(error_full)
        try: # Attempt to mark VideoSource as failed if possible
            vs_on_error = VideoSource.objects.get(id=video_source_id)
            vs_on_error.meta_visual_processing_status = 'error_unexpected'
            vs_on_error.meta_visual_processing_error = str(e)[:500]
            vs_on_error.save()
        except: pass # Ignore if can't update status
        # self.retry(exc=e, countdown=60*5, max_retries=2) # Retry for unexpected errors
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
