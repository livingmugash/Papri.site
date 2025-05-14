# backend/api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SearchTask, Video, VideoSource, Transcript, ExtractedKeyword, VideoTopic, VideoFrameFeature, SignupCode

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        # Make email read-only if it's managed by social auth primarily after creation
        # read_only_fields = ['email']

class SignupCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for the SignupCode model.
    """
    class Meta:
        model = SignupCode
        fields = ['email', 'code', 'plan_name', 'is_used', 'created_at', 'expires_at']
        read_only_fields = ['email', 'plan_name', 'is_used', 'created_at', 'expires_at'] # Code is typically input only for verification

class ActivateAccountSerializer(serializers.Serializer):
    """
    Serializer for validating account activation data.
    """
    code = serializers.CharField(max_length=10, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    # password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}) # If you want confirm password field
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    # def validate(self, data):
    #     if data['password'] != data['password_confirm']:
    #         raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
    #     return data

class SearchTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for the SearchTask model.
    """
    user = UserSerializer(read_only=True) # Display user details, not just ID
    # query_image = serializers.ImageField(write_only=True, required=False) # Handled in view for saving

    class Meta:
        model = SearchTask
        fields = [
            'id',
            'user',
            'session_id',
            'query_text',
            'query_image_ref', # This will show the reference (e.g., path/key)
            # 'query_image', # Only for input if handling file upload via serializer
            'query_image_fingerprint',
            'applied_filters_json',
            'status',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'session_id',
            'query_image_ref',
            'query_image_fingerprint',
            'status',
            'error_message',
            'created_at',
            'updated_at',
        ]

# --- Serializers for Video Search Results ---
# These are example serializers for how you might structure the actual video results.
# You'll likely customize these based on what the AI agents produce and what the frontend needs.

class ExtractedKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedKeyword
        fields = ['keyword_text', 'relevance_score']

class VideoTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoTopic
        fields = ['topic_label', 'topic_relevance_score']

class TranscriptSerializer(serializers.ModelSerializer):
    keywords = ExtractedKeywordSerializer(many=True, read_only=True)
    topics = VideoTopicSerializer(many=True, read_only=True)

    class Meta:
        model = Transcript
        fields = [
            'language_code',
            'transcript_text_content', # Could be very long, consider omitting from list views
            'transcript_timed_json',
            'quality_score',
            'keywords',
            'topics'
        ]

class VideoFrameFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoFrameFeature
        fields = [
            'timestamp_in_video_ms',
            'frame_image_url',
            'feature_type',
            'hash_value',
            'feature_data_json',
            'vector_db_id'
        ]

class VideoSourceResultSerializer(serializers.ModelSerializer):
    """
    Serializer for VideoSource when returning search results.
    May include snippets of transcripts or relevant frame features.
    """
    # transcript_snippet = serializers.CharField(read_only=True, required=False) # Example, would be added by AI agent
    # matched_frame = VideoFrameFeatureSerializer(read_only=True, required=False) # Example

    # If you want to include full transcript data for matched sources:
    # transcripts = TranscriptSerializer(many=True, read_only=True)

    class Meta:
        model = VideoSource
        fields = [
            'id',
            'platform_name',
            'platform_video_id',
            'original_url',
            'embed_url',
            'last_scraped_at',
            # 'transcript_snippet', # Add if you generate snippets
            # 'matched_frame',      # Add if you return specific matched frames
            # 'transcripts',
        ]

class VideoResultSerializer(serializers.ModelSerializer):
    """
    Serializer for the main Video model when returning search results.
    This would typically include the best matching VideoSource(s).
    """
    sources = VideoSourceResultSerializer(many=True, read_only=True)
    # For search, you might want to add a relevance score or other search-specific fields
    # relevance_score = serializers.FloatField(read_only=True, required=False)
    # matched_snippet = serializers.CharField(read_only=True, required=False) # Text snippet that matched

    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'duration_seconds',
            'publication_date',
            'primary_thumbnail_url',
            'sources', # This will list associated VideoSource objects
            'relevance_score',
            'matched_snippet',
            'created_at'
        ]



class SearchResultsView(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request, task_id, *args, **kwargs):
        # ... (try, task_id_uuid, search_task, permission checks as before) ...
        try:
            task_id_uuid = uuid.UUID(task_id)
            search_task = get_object_or_404(SearchTask, id=task_id_uuid)
            # ... permission checks ...

            if search_task.status not in ['completed', 'partial_results']:
                return Response({"error": "Search not complete.", "status": search_task.status}, status=status.HTTP_202_ACCEPTED)

            video_ids_ordered = search_task.result_video_ids_json
            if not video_ids_ordered:
                return Response({"results_data": []}, status=status.HTTP_200_OK) # Return empty list if no IDs

            # Fetch videos and preserve order
            videos_queryset = Video.objects.filter(id__in=video_ids_ordered).prefetch_related(
                'sources', 
                # If you need keywords/transcripts directly on result cards, prefetch them too:
                # 'sources__transcripts__keywords' 
            )
            videos_dict = {video.id: video for video in videos_queryset}
            ordered_videos_with_data = []

            # If you stored results_with_scores from the orchestrator in SearchTask (e.g., as another JSONField)
            # you could retrieve it here to add scores to the serialized output.
            # For now, we'll assume scores aren't directly passed, but order is preserved.
            
            for vid_id in video_ids_ordered:
                video = videos_dict.get(vid_id)
                if video:
                    # You could try to find the score if 'results_with_scores' was stored on SearchTask
                    # For this example, we'll skip adding the score to the Video object directly for serialization
                    # and rely on the frontend to just display in the received order.
                    # If you had scores: video.relevance_score = found_score 
                    ordered_videos_with_data.append(video)
            
            results_serializer = VideoResultSerializer(ordered_videos_with_data, many=True)
            return Response({
                "message": "Results fetched successfully.", "task_id": str(search_task.id),
                "status": search_task.status, "query": search_task.query_text or search_task.query_image_ref,
                "results_data": results_serializer.data
            }, status=status.HTTP_200_OK)

