# backend/api/models.py
from django.db import models
from django.contrib.auth.models import User # Using Django's built-in User model
from django.utils import timezone # For publication_date default
import uuid

# --- Core Video and Source Models ---
class Video(models.Model):
    """
    Represents a unique video entity identified by Papri, potentially existing on multiple platforms.
    """
    id = models.BigAutoField(primary_key=True)
    title = models.TextField(help_text="Title of the video.")
    description = models.TextField(null=True, blank=True, help_text="Description of the video.")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds.")
    publication_date = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Original publication date.")
    primary_thumbnail_url = models.URLField(max_length=2048, null=True, blank=True, help_text="URL of the primary thumbnail.")
    # A content-based hash for high-level deduplication across different source URLs.
    # Could be a hash of normalized title + duration, or a perceptual hash of a keyframe.
    deduplication_hash = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text="Hash for deduplication purposes.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Video {self.id}"

    class Meta:
        indexes = [
            # Django automatically creates B-tree indexes on ForeignKey fields and primary keys.
            # For TextField, consider using full-text search capabilities of your database (e.g., MySQL FULLTEXT)
            # which you'd typically add manually in a migration or use a third-party Django package.
            # Example (manual SQL for MySQL full-text index on title and description):
            # migrations.RunSQL("ALTER TABLE api_video ADD FULLTEXT(title, description);")
            models.Index(fields=['title'], name='api_video_title_idx'), # For simple LIKE queries or if DB creates prefix indexes
            models.Index(fields=['created_at'], name='api_video_created_at_idx'),
        ]

class VideoSource(models.Model):
    """
    Represents a specific instance of a Video on a particular platform (e.g., a YouTube URL for a Video).
    """
    id = models.BigAutoField(primary_key=True)
    video = models.ForeignKey(Video, related_name='sources', on_delete=models.CASCADE, db_index=True, help_text="The canonical Papri Video entry.")
    platform_name = models.CharField(max_length=100, db_index=True, help_text="Name of the platform, e.g., YouTube, Vimeo.")
    platform_video_id = models.CharField(max_length=255, db_index=True, help_text="Video's unique ID on the source platform.")
    original_url = models.URLField(max_length=2048, unique=True, help_text="Direct URL to the video on the source platform.")
    embed_url = models.URLField(max_length=2048, null=True, blank=True, help_text="URL for embedding the video.")
    # Stores the raw metadata JSON fetched from the source API or webpage.
    # Allows for future re-processing or accessing platform-specific fields not in our main schema.
    source_metadata_json = models.JSONField(null=True, blank=True, help_text="Raw metadata from the source platform.")
    last_scraped_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of the last successful scrape/API fetch.")
    is_primary_source = models.BooleanField(default=False, help_text="Is this considered the canonical source for this video?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    VISUAL_PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending Download/Index'),
        ('downloading', 'Downloading'),
        ('download_failed', 'Download Failed'),
        ('indexing', 'Indexing Frames'), # Could be set by VisualAnalyzer itself
        ('analysis_failed', 'Frame Analysis Failed'),
        ('error_unexpected', 'Unexpected Error'),
        ('completed', 'Visual Indexing Completed'),
        ('not_applicable', 'Not Applicable (e.g., audio only)'),
    ]
    meta_visual_processing_status = models.CharField(
        max_length=20, 
        choices=VISUAL_PROCESSING_STATUS_CHOICES, 
        default='pending', 
        null=True, blank=True, db_index=True
    )
    meta_visual_processing_error = models.TextField(null=True, blank=True)
    last_visual_indexed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('platform_name', 'platform_video_id') # A video ID is unique per platform
        indexes = [
            models.Index(fields=['last_scraped_at'], name='api_videosource_scraped_idx'),
        ]

    def __str__(self):
        return f"{self.platform_name} ({self.platform_video_id}) - {self.video.title[:50]}"

