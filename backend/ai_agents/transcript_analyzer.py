# backend/ai_agents/transcript_analyzer.py
import spacy
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from api.models import Transcript, ExtractedKeyword, Video
from django.utils import timezone
from django.conf import settings

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models as qdrant_models
from qdrant_client.http.models import PointStruct, Distance, VectorParams

import requests
import webvtt # For parsing VTT files
from io import StringIO # For webvtt.read_buffer
import re # For cleaning VTT text
from urllib.parse import urlparse, urljoin # For making relative VTT URLs absolute
import logging

logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    def __init__(self):
        # ... (SpaCy, SentenceTransformer, Qdrant client initialization as in Step 25/30) ...
        logger.info("TranscriptAnalyzer: Initializing...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError: # ... (download spacy model)
            logger.info("TranscriptAnalyzer: Downloading spaCy en_core_web_sm model...")
            spacy.cli.download("en_core_web_sm"); self.nlp = spacy.load("en_core_web_sm")
        
        try:
            self.embedding_model_name = settings.SENTENCE_TRANSFORMER_MODEL
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"TA: ST model '{self.embedding_model_name}' loaded. Dim: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"TA: CRITICAL - Failed to load SentenceTransformer model: {e}")
            self.embedding_model = None; self.embedding_dim = 0

        self.qdrant_collection_name = settings.QDRANT_COLLECTION_TRANSCRIPTS
        self.qdrant_client = None
        if self.embedding_dim > 0:
            try:
                self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=20)
                self.qdrant_client.health_check()
                logger.info(f"TA: Connected to Qdrant at {settings.QDRANT_URL or settings.QDRANT_HOST}")
                self._ensure_qdrant_collection_exists() # From Step 25
            except Exception as e:
                logger.error(f"TA: CRITICAL - Qdrant connection/collection setup failed: {e}")
                self.qdrant_client = None
        else:
            logger.warning("TA: Embedding model not loaded, Qdrant client for transcripts not initialized.")
        logger.info("TranscriptAnalyzer initialized.")

    def _ensure_qdrant_collection_exists(self):
        # ... (Implementation from Step 25, ensuring collection for self.embedding_dim exists) ...
        if not self.qdrant_client: return
        try:
            try: self.qdrant_client.get_collection(collection_name=self.qdrant_collection_name)
            except Exception:
                self.qdrant_client.recreate_collection(
                    collection_name=self.qdrant_collection_name,
                    vectors_config=qdrant_models.VectorParams(size=self.embedding_dim, distance=qdrant_models.Distance.COSINE)
                )
                self.qdrant_client.create_payload_index(collection_name=self.qdrant_collection_name, field_name="video_papri_id", field_schema=qdrant_models.PayloadSchemaType.INTEGER)
                logger.info(f"TA: Qdrant transcript collection '{self.qdrant_collection_name}' created/ensured.")
        except Exception as e: logger.error(f"TA: Error ensuring Qdrant transcript collection: {e}")


    def _fetch_youtube_transcript(self, youtube_video_id, preferred_languages=['en', 'en-US']):
        # ... (Implementation from Step 25 - robustly fetches YouTube transcript segments) ...
        # Returns (full_text, lang_code, timed_segments_list_of_dicts)
        logger.debug(f"TA: Fetching YouTube transcript for ID {youtube_video_id}")
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(youtube_video_id)
            found_transcript_data = None
            for lang_code_pref in preferred_languages:
                try:
                    transcript = transcript_list.find_transcript([lang_code_pref])
                    fetched_segments = transcript.fetch()
                    full_text = " ".join([segment['text'] for segment in fetched_segments])
                    found_transcript_data = (full_text, transcript.language_code, fetched_segments)
                    break 
                except NoTranscriptFound: continue
            
            if not found_transcript_data: # If preferred not found, try generated then manual
                for find_method in [transcript_list.find_generated_transcript, transcript_list.find_manually_created_transcript]:
                    try:
                        # Try with all available languages for this type
                        transcript = find_method(transcript_list.language_codes)
                        fetched_segments = transcript.fetch()
                        full_text = " ".join([segment['text'] for segment in fetched_segments])
                        found_transcript_data = (full_text, transcript.language_code, fetched_segments)
                        break
                    except NoTranscriptFound: continue
            
            if found_transcript_data:
                logger.info(f"TA: YouTube transcript fetched for {youtube_video_id} (Lang: {found_transcript_data[1]})")
                return found_transcript_data
            else:
                logger.warning(f"TA: No suitable YouTube transcript found for {youtube_video_id}.")
                return None, None, None
        except TranscriptsDisabled: logger.warning(f"TA: Transcripts disabled for YT ID {youtube_video_id}"); return None, None, None
        except Exception as e: logger.error(f"TA: Error fetching YT transcript for {youtube_video_id}: {e}"); return None, None, None


    def _fetch_and_parse_vtt_url(self, vtt_url):
        logger.debug(f"TA: Fetching VTT from URL: {vtt_url}")
        try:
            response = requests.get(vtt_url, timeout=20)
            response.raise_for_status()
            vtt_content = response.text
            if not vtt_content.strip().startswith("WEBVTT"):
                logger.warning(f"TA: Content from {vtt_url} does not appear to be valid VTT (header missing).")
                # Attempt to parse anyway, but it might fail or be incorrect.
            
            captions = webvtt.read_buffer(StringIO(vtt_content))
            full_text_parts = []
            timed_segments = []

            for caption in captions:
                clean_text = caption.text.replace('\n', ' ').strip()
                clean_text = re.sub(r'<(\/?)[^>]+(\/?)>', '', clean_text) 
                clean_text = re.sub(r'&nbsp;', ' ', clean_text)
                clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()
                if clean_text:
                    full_text_parts.append(clean_text)
                    try: # Safely parse timestamps
                        start_ms = int(webvtt.structures.Timestamp.from_srt(caption.start).total_seconds() * 1000)
                        end_ms = int(webvtt.structures.Timestamp.from_srt(caption.end).total_seconds() * 1000)
                        timed_segments.append({'text': clean_text, 'start': start_ms, 'duration': end_ms - start_ms})
                    except Exception as ts_e:
                        logger.warning(f"TA: Could not parse timestamp for VTT caption '{caption.text[:30]}...': {ts_e}")
                        timed_segments.append({'text': clean_text, 'start': 0, 'duration': 0}) # Add with default time

            full_text = " ".join(full_text_parts).strip()
            logger.info(f"TA: Parsed VTT from {vtt_url}. Text Length: {len(full_text)}, Segments: {len(timed_segments)}")
            return full_text, timed_segments if timed_segments else None
        except requests.exceptions.RequestException as e: logger.error(f"TA: Failed to download VTT from {vtt_url}: {e}"); return None, None
        except webvtt.errors.MalformedCaptionError as e: logger.error(f"TA: Malformed VTT content from {vtt_url}: {e}"); return None, None
        except Exception as e: logger.error(f"TA: Error processing VTT file from {vtt_url}: {e}"); return None, None


    def _extract_keywords(self, text_content, num_keywords=15):
        # ... (Implementation from Step 25, ensure SpaCy model is loaded) ...
        if not text_content or not self.nlp: return []
        # ... (rest of the logic)
        doc = self.nlp(text_content.lower())
        keywords = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'ADJ', 'VERB']]
        from collections import Counter
        return [kw for kw, count in Counter(keywords).most_common(num_keywords)]


    def _generate_embedding(self, text_content):
        # ... (Implementation from Step 25, ensure SentenceTransformer model is loaded) ...
        if not self.embedding_model or not text_content: return None
        # ... (rest of the logic)
        try: return self.embedding_model.encode(text_content, convert_to_tensor=False).tolist()
        except Exception as e: logger.error(f"TA: Error generating embedding: {e}"); return None

    def _store_embedding_in_qdrant(self, transcript_django_id, video_papri_id, embedding_vector):
        # ... (Implementation from Step 25, Qdrant upsert) ...
        if not self.qdrant_client or not embedding_vector: return False
        # ... (rest of the logic)
        try:
            points = [qdrant_models.PointStruct(id=transcript_django_id, vector=embedding_vector, payload={"video_papri_id": video_papri_id, "last_updated": timezone.now().isoformat()})]
            response = self.qdrant_client.upsert_points(collection_name=self.qdrant_collection_name, points=points, wait=True)
            logger.info(f"TA: Upserted embedding for Django Transcript ID {transcript_django_id} into Qdrant. Status: {response.status if hasattr(response, 'status') else 'OK'}")
            return True
        except Exception as e: logger.error(f"TA: Error storing embedding in Qdrant for Transcript ID {transcript_django_id}: {e}"); return False


    def process_transcript_for_video_source(self, video_source_obj, raw_video_data_item):
        # ... (Combined logic from Step 34) ...
        logger.info(f"TA: Processing transcript for VSID {video_source_obj.id} ({video_source_obj.platform_name})")
        full_text_transcript = None
        timed_transcript_json = None
        lang_code_from_source = raw_video_data_item.get('language_code') # From scraper
        
        source_platform = video_source_obj.platform_name.lower() # Normalize platform name

        if 'youtube' in source_platform:
            youtube_video_id = video_source_obj.platform_video_id
            if youtube_video_id:
                full_text_transcript, lang_code_yt, timed_transcript_json_yt = self._fetch_youtube_transcript(youtube_video_id)
                if full_text_transcript:
                    lang_code_from_source = lang_code_yt or lang_code_from_source # Prioritize API's lang_code
                    timed_transcript_json = timed_transcript_json_yt
        
        # Check for VTT URL from scraper (e.g., for PeerTube) AFTER API attempts
        if not full_text_transcript and raw_video_data_item.get('transcript_vtt_url'):
            vtt_url = raw_video_data_item['transcript_vtt_url']
            # Ensure VTT URL is absolute
            if not vtt_url.startswith(('http://', 'https://')) and video_source_obj.original_url:
                vtt_url = urljoin(video_source_obj.original_url, vtt_url)
            
            full_text_transcript, timed_vtt_segments = self._fetch_and_parse_vtt_url(vtt_url)
            if full_text_transcript and not lang_code_from_source: # If scraper didn't provide lang_code for VTT
                # Basic language detection for VTT text can be added here if needed
                # For now, assume 'und' or keep existing if any
                pass
            if timed_vtt_segments: timed_transcript_json = timed_vtt_segments

        # Check for directly scraped transcript text
        if not full_text_transcript and raw_video_data_item.get('transcript_text'):
            full_text_transcript = raw_video_data_item['transcript_text']
            logger.info(f"TA: Using directly scraped transcript text for VSID {video_source_obj.id}")

        # Fallback to description if still no transcript
        if not full_text_transcript and raw_video_data_item.get('description'):
            full_text_transcript = raw_video_data_item.get('description')
            logger.info(f"TA: No transcript, using description for VSID {video_source_obj.id}")
            # Language code for description is harder to determine without detection

        final_lang_code = lang_code_from_source or 'und' # 'und' for undetermined

        if not full_text_transcript:
            Transcript.objects.update_or_create(
                video_source=video_source_obj, language_code=final_lang_code,
                defaults={'transcript_text_content': "", 'processing_status': 'not_available', 'updated_at': timezone.now()}
            )
            logger.warning(f"TA: No transcript/description content for VSID {video_source_obj.id}.")
            return {"status": "no_transcript_content"}

        if not video_source_obj.video:
            logger.error(f"TA: VSID {video_source_obj.id} lacks linked canonical Video. Cannot process transcript.")
            return {"status": "error_video_not_linked"}

        transcript_obj, created = Transcript.objects.update_or_create(
            video_source=video_source_obj, language_code=final_lang_code,
            defaults={
                'transcript_text_content': full_text_transcript,
                'transcript_timed_json': timed_transcript_json, # Store parsed timed data
                'processing_status': 'pending_nlp', # Changed status
                'updated_at': timezone.now()
            }
        )
        logger.info(f"TA: Transcript {'created' if created else 'updated'} for VSID {video_source_obj.id}, Lang: {final_lang_code}. Status: pending_nlp.")

        # NLP: Keywords
        extracted_keywords_texts = self._extract_keywords(full_text_transcript)
        # ... (keyword saving logic as before - ensure it's robust)
        if created: keywords_to_create = [ExtractedKeyword(transcript=transcript_obj, keyword_text=kw) for kw in extracted_keywords_texts]
        else:
            existing_kws = set(ExtractedKeyword.objects.filter(transcript=transcript_obj).values_list('keyword_text', flat=True))
            keywords_to_create = [ExtractedKeyword(transcript=transcript_obj, keyword_text=kw) for kw in extracted_keywords_texts if kw not in existing_kws]
        if keywords_to_create: ExtractedKeyword.objects.bulk_create(keywords_to_create)
        logger.info(f"TA: Saved {len(keywords_to_create)} new keywords for Transcript ID {transcript_obj.id}")
        
        # NLP: Embeddings
        embedding_vector = self._generate_embedding(full_text_transcript)
        embedding_stored = False
        if embedding_vector:
            embedding_stored = self._store_embedding_in_qdrant(transcript_obj.id, video_source_obj.video.id, embedding_vector)
        
        transcript_obj.processing_status = 'processed' if embedding_stored else 'analysis_failed_embedding_storage'
        transcript_obj.save(update_fields=['processing_status', 'updated_at'])

        return {
            "transcript_id": transcript_obj.id, "language_code": final_lang_code,
            "keywords_count": len(extracted_keywords_texts), # Return count for logging
            "embedding_generated": bool(embedding_vector),
            "embedding_stored": embedding_stored, "status": transcript_obj.processing_status
        }
