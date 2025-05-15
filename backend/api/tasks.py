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
from backend.ai_agents.visual_analyzer import VisualAnalyzer
visual_analyzer_instance = VisualAnalyzer() # Instantiate once

@shared_task(bind=True, name='api.index_video_visual_features', acks_late=True, time_limit=7200, max_retries=1, default_retry_delay=60*10) # Increased time limit to 2hrs
def index_video_visual_features(self, video_source_id, force_reindex=False): # Added force_reindex
    logger.info(f"Celery VisualIndex: START for VSID {video_source_id}. Force reindex: {force_reindex}. CeleryTaskID: {self.request.id}")
    video_source = None # Ensure it's defined for the final try-except block
    try:
        video_source = VideoSource.objects.select_related('video').get(id=video_source_id)
        
        if video_source.meta_visual_processing_status == 'completed' and not force_reindex:
            logger.info(f"Celery VisualIndex: VSID {video_source_id} already completed. Skipping re-index (force_reindex=False).")
            return {"status": "skipped_already_completed", "video_source_id": video_source_id}
        if not video_source.video: # ... (handle and save status)
            logger.warning(f"Celery VisualIndex: VSID {video_source_id} not linked to Papri Video. Skipping.")
            video_source.meta_visual_processing_status = 'error_no_papri_video_link'; video_source.save(update_fields=['meta_visual_processing_status'])
            return {"status": "skipped_no_papri_video_link", "video_source_id": video_source_id}
        if not video_source.original_url: # ... (handle and save status)
            logger.warning(f"Celery VisualIndex: VSID {video_source_id} has no original_url. Skipping.")
            video_source.meta_visual_processing_status = 'error_no_original_url'; video_source.save(update_fields=['meta_visual_processing_status'])
            return {"status": "skipped_no_original_url", "video_source_id": video_source_id}

        video_url = video_source.original_url
        video_source.meta_visual_processing_status = 'downloading'
        video_source.meta_visual_processing_error = None 
        video_source.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])
        logger.info(f"Celery VisualIndex: VSID {video_source_id} status -> 'downloading' for URL: {video_url}")

        temp_download_basedir = os.path.join(settings.MEDIA_ROOT, "temp_video_downloads")
        os.makedirs(temp_download_basedir, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix=f"papri_dl_{video_source_id}_", dir=temp_download_basedir) as tmpdir_path:
            filename_base = video_source.platform_video_id if video_source.platform_video_id else str(video_source.id)
            output_template = os.path.join(tmpdir_path, f"{filename_base}.%(ext)s")
            
            # Ensure yt-dlp is available
            yt_dlp_executable = shutil.which('yt-dlp')
            if not yt_dlp_executable:
                logger.error("Celery VisualIndex: yt-dlp command not found in PATH.")
                video_source.meta_visual_processing_status = 'download_failed_ytdlp_not_found'
                video_source.meta_visual_processing_error = "yt-dlp not found"; video_source.save()
                return {"status": "failed_ytdlp_not_found", "video_source_id": video_source_id}

            ydl_opts = [ # Keep these reasonably aggressive for speed for now
                '-f', 'bestvideo[height<=480][ext=mp4][vcodec^=avc]/mp4', '--output', output_template,
                '--no-playlist', '--max-filesize', '300M', '--socket-timeout', '60', 
                '--retries', '2', '--fragment-retries', '2', '--restrict-filenames', 
                '--no-warnings', '--ignore-config', '--no-cache-dir',
                '--extractor-args', 'youtube:player_client=web;youtube:skip=hls,dash',
            ]
            logger.info(f"Celery VisualIndex: Downloading with yt-dlp command: {yt_dlp_executable} {' '.join(ydl_opts)} {video_url}")
            
            process = subprocess.run([yt_dlp_executable] + ydl_opts + [video_url], capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore', timeout=600) # 10 min download timeout

            downloaded_file_path = None
            if process.returncode == 0:
                # ... (logic to find downloaded_file_path, ensure it's robust) ...
                # (Code from Step 31 is good here)
                expected_filename_base_for_find = filename_base
                for f_name in sorted(os.listdir(tmpdir_path)):
                    if f_name.startswith(expected_filename_base_for_find) and any(f_name.endswith(ext) for ext in ['.mp4', '.mkv', '.webm']):
                        downloaded_file_path = os.path.join(tmpdir_path, f_name); break
                if not downloaded_file_path:
                     for f_name in sorted(os.listdir(tmpdir_path)): # Fallback
                        if any(f_name.endswith(ext) for ext in ['.mp4', '.mkv', '.webm']):
                            downloaded_file_path = os.path.join(tmpdir_path, f_name); break
                if downloaded_file_path and os.path.exists(downloaded_file_path) and os.path.getsize(downloaded_file_path) > 1024:
                    logger.info(f"Celery VisualIndex: Downloaded to {downloaded_file_path}. Size: {os.path.getsize(downloaded_file_path)} bytes.")
                else:
                    err_msg = f"yt-dlp success but downloaded file empty, missing or not found. Found: '{downloaded_file_path}'. stdout: {process.stdout[-200:]}"
                    logger.error(f"Celery VisualIndex: {err_msg}")
                    video_source.meta_visual_processing_status = 'download_failed_file_issue'; video_source.meta_visual_processing_error = err_msg[:500]; video_source.save()
                    return {"status": "failed_download_file_issue", "video_source_id": video_source_id}
            else: # yt-dlp failed
                error_output = f"yt-dlp failed (code {process.returncode}). Stderr: {process.stderr[-500:]}"
                logger.error(f"Celery VisualIndex: {error_output}")
                video_source.meta_visual_processing_status = 'download_failed'; video_source.meta_visual_processing_error = error_output; video_source.save()
                return {"status": "failed_download", "error": error_output, "video_source_id": video_source_id}

            video_source.meta_visual_processing_status = 'indexing'
            video_source.save(update_fields=['meta_visual_processing_status'])
            logger.info(f"Celery VisualIndex: VSID {video_source_id} status -> 'indexing'. Calling VisualAnalyzer.")

            result = visual_analyzer_instance.index_video_frames(video_source, downloaded_file_path)
            
            logger.info(f"Celery VisualIndex: VisualAnalyzer result for VSID {video_source_id}: {result}")
            if result.get("error") or result.get("indexed_frames_count", 0) == 0:
                video_source.meta_visual_processing_status = 'analysis_failed'
                video_source.meta_visual_processing_error = result.get("error", "No frames effectively indexed")[:500]
            else:
                video_source.meta_visual_processing_status = 'completed'
                video_source.meta_visual_processing_error = None
                video_source.last_visual_indexed_at = timezone.now()
            video_source.save()
            logger.info(f"Celery VisualIndex: VSID {video_source_id} final visual status '{video_source.meta_visual_processing_status}'.")
            return {"status": video_source.meta_visual_processing_status, "result": result, "video_source_id": video_source_id}

    except VideoSource.DoesNotExist: # ...
        logger.error(f"Celery VisualIndex: VSID {video_source_id} not found.")
        return {"status": "error_vs_not_found", "video_source_id": video_source_id}
    except subprocess.TimeoutExpired:
        logger.error(f"Celery VisualIndex: yt-dlp download timed out for VSID {video_source_id}.")
        if video_source: video_source.meta_visual_processing_status = 'download_timeout'; video_source.meta_visual_processing_error = "yt-dlp download timeout"; video_source.save()
        return {"status": "download_timeout", "video_source_id": video_source_id}
    except Exception as e: # ...
        import traceback; error_full = f"Celery VisualIndex: UNEXPECTED error for VSID {video_source_id}: {e}\n{traceback.format_exc()}"
        logger.error(error_full)
        if video_source:
            try:
                video_source.meta_visual_processing_status = 'error_unexpected'
                video_source.meta_visual_processing_error = str(e)[:500]
                video_source.save(update_fields=['meta_visual_processing_status', 'meta_visual_processing_error'])
            except: pass 
        raise self.retry(exc=e, countdown=60*10) # Retry once for truly unexpected issues after 10 mins

@shared_task(bind=True, name='api.process_search_query', acks_late=True, time_limit=600, max_retries=2, default_retry_delay=60)
def process_search_query(self, search_task_id):
    logger.info(f"Celery ProcessSearch: START for STID {search_task_id}. CeleryTaskID: {self.request.id}")
    search_task = None
    try:
        search_task = SearchTask.objects.get(id=search_task_id)
        if search_task.status == 'completed': # Avoid re-processing completed tasks
            logger.info(f"Celery ProcessSearch: STID {search_task_id} already completed. Skipping.")
            return {"status": "skipped_already_completed", "search_task_id": str(search_task_id)}

        search_task.status = 'processing'
        search_task.error_message = None # Clear previous errors
        search_task.save(update_fields=['status', 'error_message'])
        logger.info(f"Celery ProcessSearch: STID {search_task_id} status -> 'processing'.")

        search_parameters = {
            'query_text': search_task.query_text,
            'query_image_ref': search_task.query_image_ref,
            'applied_filters': search_task.applied_filters_json,
            'user_id': str(search_task.user_id) if search_task.user else None,
            'session_id': search_task.session_id,
        }

        orchestrator = PapriAIAgentOrchestrator(papri_search_task_id=search_task_id)
        orchestration_result = orchestrator.execute_search(search_parameters)

        logger.info(f"Celery ProcessSearch: STID {search_task_id} Orchestration Result: Fetched={orchestration_result.get('items_fetched_from_sources')}, Analyzed={orchestration_result.get('items_analyzed_for_content')}, Ranked={orchestration_result.get('ranked_video_count')}")

        if orchestration_result and orchestration_result.get("status_code", 200) < 400 and "error" not in orchestration_result : # Check for explicit error or status_code
            search_task.status = 'completed'
            ranked_ids = orchestration_result.get("persisted_video_ids_ranked", [])
            search_task.result_video_ids_json = ranked_ids
            search_task.detailed_results_info_json = orchestration_result.get("results_data_detailed")
            search_task.error_message = None # Clear any previous error message
        else:
            search_task.status = 'failed'
            error_msg = orchestration_result.get("error", "Unknown error during orchestration.")
            search_task.error_message = str(error_msg)[:1000] # Max 1000 chars
            logger.error(f"Celery ProcessSearch: STID {search_task_id} failed orchestration. Error: {error_msg}")
        
        search_task.updated_at = timezone.now()
        search_task.save(update_fields=['status', 'error_message', 'updated_at', 'result_video_ids_json', 'detailed_results_info_json'])
        logger.info(f"Celery ProcessSearch: STID {search_task_id} final status '{search_task.status}'. {len(search_task.result_video_ids_json or [])} results linked.")
        
        return {
            "status": search_task.status, "search_task_id": str(search_task_id),
            "message": orchestration_result.get("message", search_task.error_message),
            "ranked_video_count": len(search_task.result_video_ids_json or [])
        }

    except SearchTask.DoesNotExist:
        logger.error(f"Celery ProcessSearch: SearchTask ID {search_task_id} not found.")
        return {"status": "error_task_not_found", "search_task_id": str(search_task_id)}
    except Exception as e:
        logger.error(f"Celery ProcessSearch: UNEXPECTED error for STID {search_task_id}: {e}", exc_info=True)
        if search_task:
            try:
                search_task.status = 'failed'
                search_task.error_message = f"Unexpected Celery Error: {str(e)[:500]}"
                search_task.updated_at = timezone.now()
                search_task.save(update_fields=['status', 'error_message', 'updated_at'])
            except Exception as db_err:
                logger.error(f"Celery ProcessSearch: Failed to update STID {search_task_id} on error: {db_err}")
        
        # Retry for unexpected errors (e.g., temporary network issue, DB deadlock)
        # Default retry policy from @shared_task will be used if not explicitly raised with self.retry
        # To prevent retries for application errors caught here, you might 'return' instead of 'raise'
        # Or use 'raise Ignore()' from celery.exceptions to prevent retry for this specific exception.
        # For now, let it use default retry behavior.
        raise # Re-raise to let Celery handle retry based on task decorator settings
