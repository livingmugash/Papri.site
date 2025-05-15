# backend/ai_agents/transcript_analyzer.py
import spacy
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from api.models import Transcript, ExtractedKeyword # For saving data
from django.utils import timezone
from django.conf import settings # For potential Vector DB connection details
import requests
import webvtt
from io import StringIO # For webvtt.read_buffer
import re # For cleaning VTT text
from urllib.parse import urlparse, urljoin # For making relative VTT URLs absolute
# ...
# For Embeddings
from sentence_transformers import SentenceTransformer
# For Vector DB (Example with Milvus client - adapt if using another)
from pymilvus import connections, Collection, utility, FieldSchema, DataType, CollectionSchema


class TranscriptAnalyzer:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("TranscriptAnalyzer: Downloading spaCy en_core_web_sm model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        print("TranscriptAnalyzer initialized.")

    try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            print(f"TranscriptAnalyzer: SentenceTransformer model loaded. Embedding dim: {self.embedding_dim}")
        except Exception as e:
            print(f"TranscriptAnalyzer: CRITICAL - Failed to load SentenceTransformer model: {e}")
            self.embedding_model = None
            self.embedding_dim = 0

    # --- Vector DB Connection (Example for Milvus) ---
        self.vector_db_collection_name = "papri_transcript_embeddings"
        self.milvus_alias = "default" # Default Milvus connection alias
        try:
             connections.connect(
                 alias=self.milvus_alias,
                 host=settings.VECTOR_DB_HOST, # From Django settings
                 port=settings.VECTOR_DB_PORT
             )
             print(f"TranscriptAnalyzer: Connected to Milvus at {settings.VECTOR_DB_HOST}:{settings.VECTOR_DB_PORT}")
             self._ensure_milvus_collection_exists()
         except Exception as e:
             print(f"TranscriptAnalyzer: CRITICAL - Failed to connect to Milvus or ensure collection: {e}")
        # --- End Vector DB Connection ---
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

def _generate_embedding(self, text_content):
        if not self.embedding_model or not text_content:
            return None
        try:
            # Consider splitting long transcripts into chunks for better embedding quality
            # For now, embedding the whole transcript (can be lossy for very long texts)
            embedding = self.embedding_model.encode(text_content, convert_to_tensor=False) # Returns numpy array
            return embedding.tolist() # Convert to list for JSON serialization or DB storage
        except Exception as e:
            print(f"TranscriptAnalyzer: Error generating embedding: {e}")
            return None
def process_transcript_for_video_source(self, video_source_obj, raw_video_data_item):
        full_text_transcript = None
        timed_transcript_json = None
        lang_code = 'en' 

        if video_source_obj.platform_name == 'YouTube':
            youtube_video_id = video_source_obj.platform_video_id
            if youtube_video_id:
                full_text_transcript, lang_code, timed_transcript_json = self._fetch_youtube_transcript(youtube_video_id)
        # TODO: Add transcript fetching for Vimeo, Dailymotion if possible
        else:
            if raw_video_data_item and raw_video_data_item.get('description'):
                full_text_transcript = raw_video_data_item.get('description')
            else:
                Transcript.objects.update_or_create(
                    video_source=video_source_obj, language_code=lang_code or 'und',
                    defaults={'transcript_text_content': "", 'processing_status': 'not_available', 'updated_at': timezone.now()}
                )
                return {"status": "no_transcript_content"}

        if not full_text_transcript:
            Transcript.objects.update_or_create(
                video_source=video_source_obj, language_code=lang_code or 'und',
                defaults={'transcript_text_content': "", 'processing_status': 'not_available', 'updated_at': timezone.now()}
            )
            return {"status": "no_transcript_content"}

        # Ensure Video object is linked before proceeding
        if not video_source_obj.video:
            print(f"TranscriptAnalyzer: VideoSource ID {video_source_obj.id} is not linked to a canonical Video. Skipping transcript processing.")
            return {"status": "error_video_not_linked"}

        transcript_obj, created = Transcript.objects.update_or_create(
            video_source=video_source_obj, language_code=lang_code or 'en', # Use detected lang_code
            defaults={
                'transcript_text_content': full_text_transcript,
                'transcript_timed_json': timed_transcript_json,
                'processing_status': 'pending_analysis', 
                'updated_at': timezone.now()
            }
        )

        embedding_vector = self._generate_embedding(full_text_transcript)
        embedding_stored_successfully = False
        if embedding_vector:
            embedding_stored_successfully = self._store_embedding_in_qdrant(
               transcript_obj.id, # Qdrant point ID = Django Transcript ID
               video_source_obj.video.id, # Payload: Canonical Papri Video ID
               embedding_vector
            )
        else:
            print(f"TranscriptAnalyzer: Failed to generate embedding for Transcript ID {transcript_obj.id}")
        
        extracted_keywords_texts = self._extract_keywords(full_text_transcript)
        existing_keywords_for_transcript = set(ExtractedKeyword.objects.filter(transcript=transcript_obj).values_list('keyword_text', flat=True))
        keywords_to_create = [
            ExtractedKeyword(transcript=transcript_obj, keyword_text=kw_text)
            for kw_text in extracted_keywords_texts if kw_text not in existing_keywords_for_transcript
        ]
        if keywords_to_create: ExtractedKeyword.objects.bulk_create(keywords_to_create)

        transcript_obj.processing_status = 'processed' if embedding_stored_successfully else 'analysis_partial_failed_embedding'
        transcript_obj.save(update_fields=['processing_status'])

        return {
            "transcript_id": transcript_obj.id,
            "language_code": lang_code,
            "keywords": extracted_keywords_texts,
            "embedding_generated": bool(embedding_vector),
            "embedding_stored": embedding_stored_successfully,
            "status": transcript_obj.processing_status
        }


     def _ensure_milvus_collection_exists(self):
        if not utility.has_collection(self.vector_db_collection_name, using=self.milvus_alias):
            fields = [
                 FieldSchema(name="transcript_db_id", dtype=DataType.INT64, is_primary=True, auto_id=False), # Store our Django Transcript.id
                 FieldSchema(name="video_papri_id", dtype=DataType.INT64), # Store our Django Video.id for easier filtering
                 FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim)
             ]
             schema = CollectionSchema(fields, description="Transcript embeddings for Papri semantic search")
             collection = Collection(self.vector_db_collection_name, schema=schema, using=self.milvus_alias)
             print(f"Milvus collection '{self.vector_db_collection_name}' created.")
            
   
             index_params = {
                 "metric_type": "L2", # Or "IP" (Inner Product) for cosine similarity with normalized vectors
                 "index_type": "IVF_FLAT", # Common index type, explore others like HNSW
                 "params": {"nlist": 128}, 
            }
             collection.create_index(field_name="embedding", index_params=index_params)
             collection.load() # Load collection into memory for searching
             print(f"Milvus index created and collection loaded for '{self.vector_db_collection_name}'.")
         else:
             collection = Collection(self.vector_db_collection_name, using=self.milvus_alias)
             if not collection.has_index():
                  index_params = { "metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 128} }
                  collection.create_index(field_name="embedding", index_params=index_params)
                  print(f"Milvus index created for existing collection '{self.vector_db_collection_name}'.")
             collection.load()
             print(f"Milvus collection '{self.vector_db_collection_name}' already exists and is loaded.")
  


     def _store_embedding_in_vector_db(self, transcript_django_id, video_papri_id, embedding_vector):
        if not embedding_vector or not self.embedding_model: # Check embedding_model to see if vector DB setup was attempted
             return False
         try:
             collection = Collection(self.vector_db_collection_name, using=self.milvus_alias)
  
             data_to_insert = [[transcript_django_id], [video_papri_id], [embedding_vector]]
 
             Milvus upsert: collection.upsert([data_to_insert])
   
             res = collection.query(expr=f"transcript_db_id == {transcript_django_id}", output_fields=["transcript_db_id"])
   
                 mr = collection.insert(data_to_insert)
                 print(f"TranscriptAnalyzer: Stored embedding for Transcript ID {transcript_django_id} in Milvus. PKs: {mr.primary_keys}")
             else:
                 print(f"TranscriptAnalyzer: Embedding for Transcript ID {transcript_django_id} likely already in Milvus.")
             return True
         except Exception as e:
             print(f"TranscriptAnalyzer: Error storing embedding in Milvus for Transcript ID {transcript_django_id}: {e}")
             return False




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


    def _fetch_and_parse_vtt_url(self, vtt_url):
        """
        Downloads a VTT file from a URL and parses it into plain text.
        Returns plain text, or None if fetching/parsing fails.
        """
        try:
            self.logger.info(f"TranscriptAnalyzer: Fetching VTT from URL: {vtt_url}")
            response = requests.get(vtt_url, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors
            
            vtt_content = response.text
            captions = webvtt.read_buffer(StringIO(vtt_content)) # webvtt.read_buffer expects a file-like object
            # Or, if webvtt.from_string is available and preferred:
            # captions = webvtt.from_string(vtt_content)

            full_text_parts = []
            timed_segments = [] # Optional: if you want to store timed segments from VTT

            for caption in captions:
                # caption.text often contains the lines separated by \n, clean it up.
                # Also, VTT can have styling or metadata within the text.
                # A simple approach is to join lines and strip HTML-like tags.
                clean_text = caption.text.replace('\n', ' ').strip()
                # Basic cleaning of VTT cue settings/tags if any (e.g. <v User>Text</v>)
                clean_text = re.sub(r'<[^>]+>', '', clean_text) 
                full_text_parts.append(clean_text)
                
                # Optional: extract timing info if needed for transcript_timed_json
                start_ms = int(caption.start_in_seconds * 1000)
                end_ms = int(caption.end_in_seconds * 1000)
                timed_segments.append({'text': clean_text, 'start': start_ms, 'duration': end_ms - start_ms})

            full_text = " ".join(full_text_parts).strip()
            self.logger.info(f"TranscriptAnalyzer: Successfully parsed VTT from {vtt_url}. Length: {len(full_text)}")
            # return full_text, timed_segments # If returning timed segments
            return full_text, None # For now, just full text and None for timed_json from VTT
        except requests.exceptions.RequestException as e:
            self.logger.error(f"TranscriptAnalyzer: Failed to download VTT file from {vtt_url}: {e}")
            return None, None
        except webvtt.errors.MalformedCaptionError as e: # Catch specific webvtt parsing errors
            self.logger.error(f"TranscriptAnalyzer: Malformed VTT content from {vtt_url}: {e}")
            return None, None
        except Exception as e:
            self.logger.error(f"TranscriptAnalyzer: Error processing VTT file from {vtt_url}: {e}")
            return None, None


    def process_transcript_for_video_source(self, video_source_obj, raw_video_data_item):
        full_text_transcript = None
        timed_transcript_json = None # This will store list of dicts like {'text':.., 'start':.., 'duration':..}
        lang_code = raw_video_data_item.get('language_code', 'en') # Get lang from item if scraper provided it

        # Attempt to get transcript based on platform
        if video_source_obj.platform_name == 'YouTube':
            youtube_video_id = video_source_obj.platform_video_id
            if youtube_video_id:
                full_text_transcript, lang_code_yt, timed_transcript_json_yt = self._fetch_youtube_transcript(youtube_video_id)
                if full_text_transcript:
                    full_text_transcript = full_text_transcript
                    lang_code = lang_code_yt or lang_code # Prioritize detected lang
                    timed_transcript_json = timed_transcript_json_yt
        
        # Check if scraper provided a VTT URL (e.g., for PeerTube)
        elif raw_video_data_item.get('transcript_vtt_url'):
            vtt_url = raw_video_data_item['transcript_vtt_url']
            # Ensure it's a full URL
            if not vtt_url.startswith(('http://', 'https://')):
                parsed_original_url = urlparse(video_source_obj.original_url)
                vtt_url = urlunparse((parsed_original_url.scheme, parsed_original_url.netloc, vtt_url, '', '', ''))

            full_text_transcript, timed_vtt_segments = self._fetch_and_parse_vtt_url(vtt_url)
            # lang_code might need to be inferred from VTT or assumed
            # timed_transcript_json = timed_vtt_segments # If _fetch_and_parse_vtt_url returns it

        # Check if scraper provided direct transcript text
        elif raw_video_data_item.get('transcript_text'):
            full_text_transcript = raw_video_data_item['transcript_text']
            # lang_code might need to be inferred or assumed

        # Fallback to description if no transcript found by other means
        if not full_text_transcript and raw_video_data_item.get('description'):
            self.logger.info(f"TranscriptAnalyzer: No transcript found for VSID {video_source_obj.id}, using description.")
            full_text_transcript = raw_video_data_item.get('description')
            # lang_code might need detection here if not 'en' and description is in another lang

        lang_code = lang_code or 'und' # Ensure lang_code is not None

        if not full_text_transcript:
            # ... (Update/create Transcript record with 'not_available' status as before) ...
            Transcript.objects.update_or_create(
                video_source=video_source_obj, language_code=lang_code,
                defaults={'transcript_text_content': "", 'processing_status': 'not_available', 'updated_at': timezone.now()}
            )
            self.logger.info(f"TranscriptAnalyzer: No transcript/description content for VSID {video_source_obj.id}.")
            return {"status": "no_transcript_content"}

        if not video_source_obj.video: # ... (handle error_video_not_linked as before) ...
            self.logger.error(f"TranscriptAnalyzer: VSID {video_source_obj.id} lacks linked canonical Video.")
            return {"status": "error_video_not_linked"}

        transcript_obj, created = Transcript.objects.update_or_create(
            video_source=video_source_obj, language_code=lang_code,
            defaults={
                'transcript_text_content': full_text_transcript,
                'transcript_timed_json': timed_transcript_json, # Store if available
                'processing_status': 'pending_analysis', 
                'updated_at': timezone.now()
            }
        )
        # ... (Embedding generation & storage, keyword extraction & storage as before) ...
        embedding_vector = self._generate_embedding(full_text_transcript)
        embedding_stored = False
        if embedding_vector:
            embedding_stored = self._store_embedding_in_qdrant(transcript_obj.id, video_source_obj.video.id, embedding_vector)
        
        extracted_keywords_texts = self._extract_keywords(full_text_transcript)
        # ... (keyword saving logic) ...
        if created:
            keywords_to_create = [ExtractedKeyword(transcript=transcript_obj, keyword_text=kw_text) for kw_text in extracted_keywords_texts]
        else:
            existing_keywords = set(ExtractedKeyword.objects.filter(transcript=transcript_obj).values_list('keyword_text', flat=True))
            keywords_to_create = [ExtractedKeyword(transcript=transcript_obj, keyword_text=kw) for kw in extracted_keywords_texts if kw not in existing_keywords]
        if keywords_to_create: ExtractedKeyword.objects.bulk_create(keywords_to_create)

        transcript_obj.processing_status = 'processed' if embedding_stored else 'analysis_failed_embedding_storage'
        transcript_obj.save(update_fields=['processing_status','updated_at']) # Ensure updated_at is saved

        return {
            "transcript_id": transcript_obj.id, "language_code": lang_code,
            "keywords": extracted_keywords_texts, "embedding_generated": bool(embedding_vector),
            "embedding_stored": embedding_stored, "status": transcript_obj.processing_status
        }

    # Add logger property for easy logging within the class
    @property
    def logger(self):
        import logging
        return logging.getLogger(__name__)
