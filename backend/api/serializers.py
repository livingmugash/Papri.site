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
    sources = VideoSourceResultSerializer(many=True, read_only=True)
    relevance_score = serializers.FloatField(read_only=True, required=False)
    match_types = serializers.ListField(child=serializers.CharField(), read_only=True, required=False)
    best_match_timestamp_ms = serializers.IntegerField(read_only=True, required=False, allow_null=True) # NEW

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
            'match_types', 
            'best_match_timestamp_ms',
            'text_snippet', # NEW
            'created_at'
        ]

# backend/api/views.py
class SearchResultsView(views.APIView):
    # ... (permission_classes, get method signature) ...
    def get(self, request, task_id, *args, **kwargs):
        # ... (try, task_id_uuid, search_task, permission checks) ...
        try:
            task_id_uuid = uuid.UUID(task_id)
            search_task = get_object_or_404(SearchTask, id=task_id_uuid)
            # ... permission checks ...

            if search_task.status not in ['completed', 'partial_results']: # ...
                return Response({"error": "Search not complete."}, status=status.HTTP_202_ACCEPTED)

            video_ids_ordered = search_task.result_video_ids_json # This is the primary order
            if not video_ids_ordered: return Response({"results_data": []}, status=status.HTTP_200_OK)

            videos_queryset = Video.objects.filter(id__in=video_ids_ordered).prefetch_related('sources')
            videos_dict = {video.id: video for video in videos_queryset}
            
            # Try to get detailed scores if stored (assuming you added detailed_ranking_info_json to SearchTask)
            # detailed_scores_map = {}
            # if hasattr(search_task, 'detailed_ranking_info_json') and search_task.detailed_ranking_info_json:
            #     for item in search_task.detailed_ranking_info_json: # This was 'results_data_detailed' from orchestrator
            #         detailed_scores_map[item['video_id']] = {
            #             'combined_score': item['combined_score'],
            #             'match_types': item.get('match_types', [])
            #         }
            
            ordered_videos_with_extra_data = []
            for vid_id in video_ids_ordered:
                video = videos_dict.get(vid_id)
                if video:
                    # Add score and match_types to the video object before serialization
                    # score_info = detailed_scores_map.get(vid_id)
                    # video.relevance_score = score_info['combined_score'] if score_info else 0.0
                    # video.match_types = score_info['match_types'] if score_info else []
                    # For now, without storing detailed_ranking_info_json on SearchTask directly, these will be empty:
                    video.relevance_score = 0.0 # Placeholder
                    video.match_types = []      # Placeholder
                    ordered_videos_with_extra_data.append(video)
            
            results_serializer = VideoResultSerializer(ordered_videos_with_extra_data, many=True)
            # ... (return Response with results_serializer.data)
            return Response({
                "message": "Results fetched.", "task_id": str(search_task.id),
                "status": search_task.status, "query": search_task.query_text or search_task.query_image_ref,
                "results_data": results_serializer.data
            }, status=status.HTTP_200_OK)
