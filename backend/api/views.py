# backend/api/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Case, When, Value, IntegerField
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone
from django.conf import settings
import uuid
import os
import logging

from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination

from .models import SearchTask, Video, VideoSource, SignupCode, User # Assuming User from django.contrib.auth.models
from .serializers import (
    SearchTaskSerializer, UserSerializer, VideoResultSerializer, 
    SignupCodeSerializer, ActivateAccountSerializer, VideoSourceResultSerializer # Added VSRS
)
# from backend.tasks import process_search_query # Assuming tasks.py is one level up from current app
# Corrected import for tasks within the same app:
from .tasks import process_search_query # Celery task for search

logger = logging.getLogger(__name__)

@login_required # Protects the main app page
def papri_app_view(request):
    return render(request, 'papriapp.html') # Renders frontend/templates/papriapp.html

class UserDetailView(generics.RetrieveAPIView): # ... (as in Step 32)
    permission_classes = [IsAuthenticated]; serializer_class = UserSerializer
    def get_object(self): return self.request.user

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_status_view(request): # ... (as in Step 32)
    if request.user.is_authenticated: return Response(UserSerializer(request.user).data)
    return Response({'is_authenticated': False})

class StandardResultsSetPagination(PageNumberPagination): # 
    page_size = getattr(settings, 'API_PAGE_SIZE', 12)
    page_size_query_param = 'page_size'
    max_page_size = getattr(settings, 'API_MAX_PAGE_SIZE', 50)

