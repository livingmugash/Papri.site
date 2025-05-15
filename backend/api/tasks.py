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

@shared_task(bind=True, name='api.index_video_visual_features', acks_late=True, time_limit=3600, max_retries=1, default_retry_delay=60*5) # Increased time limit to 1hr, added retry delay
def index_video_visual_features(self, video_source_id):
    # ... (VideoSource fetching and initial checks as in Step 31) ...
    try:
        video_source = VideoSource.objects.select_related('video').get(id=video_source_id)
        if not video_source.video: # ...
            video_source.meta_visual_processing_status = 'error_no_papri_video_link'
            video_source.save(update_fields=['meta_visual_processing_status'])
            return {"status": "skipped", "reason": "Not linked to Papri Video"}
        if not video_source.original_url: # ...
            video_source.meta_visual_processing_status = 'error_no_original_url'
            video_source.save(update_fields=['meta_visual_processing_status'])
            return {"status": "skipped", "reason": "No original_url"}

        video_url = video_source.original_url
        video_source.meta_visual_processing_status = 'downloading'
        video_source.meta_visual_processing_error = None # Clear previous errors
        video_source.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])

        # ... (temp_download_basedir setup) ...
        temp_download_basedir = os.path.join(settings.MEDIA_ROOT, "temp_video_downloads") # Ensure this exists and is writable
        os.makedirs(temp_download_basedir, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix=f"papri_dl_{video_source_id}_", dir=temp_download_basedir) as tmpdir_path:
            # ... (output_template and ydl_opts as in Step 31, ensure robust output filename handling) ...
            # Using platform_video_id in filename template for better predictability
            filename_base = video_source.platform_video_id if video_source.platform_video_id else str(video_source.id)
            output_template = os.path.join(tmpdir_path, f"{filename_base}.%(ext)s")
            
            ydl_opts = [ # Example, tune as needed
                '-f', 'bestvideo[height<=480][ext=mp4][vcodec^=avc]/mp4', # Prefer h264 for wider compatibility with OpenCV
                '--output', output_template,
                '--no-playlist', '--max-filesize', '300M',
                '--socket-timeout', '60', '--retries', '2', '--fragment-retries', '2',
                '--restrict-filenames', '--no-warnings', '--ignore-config', '--no-cache-dir',
                '--extractor-args', 'youtube:player_client=web;youtube:skip=hls,dash',
            ]
            # ... (subprocess.run for yt-dlp) ...
            process = subprocess.run(['yt-dlp'] + ydl_opts + [video_url], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
            
            downloaded_file_path = None
            if process.returncode == 0:
                # ... (logic to find downloaded_file_path, refined to use expected_filename_base) ...
                expected_filename_base_for_find = filename_base # The platform_video_id or source.id
                for f_name in sorted(os.listdir(tmpdir_path)):
                    if f_name.startswith(expected_filename_base_for_find) and any(f_name.endswith(ext) for ext in ['.mp4', '.mkv', '.webm']):
                        downloaded_file_path = os.path.join(tmpdir_path, f_name)
                        break
                if not downloaded_file_path: # Fallback
                     for f_name in sorted(os.listdir(tmpdir_path)):
                        if any(f_name.endswith(ext) for ext in ['.mp4', '.mkv', '.webm']):
                            downloaded_file_path = os.path.join(tmpdir_path, f_name); break
                # ... (error if file not found) ...
                if not downloaded_file_path:
                    video_source.meta_visual_processing_status = 'download_failed_file_not_found'
                    video_source.meta_visual_processing_error = f"yt-dlp success but file not found. stdout: {process.stdout[-200:]}"
                    video_source.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])
                    return {"status": "failed_download_file_missing"}
            else: # yt-dlp failed
                # ... (error handling, save status to video_source) ...
                error_output = f"yt-dlp failed (code {process.returncode}). Stderr: {process.stderr[-500:]}"
                video_source.meta_visual_processing_status = 'download_failed'
                video_source.meta_visual_processing_error = error_output
                video_source.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])
                return {"status": "failed_download", "error": error_output}

            video_source.meta_visual_processing_status = 'indexing' # Mark as indexing
            video_source.save(update_fields=['meta_visual_processing_status'])

            # Call VisualAnalyzer using the shared instance
            result = visual_analyzer_instance.index_video_frames(video_source, downloaded_file_path)
            
            if result.get("error") or result.get("indexed_frames_count", 0) == 0:
                video_source.meta_visual_processing_status = 'analysis_failed'
                video_source.meta_visual_processing_error = result.get("error", "No frames indexed")[:500]
            else:
                video_source.meta_visual_processing_status = 'completed'
                video_source.meta_visual_processing_error = None
                video_source.last_visual_indexed_at = timezone.now()
            video_source.save() # Save final status

            return {"status": video_source.meta_visual_processing_status, "result": result}

    # ... (except VideoSource.DoesNotExist and general Exception blocks) ...
    except VideoSource.DoesNotExist:
        print(f"Celery VisualIndex: VSID {video_source_id} not found.")
        return {"status": "error_vs_not_found"}
    except Exception as e:
        # ... (Log full traceback, attempt to update VideoSource status to error_unexpected)
        import traceback; error_full = f"UNEXPECTED error VSID {video_source_id}: {e}\n{traceback.format_exc()}"
        print(error_full)
        try:
            vs_on_error = VideoSource.objects.get(id=video_source_id)
            vs_on_error.meta_visual_processing_status = 'error_unexpected'
            vs_on_error.meta_visual_processing_error = str(e)[:500]
            vs_on_error.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])
        except: pass
        # self.retry(exc=e, countdown=60*10, max_retries=1) # Retry once for truly unexpected issues
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
