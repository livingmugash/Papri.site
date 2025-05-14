# backend/api/management/commands/indexvideosvisual.py
from django.core.management.base import BaseCommand, CommandError
from api.models import VideoSource, VideoFrameFeature # Assuming VideoFrameFeature indicates indexing
from api.tasks import index_video_visual_features # Import your Celery task
from django.db.models import Count

class Command(BaseCommand):
    help = 'Dispatches Celery tasks to index visual features for videos that have not been processed yet or specified ones.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video_source_ids',
            nargs='+', # one or more arguments
            type=int,
            help='Specific VideoSource IDs to index.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10, # Default number of videos to process if no IDs are given
            help='Number of unindexed videos to process.',
        )
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='Re-index videos even if they already have some frame features.',
        )
        parser.add_argument(
            '--platform',
            type=str,
            help='Only index videos from a specific platform (e.g., YouTube).',
        )

    def handle(self, *args, **options):
        video_source_ids = options['video_source_ids']
        limit = options['limit']
        reindex = options['reindex']
        platform_filter = options['platform']

        if video_source_ids:
            sources_to_process = VideoSource.objects.filter(id__in=video_source_ids)
            if not sources_to_process.exists():
                raise CommandError(f"No VideoSource objects found for IDs: {video_source_ids}")
            self.stdout.write(self.style.SUCCESS(f"Processing specified {sources_to_process.count()} VideoSource IDs."))
        else:
            self.stdout.write(self.style.NOTICE(f"No specific VideoSource IDs provided. Looking for up to {limit} videos to index..."))

            # Find VideoSources that don't have any VideoFrameFeature entries yet
            # or all VideoSources if --reindex is specified.
            unindexed_sources_query = VideoSource.objects.all()

            if platform_filter:
                unindexed_sources_query = unindexed_sources_query.filter(platform_name__iexact=platform_filter)
                self.stdout.write(self.style.NOTICE(f"Filtering by platform: {platform_filter}"))

            if not reindex:
                # Annotate with a count of existing frame features
                unindexed_sources_query = unindexed_sources_query.annotate(
                    frame_feature_count=Count('frame_features')
                ).filter(frame_feature_count=0)
                # This ensures we only pick those with no features yet.

            sources_to_process = unindexed_sources_query.order_by('?')[:limit] # Random order, take limit

            if not sources_to_process:
                self.stdout.write(self.style.SUCCESS("No videos found needing visual indexing based on current criteria."))
                return

        count = 0
        for vs in sources_to_process:
            if not vs.original_url:
                self.stdout.write(self.style.WARNING(f"Skipping VideoSource ID {vs.id} (Papri Video ID: {vs.video.id if vs.video else 'N/A'}) - missing original_url."))
                continue

            self.stdout.write(f"Dispatching visual indexing task for VideoSource ID: {vs.id} (URL: {vs.original_url})...")
            try:
                index_video_visual_features.delay(vs.id)
                count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to dispatch task for VideoSource ID {vs.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully dispatched {count} visual indexing tasks."))
        if video_source_ids and count < len(video_source_ids):
            self.stdout.write(self.style.WARNING(f"Note: Some specified IDs might have been skipped (e.g., missing URL)."))
