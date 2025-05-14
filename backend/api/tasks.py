# backend/api/tasks.py

from celery import shared_task
from django.utils import timezone
import time # For simulating work

# Import your models
from .models import SearchTask #, Video, VideoSource, Transcript, etc. - import as needed by the task

# Import the AI Agent Orchestrator (to be created later)
# from backend.ai_agents.main_orchestrator import PapriAIAgentOrchestrator # Assuming orchestrator is in backend/ai_agents

@shared_task(bind=True, name='api.process_search_query')
def process_search_query(self, search_task_id):
    # ... (try block, fetching search_task, preparing search_parameters as before) ...
    try:
        search_task = SearchTask.objects.get(id=search_task_id)
        search_task.status = 'processing'
        search_task.save(update_fields=['status'])
        # ... (search_parameters prep) ...

        orchestrator = PapriAIAgentOrchestrator(papri_search_task_id=search_task_id)
        orchestration_result = orchestrator.execute_search(search_parameters) # Returns dict

        print(f"SearchTask {search_task_id}: Orchestration result: ItemsFetched={orchestration_result.get('items_fetched_from_sources')}, ItemsAnalyzed={orchestration_result.get('items_analyzed_for_content')}, RankedCount={orchestration_result.get('ranked_video_count')}")

        if orchestration_result and "error" not in orchestration_result:
            search_task.status = 'completed'
            # Get the list of ranked video IDs
            ranked_ids = orchestration_result.get("persisted_video_ids_ranked", []) # This key was from Orchestrator
            search_task.result_video_ids_json = ranked_ids 
            
            # Optionally store more detailed results if SearchTask model is extended
            # search_task.detailed_results_json = orchestration_result.get("results_with_scores") 
        else:
            search_task.status = 'failed'
            search_task.error_message = orchestration_result.get("error", "Unknown error during orchestration.")
        
        search_task.updated_at = timezone.now()
        search_task.save(update_fields=['status', 'error_message', 'updated_at', 'result_video_ids_json'])
        print(f"SearchTask {search_task_id}: Final status '{search_task.status}'. {len(search_task.result_video_ids_json or [])} results linked.")
        
        return {
            "status": search_task.status,
            "search_task_id": str(search_task_id),
            "message": orchestration_result.get("message", search_task.error_message),
            "ranked_video_count": len(search_task.result_video_ids_json or [])
        }

    except SearchTask.DoesNotExist:
        print(f"Error: SearchTask with ID {search_task_id} not found.")
        # self.update_state(state='FAILURE', meta={'exc': 'SearchTask.DoesNotExist'}) # Optionally update Celery task state
        return {"status": "failed", "search_task_id": str(search_task_id), "error": "Search task not found."}
    except Exception as e:
        print(f"Error processing SearchTask {search_task_id}: {e}")
        # Attempt to update the SearchTask object in the DB with the error
        try:
            search_task_on_error = SearchTask.objects.get(id=search_task_id)
            search_task_on_error.status = 'failed'
            search_task_on_error.error_message = str(e)[:1000] # Truncate if necessary
            search_task_on_error.updated_at = timezone.now()
            search_task_on_error.save(update_fields=['status', 'error_message', 'updated_at'])
        except SearchTask.DoesNotExist:
            pass # Task was not found initially
        except Exception as db_error: # Catch error during DB update
             print(f"Could not update SearchTask {search_task_id} with error state: {db_error}")

        # self.update_state(state='FAILURE', meta={'exc': type(e).__name__, 'exc_message': str(e)}) # Update Celery task state
        # To prevent Celery from retrying indefinitely for app-level errors unless specifically configured:
        # raise Ignore()
        return {"status": "failed", "search_task_id": str(search_task_id), "error": str(e)}
