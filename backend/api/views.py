# backend/api/views.py
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings # For accessing settings like MEDIA_ROOT

from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes

# Import your models
from .models import SearchTask, VideoSource, SignupCode # Add other models as needed

# Import your serializers (we'll create these next)
from .serializers import (
    SearchTaskSerializer,
    UserSerializer, # For user details
    # VideoSourceSerializer, # If you need to serialize video results directly
    SignupCodeSerializer,
    ActivateAccountSerializer
)

# Import Celery tasks (we'll create this file soon)
# from backend.tasks import process_search_query # Assuming tasks.py is in 'backend' app or project root

import uuid
import os # For handling file paths if image uploads are stored temporarily

# --- User Authentication Views (Placeholders/Basic) ---
class UserDetailView(generics.RetrieveAPIView):
    """
    Provides the details of the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

@api_view(['GET'])
@permission_classes([AllowAny]) # Or IsAuthenticated if you only want logged-in users to see this
def auth_status_view(request):
    """
    Checks if the user is authenticated and returns user info if they are.
    Useful for frontend to determine auth state.
    """
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    return Response({'is_authenticated': False}, status=status.HTTP_200_OK)


# --- Search Task Views ---
class InitiateSearchView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        query_text = request.data.get('query_text')
        query_image = request.FILES.get('query_image')
        filters_json = request.data.get('filters', {})

        if not query_text and not query_image:
            return Response(
                {"error": "Either 'query_text' or 'query_image' must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_ref = None
        if query_image:
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_query_images')
            os.makedirs(temp_dir, exist_ok=True)
            ext = query_image.name.split('.')[-1] if '.' in query_image.name else 'tmp'
            unique_filename = f"{uuid.uuid4()}.{ext}"
            image_path = os.path.join(temp_dir, unique_filename)
            try:
                with open(image_path, 'wb+') as destination:
                    for chunk in query_image.chunks():
                        destination.write(chunk)
                image_ref = image_path
            except Exception as e:
                # Log the error
                print(f"Error saving query image: {str(e)}")
                return Response({"error": f"Could not save query image."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key
        if not session_id and not user:
            request.session.save()
            session_id = request.session.session_key

        search_task = SearchTask.objects.create(
            user=user,
            session_id=session_id,
            query_text=query_text,
            query_image_ref=image_ref,
            applied_filters_json=filters_json,
            status='pending' # Initial status
        )

        # ---- TRIGGER CELERY TASK ----
        try:
            # Send the task to Celery. Pass the search_task_id.
            process_search_query.delay(search_task.id)
            print(f"Celery task process_search_query dispatched for SearchTask ID: {search_task.id}")
        except Exception as e:
            # Handle case where Celery might not be available (e.g., broker down)
            # Log this critical error
            print(f"CRITICAL: Failed to dispatch Celery task for SearchTask ID {search_task.id}: {e}")
            search_task.status = 'failed'
            search_task.error_message = "Failed to initiate search processing."
            search_task.save()
            # Return an error to the user
            return Response(
                {"error": "There was an issue initiating your search. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # ----------------------------

        serializer = SearchTaskSerializer(search_task)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
class SearchStatusView(views.APIView):
    """
    Retrieves the status and basic details of a specific search task.
    """
    permission_classes = [AllowAny] # Or more restrictive if needed

    def get(self, request, task_id, *args, **kwargs):
        try:
            task_id_uuid = uuid.UUID(task_id) # Ensure task_id is a valid UUID
            search_task = get_object_or_404(SearchTask, id=task_id_uuid)
            
            # Security check: Ensure the user requesting status is either the owner or it's an anonymous task
            # This logic might need refinement based on your exact auth requirements for viewing tasks
            is_owner = request.user.is_authenticated and search_task.user == request.user
            is_session_owner = not request.user.is_authenticated and search_task.session_id == request.session.session_key
            
            if not (is_owner or is_session_owner or search_task.user is None): # Allow if task is fully anonymous (no user, relies on session)
                 # If the task has a user and the current request user doesn't match, AND
                 # if the task has a session_id and the current request session doesn't match (or user is auth'd but it's not their task)
                if search_task.user or (not request.user.is_authenticated and search_task.session_id != request.session.session_key):
                    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

            serializer = SearchTaskSerializer(search_task)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "Invalid task_id format."}, status=status.HTTP_400_BAD_REQUEST)
        except SearchTask.DoesNotExist: # Handled by get_object_or_404 but explicit for clarity
            return Response({"error": "Search task not found."}, status=status.HTTP_404_NOT_FOUND)


class StandardResultsSetPagination(PageNumberPagination): # Optional: Custom pagination class
    page_size = 12 # Default for this view
    page_size_query_param = 'page_size'
    max_page_size = 50

class SearchResultsView(views.APIView):
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination # Use custom or DRF default

    def get_filter_kwargs(self, request):
        """Helper to parse filter query parameters."""
        kwargs = {}
        platform = request.query_params.get('platform')
        if platform:
            # Assuming VideoSource platform_name stores 'YouTube', 'Vimeo', 'PeerTube_tilvids.com' etc.
            # We need to filter on Video objects that have at least one source matching this platform.
            # This becomes a subquery or an exists clause.
            # For simplicity now, we might filter on VideoSource directly if RARAgent passes VideoSource IDs,
            # or filter Video objects that have any source matching.
            # This filter is best applied AFTER RARAgent's ranking if rank depends on all sources.
            # Let's assume for now RARAgent does its ranking, and we filter the *ranked Video IDs*.
            # This means the filter logic needs to be in RARAgent or applied to the video_ids list.
            # For a simpler DB-level filter on Video:
            # kwargs['sources__platform_name__iexact'] = platform 
            # This will be passed to the Video.objects.filter()
            # However, our primary list comes from search_task.result_video_ids_json.
            # So, filtering will be on this list of Video objects.
            pass # We'll handle platform filtering after fetching videos by ID

        duration_min_sec = request.query_params.get('duration_min')
        duration_max_sec = request.query_params.get('duration_max')
        if duration_min_sec and duration_min_sec.isdigit():
            kwargs['duration_seconds__gte'] = int(duration_min_sec)
        if duration_max_sec and duration_max_sec.isdigit():
            kwargs['duration_seconds__lte'] = int(duration_max_sec)
        
        date_after_str = request.query_params.get('date_after') # Expected YYYY-MM-DD
        if date_after_str:
            parsed_date_after = parse_date(date_after_str)
            if parsed_date_after:
                kwargs['publication_date__gte'] = parsed_date_after
        
        date_before_str = request.query_params.get('date_before') # Expected YYYY-MM-DD
        if date_before_str:
            parsed_date_before = parse_date(date_before_str)
            if parsed_date_before:
                # To include the date_before itself, you might want to go to end of day or next day
                from datetime import timedelta
                kwargs['publication_date__lte'] = parsed_date_before + timedelta(days=1)


        # Language filter (if transcripts are involved and language is stored on Video or VideoSource)
        lang = request.query_params.get('lang')
        if lang:
            kwargs['sources__transcripts__language_code__iexact'] = lang # Example

        return kwargs

    def get_ordering_args(self, request, has_combined_scores):
        """Helper to parse sort query parameter."""
        sort_by = request.query_params.get('sort_by', 'relevance' if has_combined_scores else 'publication_date') # Default sort
        
        if sort_by == 'date_asc':
            return ['publication_date']
        elif sort_by == 'date_desc' or sort_by == 'publication_date': # Default if no relevance
            return ['-publication_date']
        elif sort_by == 'title_asc':
            return ['title']
        elif sort_by == 'title_desc':
            return ['-title']
        # 'relevance' is handled by the order from search_task.result_video_ids_json or detailed_results_info_json
        return [] # Default to relevance (order from task)


    @property # Make paginator an instance property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)


    def get(self, request, task_id, *args, **kwargs):
        try:
            task_id_uuid = uuid.UUID(task_id)
            search_task = get_object_or_404(SearchTask.objects.prefetch_related('user'), id=task_id_uuid) # Prefetch user
            
            # ... (permission checks as before) ...
            is_owner = request.user.is_authenticated and search_task.user == request.user
            is_session_owner = not request.user.is_authenticated and search_task.session_id == request.session.session_key
            if not (is_owner or is_session_owner or (search_task.user is None and search_task.session_id is None)): # Allow if task is truly anonymous
                 if search_task.user or (not request.user.is_authenticated and search_task.session_id != request.session.session_key):
                     return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


            if search_task.status not in ['completed', 'partial_results']:
                return Response({"error": "Search not complete.", "status": search_task.status}, status=status.HTTP_202_ACCEPTED)

            # --- Get Ranked IDs and Detailed Info from SearchTask ---
            # detailed_results_info contains [{'video_id': X, 'combined_score': Y, 'match_types': [], 'best_match_timestamp_ms': Z}, ...]
            # It's already ranked by RARAgent.
            detailed_results_list = search_task.detailed_results_info_json or []
            
            # Fallback if detailed_results_info_json is empty but result_video_ids_json has IDs
            if not detailed_results_list and search_task.result_video_ids_json:
                detailed_results_list = [{'video_id': vid_id, 'combined_score': 0.0, 'match_types':['unknown']} 
                                         for vid_id in search_task.result_video_ids_json]

            if not detailed_results_list:
                return Response({"results_data": [], "count":0, "next":None, "previous":None}, status=status.HTTP_200_OK)

            # Extract video_ids in the ranked order
            ordered_video_ids = [item['video_id'] for item in detailed_results_list]
            
            # --- Fetch Video objects from DB based on these IDs ---
            # We need to preserve the order from detailed_results_list.
            # Using Case/When for ordering by a list of IDs.
            preserved_order = Case(*[When(id=pk, then=Value(i)) for i, pk in enumerate(ordered_video_ids)], output_field=IntegerField())
            
            videos_queryset = Video.objects.filter(id__in=ordered_video_ids).prefetch_related(
                'sources', # For platform_name, original_url
                # 'sources__transcripts__keywords' # If showing keywords on cards
            ).annotate(custom_order=preserved_order).order_by('custom_order')


            # --- Apply DB-Level Filters (Duration, Publication Date) ---
            filter_kwargs_db = self.get_filter_kwargs(request)
            if filter_kwargs_db:
                videos_queryset = videos_queryset.filter(**filter_kwargs_db)
            
            # --- Apply Sorting (if not relevance) ---
            # If sorting is by relevance, the order from 'ordered_video_ids' (from RARAgent) is primary.
            # If sorting by other fields, we apply it now.
            # Note: if we sort by something other than relevance, the RARAgent's complex ranking is overridden.
            # This is a choice: either RARAgent provides THE definitive order, or API allows overriding.
            # For V1, let's say if sort_by is not 'relevance', we re-sort.
            
            # Check if detailed_results_list has meaningful scores
            has_combined_scores = any(item.get('combined_score', 0) > 0 for item in detailed_results_list)
            ordering_args = self.get_ordering_args(request, has_combined_scores)
            
            requested_sort = request.query_params.get('sort_by', 'relevance')
            if requested_sort != 'relevance' and ordering_args:
                videos_queryset = videos_queryset.order_by(*ordering_args)
            # Else, the 'custom_order' based on RARAgent's ranking is maintained.

            # --- Platform Filtering (Post-DB Fetch, as it involves sources) ---
            # This is less efficient than a DB filter but simpler if RARAgent provides the master list.
            platform_filter_value = request.query_params.get('platform')
            if platform_filter_value:
                filtered_videos_by_platform = []
                for video in videos_queryset: # This queryset is already ordered
                    if any(source.platform_name.lower() == platform_filter_value.lower() for source in video.sources.all()):
                        filtered_videos_by_platform.append(video)
                # The queryset is now a list, pagination will work on this list.
                videos_to_paginate = filtered_videos_by_platform
            else:
                videos_to_paginate = list(videos_queryset) # Convert queryset to list for pagination if not already

            # --- Paginate the (filtered and sorted) list of Video objects ---
            page = self.paginate_queryset(videos_to_paginate)

            # --- Add detailed scores and match types to video objects before serialization ---
            if page is not None:
                results_on_page = list(page) # Get items for the current page
            else: # No pagination
                results_on_page = list(videos_to_paginate)

            # Create a map for quick lookup of detailed info
            detailed_info_map = {item['video_id']: item for item in detailed_results_list}

            for video in results_on_page:
                detail = detailed_info_map.get(video.id)
                if detail:
                    video.relevance_score = detail.get('combined_score', 0.0)
                    video.match_types = detail.get('match_types', [])
                    video.best_match_timestamp_ms = detail.get('best_match_timestamp_ms')
                else: # Should not happen if detailed_results_list was the source of IDs
                    video.relevance_score = 0.0
                    video.match_types = ['unknown_source_of_rank']
                    video.best_match_timestamp_ms = None
            
            serializer = VideoResultSerializer(results_on_page, many=True, context={'request': request})
            
            if page is not None:
                return self.get_paginated_response(serializer.data)
            else: # No pagination
                return Response({ # Mimic paginated structure if needed by frontend
                    "count": len(serializer.data), "next": None, "previous": None,
                    "results_data": serializer.data 
                }, status=status.HTTP_200_OK)

        except ValueError: # For invalid UUID
            return Response({"error": "Invalid task_id format."}, status=status.HTTP_400_BAD_REQUEST)
        except SearchTask.DoesNotExist:
            return Response({"error": "Search task not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"SearchResultsView Error for task {task_id}: {e}", exc_info=True)
            return Response({"error": "An unexpected error occurred while fetching results."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ActivateAccountWithCodeView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ActivateAccountSerializer(data=request.data)
        if serializer.is_valid():
            code_text = serializer.validated_data['code']
            email = serializer.validated_data['email'] # This should match the code's email
            password = serializer.validated_data['password']
            # Optional: first_name, last_name from serializer.validated_data

            try:
                signup_code = SignupCode.objects.get(code=code_text, email__iexact=email, is_used=False)

                if signup_code.expires_at and signup_code.expires_at < timezone.now():
                    return Response({"error": "Signup code has expired."}, status=status.HTTP_400_BAD_REQUEST)

                if User.objects.filter(email__iexact=email).exists():
                    return Response({"error": "An account with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

                # Create user
                user = User.objects.create_user(
                    username=email, # Using email as username for simplicity with allauth
                    email=email,
                    password=password,
                    first_name=serializer.validated_data.get('first_name', ''),
                    last_name=serializer.validated_data.get('last_name', '')
                )
                user.is_active = True # Activate the user
                user.save()

                # Mark code as used
                signup_code.is_used = True
                signup_code.user_activated = user
                signup_code.save()
                
                # Optionally log the user in immediately (django.contrib.auth.login)
                # Or return a success message for the frontend to handle login flow

                return Response({
                    "message": "Account activated successfully. You can now log in.",
                    "user": UserSerializer(user).data # Return basic user info
                }, status=status.HTTP_201_CREATED)

            except SignupCode.DoesNotExist:
                return Response({"error": "Invalid signup code or email mismatch for the code."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e: # Catch other potential errors
                return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.shortcuts import render
from django.contrib.auth.decorators import login_required # To protect the app page

@login_required # Ensure user is logged in to access the app
def papri_app_view(request):
    return render(request, 'papriapp.html') # Assumes papriapp.html is in templates/