# --- Transcript and NLP Feature Models ---
class Transcript(models.Model):
    """
    Stores the transcript content for a specific VideoSource.
    """
    id = models.BigAutoField(primary_key=True)
    # Each VideoSource can have one transcript (or one per language)
    video_source = models.ForeignKey(VideoSource, related_name='transcripts', on_delete=models.CASCADE, db_index=True)
    language_code = models.CharField(max_length=15, default='en', db_index=True, help_text="Language code of the transcript, e.g., en, es-MX, fr.")
    # Full plain text of the transcript, intended for FULLTEXT search.
    transcript_text_content = models.TextField(help_text="Full plain text of the transcript.") # Uses LONGTEXT in MySQL
    # Stores structured timed transcript data (e.g., list of {'text': 'word', 'start_ms': 100, 'end_ms': 150})
    transcript_timed_json = models.JSONField(null=True, blank=True, help_text="Transcript with word/phrase level timestamps.")
    quality_score = models.FloatField(null=True, blank=True, help_text="Estimated quality of the transcript (0.0 to 1.0).")
    processing_status_choices = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('not_available', 'Not Available'), # If transcript doesn't exist for source
    ]
    processing_status = models.CharField(max_length=20, choices=processing_status_choices, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('video_source', 'language_code') # One transcript per language for a given video source
        indexes = [
            # Add FULLTEXT index manually for transcript_text_content if using MySQL via migration
            # migrations.RunSQL("ALTER TABLE api_transcript ADD FULLTEXT(transcript_text_content);")
        ]

    def __str__(self):
        return f"Transcript for {self.video_source.platform_video_id} ({self.language_code})"

class ExtractedKeyword(models.Model):
    """
    Keywords extracted from a Transcript.
    """
    id = models.BigAutoField(primary_key=True)
    transcript = models.ForeignKey(Transcript, related_name='keywords', on_delete=models.CASCADE, db_index=True)
    keyword_text = models.CharField(max_length=255, db_index=True)
    relevance_score = models.FloatField(null=True, blank=True, help_text="Score from the keyword extraction algorithm.")
    # Add created_at for potential pruning of old/irrelevant keywords if needed
    # created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('transcript', 'keyword_text') # Avoid duplicate keywords for the same transcript

    def __str__(self):
        return self.keyword_text

class VideoTopic(models.Model):
    """
    Topics identified from a Transcript using topic modeling.
    """
    id = models.BigAutoField(primary_key=True)
    transcript = models.ForeignKey(Transcript, related_name='topics', on_delete=models.CASCADE, db_index=True)
    topic_label = models.CharField(max_length=255, db_index=True, help_text="Human-readable topic label.")
    topic_relevance_score = models.FloatField(null=True, blank=True, help_text="Score from the topic modeling algorithm.")
    # created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('transcript', 'topic_label')

    def __str__(self):
        return self.topic_label

# --- Visual Feature Models (Metadata stored in MySQL, Vectors likely in Vector DB) ---
class VideoFrameFeature(models.Model):
    """
    Metadata about visual features extracted from a video frame.
    The actual vector embeddings are typically stored in a specialized Vector DB.
    """
    id = models.BigAutoField(primary_key=True)
    video_source = models.ForeignKey(VideoSource, related_name='frame_features', on_delete=models.CASCADE, db_index=True)
    timestamp_in_video_ms = models.PositiveIntegerField(help_text="Timestamp of the frame in milliseconds from video start.")
    # Optional URL if PAPRI stores representative keyframes (e.g., on S3)
    frame_image_url = models.URLField(max_length=2048, null=True, blank=True, help_text="URL to a stored representative image of the frame.")
    feature_type = models.CharField(max_length=50, db_index=True, help_text="Type of feature, e.g., EfficientNetV2S_embedding, pHash.")
    
    # For perceptual hashes (e.g., from imagehash library)
    hash_value = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text="Perceptual hash value if applicable.")
    
    # If storing small feature sets directly (e.g., ORB keypoints as JSON)
    # For large embeddings, this field would NOT be used here; they go to Vector DB.
    feature_data_json = models.JSONField(null=True, blank=True, help_text="Additional metadata like ORB keypoints, or small features.")
    
    # This ID would be used to link to the actual vector in the Vector DB
    vector_db_id = models.CharField(max_length=255, null=True, blank=True, db_index=True, unique=True, help_text="ID of the corresponding vector in the Vector DB.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A frame at a specific time for a video source should ideally have one set of features of a certain type
        unique_together = ('video_source', 'timestamp_in_video_ms', 'feature_type')
        indexes = [
            models.Index(fields=['video_source', 'timestamp_in_video_ms'], name='api_frame_time_idx'),
        ]

    def __str__(self):
        return f"{self.feature_type} for {self.video_source.platform_video_id} at {self.timestamp_in_video_ms}ms"

# --- User Activity and Search Task Models ---
class SearchTask(models.Model):
    """
    Tracks an asynchronous search initiated by a user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique ID for the search task.")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, help_text="User who initiated the search (if logged in).")
    session_id = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text="Session ID for anonymous users.")
    
    query_text = models.TextField(null=True, blank=True)
    # Store reference to uploaded image (e.g., path in temp storage or S3 key)
    # The actual image data shouldn't be in the DB long-term.
    query_image_ref = models.CharField(max_length=1024, null=True, blank=True, help_text="Reference to the uploaded query image.")
    query_image_fingerprint = models.CharField(max_length=255, null=True, blank=True, db_index=True, help_text="Hash/fingerprint of the uploaded query image for quick checks.")
    
    applied_filters_json = models.JSONField(null=True, blank=True, help_text="JSON representation of filters applied to this search.")
    
    status_choices = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial_results', 'Partial Results'), # If some sources failed
    ]
    status = models.CharField(max_length=20, choices=status_choices, default='pending', db_index=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Store a summary or IDs of the results. Full result data is usually fetched on demand.
    # result_summary_json = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SearchTask {self.id} ({self.status})"

# Optional: Model to store actual results of a search task if you don't want to re-aggregate.
# class SearchTaskResult(models.Model):
#     task = models.ForeignKey(SearchTask, related_name='results_link', on_delete=models.CASCADE)
#     video_source = models.ForeignKey(VideoSource, on_delete=models.CASCADE)
#     rank = models.PositiveIntegerField()
#     relevance_score = models.FloatField(null=True, blank=True)
#     # other specific metadata relevant to this result in this search context
#     class Meta:
#         unique_together = ('task', 'video_source')
#         ordering = ['rank']


# If you add SignupCode model as discussed for payments:
class SignupCode(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(unique=True, help_text="Email address the code was sent to.")
    code = models.CharField(max_length=10, unique=True, db_index=True) # 6-digit, but make flexible
    plan_name = models.CharField(max_length=100, default="Pro Plan") # In case of multiple plans
    is_used = models.BooleanField(default=False, db_index=True)
    user_activated = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="signup_code_used")
    payment_reference = models.CharField(max_length=255, null=True, blank=True, help_text="Reference from payment gateway, e.g., Stripe PaymentIntent ID.")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiry for the code.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Code {self.code} for {self.email} (Used: {self.is_used})"


# backend/api/models.py
# ... other imports and models ...

class SearchTask(models.Model):
    # ... existing fields ...
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique ID for the search task.")
    # ...
    status = models.CharField(max_length=20, choices=SearchTask.status_choices, default='pending', db_index=True)
    error_message = models.TextField(null=True, blank=True)
    
    # NEW FIELD: Store JSON array of Papri Video model IDs that are results of this task
    result_video_ids_json = models.JSONField(null=True, blank=True, help_text="JSON array of Papri Video IDs for this task's results.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SearchTask {self.id} ({self.status})"
