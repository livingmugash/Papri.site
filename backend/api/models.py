# backend/api/models.py
from django.db import models
from django.contrib.auth.models import User # Using Django's built-in User model
import uuid

class Video(models.Model):
    # video_papri_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.BigAutoField(primary_key=True) # Simpler auto-incrementing ID
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    publication_date = models.DateTimeField(null=True, blank=True)
    primary_thumbnail_url = models.URLField(max_length=2048, null=True, blank=True)
    deduplication_hash = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['title']), # Consider full-text search capabilities of MySQL
            models.Index(fields=['publication_date']),
        ]

class VideoSource(models.Model):
    id = models.BigAutoField(primary_key=True)
    video = models.ForeignKey(Video, related_name='sources', on_delete=models.CASCADE, db_index=True)
    platform_name = models.CharField(max_length=100, db_index=True) # e.g., "YouTube", "Vimeo"
    platform_video_id = models.CharField(max_length=255, db_index=True)
    original_url = models.URLField(max_length=2048, unique=True)
    embed_url = models.URLField(max_length=2048, null=True, blank=True)
    source_metadata_json = models.JSONField(null=True, blank=True) # Raw metadata from source
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    is_primary_source = models.BooleanField(default=False) # If this is the canonical source

    class Meta:
        unique_together = ('platform_name', 'platform_video_id')
        indexes = [
            models.Index(fields=['original_url']),
        ]

    def __str__(self):
        return f"{self.platform_name}: {self.video.title[:50]}"

class Transcript(models.Model):
    id = models.BigAutoField(primary_key=True)
    video_source = models.OneToOneField(VideoSource, related_name='transcript', on_delete=models.CASCADE, db_index=True)
    language_code = models.CharField(max_length=10, default='en', db_index=True)
    transcript_text_content = models.TextField() # LONGTEXT in MySQL
    transcript_timed_json = models.JSONField(null=True, blank=True) # For word/phrase level timestamps
    quality_score = models.FloatField(null=True, blank=True) # Estimated quality 0.0-1.0
    processing_status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processed', 'Processed'), ('failed', 'Failed')], default='pending')

    class Meta:
        indexes = [
             # Consider full-text search on transcript_text_content using Django's SearchVector or MySQL's features
        ]

    def __str__(self):
        return f"Transcript for {self.video_source_id} ({self.language_code})"

class ExtractedKeyword(models.Model):
    id = models.BigAutoField(primary_key=True)
    transcript = models.ForeignKey(Transcript, related_name='keywords', on_delete=models.CASCADE, db_index=True)
    keyword_text = models.CharField(max_length=255, db_index=True)
    relevance_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.keyword_text

class VideoTopic(models.Model):
    id = models.BigAutoField(primary_key=True)
    transcript = models.ForeignKey(Transcript, related_name='topics', on_delete=models.CASCADE, db_index=True)
    topic_label = models.CharField(max_length=255, db_index=True)
    topic_relevance_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.topic_label

class VideoFrameFeature(models.Model):
    id = models.BigAutoField(primary_key=True)
    video_source = models.ForeignKey(VideoSource, related_name='frame_features', on_delete=models.CASCADE, db_index=True)
    timestamp_in_video_ms = models.PositiveIntegerField()
    frame_image_url = models.URLField(max_length=2048, null=True, blank=True) # Optional, if keyframes are stored
    feature_type = models.CharField(max_length=50, db_index=True) # e.g., "EfficientNetV2S_embedding", "pHash"

    # For perceptual hashes
    hash_value = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # For vector embeddings (if stored in MySQL, otherwise this is in Vector DB)
    # embedding_vector = models.BinaryField(null=True, blank=True) # Requires custom handling for search

    feature_metadata_json = models.JSONField(null=True, blank=True) # e.g., ORB keypoints

    def __str__(self):
        return f"Frame feature for {self.video_source_id} at {self.timestamp_in_video_ms}ms"

# ---- Models for Vector DB (Conceptual - not Django models, but represent data in Vector DB) ----
# class TranscriptEmbedding_VectorDB:
#     transcript_id: int # FK to api.Transcript.id
#     embedding_vector: list[float]
#     model_name: str

# class FrameEmbedding_VectorDB:
#     frame_feature_id: int # FK to api.VideoFrameFeature.id
#     embedding_vector: list[float]
#     model_name: str
# ---- End Vector DB Conceptual Models ----


# User query history for analytics and potential personalization
class UserSearchQuery(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL) # Link to Django User
    session_id = models.CharField(max_length=255, null=True, blank=True, db_index=True) # For anonymous users
    query_text = models.TextField(null=True, blank=True)
    query_image_fingerprint = models.CharField(max_length=255, null=True, blank=True) # Hash of uploaded image
    query_timestamp = models.DateTimeField(auto_now_add=True)
    applied_filters_json = models.JSONField(null=True, blank=True)
    # Store results? Perhaps IDs of top N results for relevance feedback
    # result_video_ids_json = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Query by {self.user_id or self.session_id} at {self.query_timestamp}"
