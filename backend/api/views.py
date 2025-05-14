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


class SearchResultsView(views.APIView):
    """
    Retrieves the results for a completed search task.
    Actual results will be fetched by the Celery task and associated with the SearchTask.
    This view will then query those associated results (e.g., from VideoSource or a dedicated SearchTaskResult model).
    """
    permission_classes = [AllowAny] # Or more restrictive

    def get(self, request, task_id, *args, **kwargs):
        try:
            task_id_uuid = uuid.UUID(task_id)
            search_task = get_object_or_404(SearchTask, id=task_id_uuid)

            # Similar ownership/permission check as in SearchStatusView
            is_owner = request.user.is_authenticated and search_task.user == request.user
            is_session_owner = not request.user.is_authenticated and search_task.session_id == request.session.session_key
            
            if not (is_owner or is_session_owner or search_task.user is None):
                if search_task.user or (not request.user.is_authenticated and search_task.session_id != request.session.session_key):
                    return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

            if search_task.status not in ['completed', 'partial_results']:
                return Response(
                    {"error": "Search is not yet complete.", "status": search_task.status},
                    status=status.HTTP_202_ACCEPTED # Or 400 if you prefer to indicate it's not ready
                )

            # --- Placeholder for fetching actual results ---
            # This is where you would query VideoSource or a SearchTaskResult model
            # based on how the Celery task stores the results linked to 'search_task.id'.
            # For now, let's return a dummy response.
            #
            # Example:
            # results = VideoSource.objects.filter(some_relation_to_search_task=search_task)
            # results_serializer = VideoSourceSerializer(results, many=True)
            # return Response({
            #     "task_info": SearchTaskSerializer(search_task).data,
            #     "results": results_serializer.data
            # }, status=status.HTTP_200_OK)
            # --- End Placeholder ---

            return Response({
                "message": "Results would be here.",
                "task_id": str(search_task.id),
                "status": search_task.status,
                "query": search_task.query_text or search_task.query_image_ref,
                "results_data": [] # Replace with actual results data later
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response({"error": "Invalid task_id format."}, status=status.HTTP_400_BAD_REQUEST)
        except SearchTask.DoesNotExist:
            return Response({"error": "Search task not found."}, status=status.HTTP_404_NOT_FOUND)


# --- Signup Code / Account Activation Views (from previous discussion) ---
class VerifySignupCodeView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        if not code:
            return Response({"error": "Code not provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            signup_code = SignupCode.objects.get(code=code, is_used=False)
            if signup_code.expires_at and signup_code.expires_at < timezone.now():
                return Response({"error": "Code has expired."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Valid code, return success (but don't mark as used yet)
            # You might want to include the email or plan associated if needed by frontend
            serializer = SignupCodeSerializer(signup_code)
            return Response({"message": "Code is valid.", "data": serializer.data}, status=status.HTTP_200_OK)
        except SignupCode.DoesNotExist:
            return Response({"error": "Invalid or already used code."}, status=status.HTTP_404_NOT_FOUND)

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
