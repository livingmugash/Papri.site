# backend/ai_agents/transcript_analyzer.py
import spacy
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from api.models import Transcript, ExtractedKeyword # For saving data
from django.utils import timezone

class TranscriptAnalyzer:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("TranscriptAnalyzer: Downloading spaCy en_core_web_sm model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        print("TranscriptAnalyzer initialized.")

    def _fetch_youtube_transcript(self, youtube_video_id, preferred_languages=['en', 'en-US']):
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_video_id)
            
            # Try to find a transcript in preferred languages
            for lang_code in preferred_languages:
                try:
                    transcript = transcript_list.find_transcript([lang_code])
                    fetched_transcript = transcript.fetch() # List of dicts [{'text': '...', 'start': ..., 'duration': ...}]
                    full_text = " ".join([segment['text'] for segment in fetched_transcript])
                    return full_text, transcript.language_code, fetched_transcript # Return full text, lang code, and timed segments
                except NoTranscriptFound:
                    continue # Try next preferred language
            
            # If no preferred language found, try any generated transcript
            try:
                generated_transcripts = [t for t in transcript_list if t.is_generated]
                if generated_transcripts:
                    transcript = generated_transcripts[0] # Take the first available generated one
                    fetched_transcript = transcript.fetch()
                    full_text = " ".join([segment['text'] for segment in fetched_transcript])
                    return full_text, transcript.language_code, fetched_transcript
            except NoTranscriptFound: # Should be caught by outer try now
                pass

            # If still no transcript, try fetching any manual transcript
            manual_transcripts = [t for t in transcript_list if not t.is_generated]
            if manual_transcripts:
                transcript = manual_transcripts[0]
                fetched_transcript = transcript.fetch()
                full_text = " ".join([segment['text'] for segment in fetched_transcript])
                return full_text, transcript.language_code, fetched_transcript

            print(f"TranscriptAnalyzer: No suitable transcript found for YouTube ID {youtube_video_id} after checking all options.")
            return None, None, None

        except TranscriptsDisabled:
            print(f"TranscriptAnalyzer: Transcripts are disabled for YouTube ID {youtube_video_id}")
            return None, None, None
        except Exception as e:
            print(f"TranscriptAnalyzer: Error fetching YouTube transcript for {youtube_video_id}: {e}")
            return None, None, None

    def _extract_keywords(self, text_content, num_keywords=10):
        if not text_content:
            return []
        doc = self.nlp(text_content.lower()) # Process in lowercase
        # Simple keyword extraction: Nouns and Proper Nouns, excluding stop words and punctuation
        keywords = [
            token.lemma_ 
            for token in doc 
            if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'ADJ'] # Added ADJ
        ]
        # Get frequency and return top N unique keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [kw for kw, count in keyword_counts.most_common(num_keywords)]


    def process_transcript_for_video_source(self, video_source_obj, raw_video_data_item):
        """
        Fetches/processes transcript, extracts keywords, and saves them.
        video_source_obj: The VideoSource Django model instance.
        raw_video_data_item: Data from SOIAgent, might contain platform_video_id.
        Returns a dict of analysis results or None.
        """
        full_text_transcript = None
        timed_transcript_json = None
        lang_code = 'en' # Default

        if video_source_obj.platform_name == 'YouTube':
            youtube_video_id = video_source_obj.platform_video_id
            if youtube_video_id:
                full_text_transcript, lang_code, timed_transcript_json = self._fetch_youtube_transcript(youtube_video_id)
            else:
                print(f"TranscriptAnalyzer: Missing YouTube video ID for VideoSource {video_source_obj.id}")
                return None
        # TODO: Add transcript fetching logic for Vimeo, Dailymotion, etc.
        # Vimeo API might provide text tracks. Dailymotion is less clear on public transcript APIs.
        # This might involve scraping or checking raw_video_data_item for transcript info.
        else:
            print(f"TranscriptAnalyzer: Transcript processing not yet implemented for platform: {video_source_obj.platform_name}")
            # For now, we can try to extract keywords from description if no transcript
            if raw_video_data_item and raw_video_data_item.get('description'):
                print(f"TranscriptAnalyzer: Using description for keyword extraction for {video_source_obj.platform_name}")
                full_text_transcript = raw_video_data_item.get('description')
                # lang_code might need detection if not 'en'
            else:
                 return None # No transcript and no description

        if not full_text_transcript:
            # Update or create Transcript record with 'not_available' status
            transcript_obj, created = Transcript.objects.update_or_create(
                video_source=video_source_obj,
                language_code=lang_code or 'und', # 'und' for undetermined
                defaults={
                    'transcript_text_content': "",
                    'processing_status': 'not_available',
                    'updated_at': timezone.now()
                }
            )
            print(f"TranscriptAnalyzer: No transcript content found or fetched for VideoSource {video_source_obj.id}.")
            return {"status": "no_transcript_content"}

        # Save or update the transcript
        transcript_obj, created = Transcript.objects.update_or_create(
            video_source=video_source_obj,
            language_code=lang_code, # Use the detected language code
            defaults={
                'transcript_text_content': full_text_transcript,
                'transcript_timed_json': timed_transcript_json, # Store timed data if available
                'processing_status': 'processed', # Mark as processed
                'quality_score': 0.7 if lang_code and 'en' in lang_code else 0.5, # Dummy quality score
                'updated_at': timezone.now()
            }
        )
        print(f"TranscriptAnalyzer: Transcript {'created' if created else 'updated'} for VideoSource ID {video_source_obj.id}, Lang: {lang_code}")

        # Extract and save keywords
        extracted_keywords_texts = self._extract_keywords(full_text_transcript)
        
        # Bulk create keywords for efficiency, avoiding duplicates for this transcript
        existing_keywords_for_transcript = set(
            ExtractedKeyword.objects.filter(transcript=transcript_obj).values_list('keyword_text', flat=True)
        )
        keywords_to_create = []
        for kw_text in extracted_keywords_texts:
            if kw_text not in existing_keywords_for_transcript:
                keywords_to_create.append(ExtractedKeyword(transcript=transcript_obj, keyword_text=kw_text))
        
        if keywords_to_create:
            ExtractedKeyword.objects.bulk_create(keywords_to_create)
            print(f"TranscriptAnalyzer: Saved {len(keywords_to_create)} new keywords for Transcript ID {transcript_obj.id}")

        return {
            "transcript_id": transcript_obj.id,
            "language_code": lang_code,
            "keywords": extracted_keywords_texts,
            "status": "processed"
        }