class InitiateSearchView(views.APIView): # 
    permission_classes = [AllowAny] # Or IsAuthenticated
    # parser_classes = (MultiPartParser, FormParser) # if handling image upload here (moved to Celery task)

    def post(self, request, *args, **kwargs):
        query_text = request.data.get('query_text')
        query_image_file = request.FILES.get('query_image') # For image uploads
        filters_json = request.data.get('filters', {})

        if not query_text and not query_image_file:
            return Response({"error": "Query text or image required."}, status=status.HTTP_400_BAD_REQUEST)

        image_ref_path = None
        if query_image_file:
            try:
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_query_images'); os.makedirs(temp_dir, exist_ok=True)
                ext = query_image_file.name.split('.')[-1] if '.' in query_image_file.name else 'jpg'
                temp_filename = f"queryimg_{uuid.uuid4().hex}.{ext}"
                image_ref_path = os.path.join(temp_dir, temp_filename)
                with open(image_ref_path, 'wb+') as dest:
                    for chunk in query_image_file.chunks(): dest.write(chunk)
                logger.info(f"Query image saved temporarily to: {image_ref_path}")
            except Exception as e:
                logger.error(f"Failed to save query image: {e}", exc_info=True)
                return Response({"error": "Could not process uploaded image."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key if request.session.session_key else str(uuid.uuid4()) # Ensure session_id for anon
        if not request.session.session_key: request.session.create() # Create session if none for anon

        search_task = SearchTask.objects.create(
            user=user, session_id=session_id, query_text=query_text,
            query_image_ref=image_ref_path, # Store path for Celery task to access
            applied_filters_json=filters_json, status='pending'
        )
        try:
            process_search_query.delay(search_task.id)
            logger.info(f"Dispatched Celery task process_search_query for STID: {search_task.id}")
        except Exception as e: # e.g. Celery broker not available
            logger.error(f"Failed to dispatch Celery task for STID {search_task.id}: {e}", exc_info=True)
            search_task.status = 'failed'; search_task.error_message = "Failed to initiate search processing."; search_task.save()
            return Response({"error": "Search initiation failed. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(SearchTaskSerializer(search_task).data, status=status.HTTP_202_ACCEPTED)


class SearchStatusView(views.APIView): # ... (as in Step 32, ensure permission checks)
    permission_classes = [AllowAny]
    def get(self, request, task_id, *args, **kwargs): # ... (logic to get task and check ownership) ...
        try:
            task_uuid = uuid.UUID(task_id); search_task = get_object_or_404(SearchTask, id=task_uuid)
            # Ownership check (simplified for brevity - ensure robust in your final code)
            if search_task.user and search_task.user != request.user:
                if not (request.user.is_staff or request.user.is_superuser): # Allow staff to view any
                    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            elif not search_task.user and search_task.session_id != request.session.session_key:
                 return Response({"error": "Forbidden - session mismatch for anonymous task"}, status=status.HTTP_403_FORBIDDEN)
            return Response(SearchTaskSerializer(search_task).data)
        except ValueError: return Response({"error": "Invalid task ID format"}, status.HTTP_400_BAD_REQUEST)
        except SearchTask.DoesNotExist: return Response({"error": "Task not found"}, status.HTTP_404_NOT_FOUND)


class SearchResultsView(views.APIView): # , refined in Step 37/39
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_filter_kwargs_for_videos(self, request): # Helper for Video model specific filters
        kwargs = {}
        duration_min = request.query_params.get('duration_min')
        if duration_min and duration_min.isdigit(): kwargs['duration_seconds__gte'] = int(duration_min)
        duration_max = request.query_params.get('duration_max')
        if duration_max and duration_max.isdigit(): kwargs['duration_seconds__lte'] = int(duration_max)
        
        date_after = request.query_params.get('date_after') # YYYY-MM-DD
        if date_after: pd_after = parse_date(date_after); kwargs['publication_date__gte'] = pd_after if pd_after else None
        date_before = request.query_params.get('date_before')
        if date_before: pd_before = parse_date(date_before); kwargs['publication_date__lte'] = pd_before if pd_before else None # Consider end of day for lte
        return {k:v for k,v in kwargs.items() if v is not None} # Clean None values

    def get_ordering_for_videos(self, request, has_relevance_scores):
        sort_by = request.query_params.get('sort_by', 'relevance' if has_relevance_scores else '-publication_date')
        if sort_by == 'date_asc': return ['publication_date']
        if sort_by == 'date_desc': return ['-publication_date']
        if sort_by == 'title_asc': return ['title']
        if sort_by == 'title_desc': return ['-title']
        return [] # Default to relevance (order from task.detailed_results_info_json)

    @property
    def paginator(self): # ... (as in Step 37) ...
        if not hasattr(self, '_paginator'): self._paginator = self.pagination_class() if self.pagination_class else None
        return self._paginator
    def paginate_queryset(self, queryset): # ... (as in Step 37) ...
        return self.paginator.paginate_queryset(queryset, self.request, view=self) if self.paginator else None
    def get_paginated_response(self, data): # ... (as in Step 37) ...
        return self.paginator.get_paginated_response(data)

    def get(self, request, task_id, *args, **kwargs): # , refined in Step 37/39/40
        try:
            task_uuid = uuid.UUID(task_id); search_task = get_object_or_404(SearchTask, id=task_uuid)
            # ... (Ownership/permission checks as in SearchStatusView) ...
            if search_task.status not in ['completed', 'partial_results']:
                return Response({"error": "Search not complete.", "status": search_task.status}, status.HTTP_202_ACCEPTED)

            # detailed_results_info_json contains the RANKED list of dicts from RARAgent
            # Each dict has 'video_id', 'combined_score', 'match_types', 'best_match_timestamp_ms', 'text_snippet'
            detailed_ranked_results = search_task.detailed_results_info_json or []
            
            # Fallback to result_video_ids_json if detailed_results_info_json is empty
            if not detailed_ranked_results and search_task.result_video_ids_json:
                detailed_ranked_results = [{'video_id': vid_id, 'combined_score': 0.0, 'match_types':['unknown_rank_source']} 
                                           for vid_id in search_task.result_video_ids_json]

            if not detailed_ranked_results:
                return Response(self.get_paginated_response([]) if self.paginator else {"results_data": [], "count":0, "next":None, "previous":None})


            ordered_video_ids = [item['video_id'] for item in detailed_ranked_results]
            
            # Fetch Video objects, preserving the order from RARAgent
            preserved_order_qs = Case(*[When(id=pk, then=Value(i)) for i, pk in enumerate(ordered_video_ids)], output_field=IntegerField())
            videos_queryset = Video.objects.filter(id__in=ordered_video_ids).prefetch_related(
                'sources' # For platform_name, original_url, embed_url
            ).annotate(relevance_order=preserved_order_qs).order_by('relevance_order')

            # Apply DB-level filters (duration, date) from query params
            db_filters = self.get_filter_kwargs_for_videos(request)
            if db_filters: videos_queryset = videos_queryset.filter(**db_filters)
            
            # Apply platform filter (post-DB for simplicity with pre-ranked IDs)
            platform_filter_val = request.query_params.get('platform')
            if platform_filter_val:
                videos_list_for_platform_filter = list(videos_queryset) # Evaluate queryset
                videos_queryset = [v for v in videos_list_for_platform_filter if any(s.platform_name.lower() == platform_filter_val.lower() for s in v.sources.all())]
                # Note: videos_queryset is now a list, not a queryset, if platform filter applied

            # Apply sorting if not 'relevance'
            has_relevance_scores = any(item.get('combined_score',0) > 0 for item in detailed_ranked_results)
            sort_args = self.get_ordering_for_videos(request, has_relevance_scores)
            if request.query_params.get('sort_by', 'relevance') != 'relevance' and sort_args:
                if isinstance(videos_queryset, list): # If it became a list due to platform filter
                    videos_queryset.sort(key=lambda v: tuple(getattr(v, field.lstrip('-')) if not field.startswith('-') else (not getattr(v, field.lstrip('-'))) for field in sort_args), 
                                         reverse=any(field.startswith('-') for field in sort_args)) # Basic multi-field sort for list
                else: # Still a queryset
                    videos_queryset = videos_queryset.order_by(*sort_args)
            
            # Paginate the final list/queryset
            page_items = self.paginate_queryset(list(videos_queryset)) # Ensure it's a list for consistent handling
            
            # Add scores, snippets etc. from detailed_ranked_results to the page_items
            detailed_info_map = {item['video_id']: item for item in detailed_ranked_results}
            results_for_serializer = []
            for video_obj in page_items if page_items else []:
                detail = detailed_info_map.get(video_obj.id)
                if detail:
                    video_obj.relevance_score = detail.get('combined_score', 0.0)
                    video_obj.match_types = detail.get('match_types', [])
                    video_obj.best_match_timestamp_ms = detail.get('best_match_timestamp_ms')
                    video_obj.text_snippet = detail.get('text_snippet')
                results_for_serializer.append(video_obj)
            
            serializer = VideoResultSerializer(results_for_serializer, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data) if page_items is not None else Response({"results_data": serializer.data})

        except ValueError: return Response({"error": "Invalid task ID"}, status.HTTP_400_BAD_REQUEST)
        except SearchTask.DoesNotExist: return Response({"error": "Task not found"}, status.HTTP_404_NOT_FOUND)
        except Exception as e: logger.error(f"SearchResultsView Error for task {task_id}: {e}", exc_info=True); return Response({"error": "Unexpected error fetching results."}, status.HTTP_500_INTERNAL_SERVER_ERROR)

# ... (SignupCode views as in Step 32)
