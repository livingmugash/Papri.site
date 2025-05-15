# backend/ai_agents/visual_analyzer.py
import tensorflow as tf
from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image as keras_image
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess_input
import numpy as np
from PIL import Image as PILImage, UnidentifiedImageError
import imagehash
import os
import tempfile
import shutil 
import logging

from qdrant_client import QdrantClient, models as qdrant_models
from django.conf import settings
from django.utils import timezone

from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.frame_time_code import FrameTimecode

# Import Django model for saving at method level to avoid early load issues if any
# from api.models import VideoFrameFeature

logger = logging.getLogger(__name__)

class VisualAnalyzer:
    def __init__(self):
        logger.info("VisualAnalyzer: Initializing...")
        self.cnn_model_name = getattr(settings, 'VISUAL_CNN_MODEL_NAME', "ResNet50")
        self.target_size = (224, 224) # Default for ResNet50
        self.cnn_model = None
        self.cnn_embedding_dim = 0
        self.preprocess_input_func = None

        try:
            if self.cnn_model_name == "ResNet50":
                self.cnn_model = resnet50.ResNet50(weights='imagenet', include_top=False, pooling='avg')
                self.preprocess_input_func = resnet_preprocess_input
                self.cnn_embedding_dim = self.cnn_model.output_shape[-1]
            # Add elif for EfficientNetV2S or other models from settings
            # elif self.cnn_model_name == "EfficientNetV2S":
            #     from tensorflow.keras.applications import efficientnet_v2
            #     self.cnn_model = efficientnet_v2.EfficientNetV2S(weights='imagenet', include_top=False, pooling='avg')
            #     self.preprocess_input_func = efficientnet_v2.preprocess_input
            #     self.target_size = (384, 384) # Example, check model docs
            #     self.cnn_embedding_dim = self.cnn_model.output_shape[-1]
            else:
                logger.error(f"VA: Unsupported CNN model name configured: {self.cnn_model_name}")
                raise ValueError(f"Unsupported CNN model name: {self.cnn_model_name}")
            
            logger.info(f"VA: CNN model '{self.cnn_model_name}' loaded. Embedding dim: {self.cnn_embedding_dim}")
        except Exception as e:
            logger.error(f"VA: CRITICAL - Failed to load CNN model '{self.cnn_model_name}': {e}", exc_info=True)
            # Further execution requiring CNN model will fail gracefully

        self.qdrant_visual_collection_name = settings.QDRANT_COLLECTION_VISUAL
        self.qdrant_client = None
        if self.cnn_embedding_dim > 0: # Only attempt Qdrant setup if embedding model loaded
            try:
                self.qdrant_client = QdrantClient(
                    url=settings.QDRANT_URL, 
                    api_key=settings.QDRANT_API_KEY, 
                    timeout=20 
                )
                self.qdrant_client.health_check()
                logger.info(f"VA: Connected to Qdrant for visual collection '{self.qdrant_visual_collection_name}'.")
                self._ensure_qdrant_visual_collection_exists()
            except Exception as e:
                logger.error(f"VA: CRITICAL - Qdrant connection/collection setup failed for visual: {e}", exc_info=True)
                self.qdrant_client = None
        else:
            logger.warning("VA: CNN model not loaded, Qdrant client for visual not initialized.")
        logger.info("VisualAnalyzer initialized.")

    def _ensure_qdrant_visual_collection_exists(self):
        if not self.qdrant_client:
            logger.warning("VA: Qdrant client not available, cannot ensure visual collection.")
            return
        try:
            self.qdrant_client.get_collection(collection_name=self.qdrant_visual_collection_name)
            logger.info(f"VA: Qdrant visual collection '{self.qdrant_visual_collection_name}' already exists.")
        except Exception as e: # Catching generic exception as "not found" varies
            logger.info(f"VA: Visual collection '{self.qdrant_visual_collection_name}' may not exist or error checking ({type(e).__name__}). Attempting to create.")
            try:
                self.qdrant_client.recreate_collection(
                    collection_name=self.qdrant_visual_collection_name,
                    vectors_config=qdrant_models.VectorParams(size=self.cnn_embedding_dim, distance=qdrant_models.Distance.COSINE)
                )
                logger.info(f"VA: Qdrant visual collection '{self.qdrant_visual_collection_name}' created/recreated with dim {self.cnn_embedding_dim}.")
                # Payload indexes
                self.qdrant_client.create_payload_index(collection_name=self.qdrant_visual_collection_name, field_name="video_papri_id", field_schema=qdrant_models.PayloadSchemaType.INTEGER)
                self.qdrant_client.create_payload_index(collection_name=self.qdrant_visual_collection_name, field_name="timestamp_ms", field_schema=qdrant_models.PayloadSchemaType.INTEGER)
                logger.info(f"VA: Qdrant payload indexes created for visual collection.")
            except Exception as create_e:
                 logger.error(f"VA: Error CREATING Qdrant visual collection '{self.qdrant_visual_collection_name}': {create_e}", exc_info=True)

    def _load_and_preprocess_image(self, image_path_or_pil_image):
        if not self.cnn_model or not self.preprocess_input_func: return None
        try:
            if isinstance(image_path_or_pil_image, str):
                if not os.path.exists(image_path_or_pil_image): 
                    logger.warning(f"VA: Image path does not exist: {image_path_or_pil_image}"); return None
                img = keras_image.load_img(image_path_or_pil_image, target_size=self.target_size)
            elif isinstance(image_path_or_pil_image, PILImage.Image):
                img = image_path_or_pil_image.copy().resize(self.target_size) # Use copy to avoid modifying original
            else:
                logger.warning(f"VA: Invalid image input type: {type(image_path_or_pil_image)}"); return None
            
            img_array = keras_image.img_to_array(img)
            img_array_expanded = np.expand_dims(img_array, axis=0)
            return self.preprocess_input_func(img_array_expanded)
        except UnidentifiedImageError: # From PIL
            logger.error(f"VA: UnidentifiedImageError for image: {image_path_or_pil_image}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"VA: Error loading/preprocessing image '{image_path_or_pil_image}': {e}", exc_info=True)
            return None

    def extract_cnn_embedding_from_image(self, image_path_or_pil_image):
        if not self.cnn_model: return None
        processed_img = self._load_and_preprocess_image(image_path_or_pil_image)
        if processed_img is None: return None
        try:
            features = self.cnn_model.predict(processed_img, verbose=0)
            return features[0].tolist()
        except Exception as e:
            logger.error(f"VA: Error extracting CNN features: {e}", exc_info=True); return None

    def generate_perceptual_hash(self, image_path_or_pil_image, hash_size=8):
        try:
            if isinstance(image_path_or_pil_image, str):
                if not os.path.exists(image_path_or_pil_image): logger.warning(f"VA: Image path for hash does not exist: {image_path_or_pil_image}"); return None
                img = PILImage.open(image_path_or_pil_image)
            elif isinstance(image_path_or_pil_image, PILImage.Image):
                img = image_path_or_pil_image.copy() # Use copy
            else: logger.warning(f"VA: Invalid image type for hash: {type(image_path_or_pil_image)}"); return None

            phash_val = str(imagehash.phash(img.convert('L'), hash_size=hash_size))
            dhash_val = str(imagehash.dhash(img, hash_size=hash_size))
            return {"phash": phash_val, "dhash": dhash_val}
        except UnidentifiedImageError:
            logger.error(f"VA: UnidentifiedImageError for hashing image: {image_path_or_pil_image}", exc_info=True); return None
        except Exception as e:
            logger.error(f"VA: Error generating perceptual hash for '{image_path_or_pil_image}': {e}", exc_info=True); return None

    def process_query_image(self, image_path):
        # ... (Implementation from Step 22 - this method is primarily for query images) ...
        logger.info(f"VA: Processing query image: {image_path}")
        if not os.path.exists(image_path): logger.error(f"VA: Query image not found: {image_path}"); return None
        pil_img = None
        try: pil_img = PILImage.open(image_path)
        except Exception as e: logger.error(f"VA: Failed to open query image {image_path}: {e}"); return None
        
        cnn_embedding = self.extract_cnn_embedding_from_image(pil_img)
        hashes = self.generate_perceptual_hash(pil_img)
        if not cnn_embedding and not hashes: logger.warning(f"VA: No features extracted from query image {image_path}"); return None
        return {"cnn_embedding": cnn_embedding, "perceptual_hashes": hashes, "source_image_path": image_path}

    def _extract_key_frames_from_video(self, video_file_path, threshold=27.0, min_scene_len_frames=15, downscale_factor=1):
        # ... (Full implementation from Step 31, with robust error handling, FPS check, FrameTimecode, BGR->RGB conversion) ...
        logger.info(f"VA Keyframe: Starting for '{video_file_path}' (Thresh:{threshold}, MinLen:{min_scene_len_frames}, DScale:{downscale_factor})")
        keyframes_with_timestamps = []
        video_manager = None
        if not os.path.exists(video_file_path) or os.path.getsize(video_file_path) < 1024: # Check size too
            logger.error(f"VA Keyframe: Video file not found, empty or too small at '{video_file_path}'")
            return keyframes_with_timestamps
        try:
            video_manager = VideoManager([video_file_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len_frames))
            base_timecode = video_manager.get_base_timecode()
            if downscale_factor > 0 and isinstance(downscale_factor, int):
                res = video_manager.get_video_resolution()
                if res and res[1] > 480: video_manager.set_downscale_factor(downscale_factor)
            video_manager.start()
            fps = video_manager.get_framerate()
            if not fps or fps <= 0:
                logger.error(f"VA Keyframe: Invalid FPS ({fps}) for video '{video_file_path}'. Cannot process accurately.")
                # Attempt to sample a few frames even if FPS is bad, using frame numbers directly
                duration_frames = video_manager.get_duration()[0].get_frames()
                if duration_frames > 0:
                    num_samples = 3
                    for i in range(num_samples):
                        frame_num = int(duration_frames * (i + 1) / (num_samples + 1))
                        if video_manager.seek(frame_num) == 0:
                            frame_img_np = video_manager.read()
                            if frame_img_np is not False:
                                keyframes_with_timestamps.append((PILImage.fromarray(frame_img_np[:, :, ::-1].copy()), int(frame_num * 1000 / (fps or 25)) )) # Guess FPS if 0
                return keyframes_with_timestamps

            scene_manager.detect_scenes(frame_source=video_manager, show_progress=False)
            scene_list = scene_manager.get_scene_list(base_timecode)
            logger.info(f"VA Keyframe: Detected {len(scene_list)} scenes in '{os.path.basename(video_file_path)}'.")
            if not scene_list: # Sample frames if no scenes
                num_frames_if_no_scenes = 5
                duration_total_frames = video_manager.get_duration()[0].get_frames()
                if duration_total_frames > num_frames_if_no_scenes * max(1,min_scene_len_frames) : # Heuristic
                    interval = duration_total_frames // (num_frames_if_no_scenes + 1)
                    for i in range(1, num_frames_if_no_scenes + 1):
                        frame_num = i * interval
                        if frame_num >= duration_total_frames: break
                        if video_manager.seek(frame_num) == 0:
                            frame_img_np = video_manager.read();
                            if frame_img_np is not False: keyframes_with_timestamps.append((PILImage.fromarray(frame_img_np[:, :, ::-1].copy()), int(FrameTimecode(frame_num, base_timecode).get_seconds() * 1000)))
            else: # Scenes detected
                for i, (start_time, end_time) in enumerate(scene_list):
                    middle_frame_num = start_time.get_frames() + ((end_time.get_frames() - start_time.get_frames()) // 2)
                    if video_manager.seek(middle_frame_num) == 0:
                        frame_img_np = video_manager.read()
                        if frame_img_np is not False: keyframes_with_timestamps.append((PILImage.fromarray(frame_img_np[:, :, ::-1].copy()), int(FrameTimecode(middle_frame_num, base_timecode).get_seconds() * 1000)))
        except Exception as e: logger.error(f"VA Keyframe: Error for '{video_file_path}': {e}", exc_info=True)
        finally:
            if video_manager and video_manager.is_started(): video_manager.release()
        logger.info(f"VA Keyframe: Extracted {len(keyframes_with_timestamps)} keyframes for '{os.path.basename(video_file_path)}'.")
        return keyframes_with_timestamps

    def index_video_frames(self, video_source_obj, video_file_path):
        from api.models import VideoFrameFeature # Moved import here
        logger.info(f"VA IndexFrames: Processing VSID {video_source_obj.id} from path: {video_file_path}")
        
        if not video_file_path or not os.path.exists(video_file_path) or os.path.getsize(video_file_path) < 1024 :
            logger.error(f"VA IndexFrames: Video file path invalid, not found or empty: {video_file_path}")
            return {"indexed_frames_count": 0, "error": "Video file not found or empty."}
        if not self.qdrant_client or not self.cnn_model:
            logger.error("VA IndexFrames: Qdrant client or CNN model not available.")
            return {"indexed_frames_count": 0, "error": "Client or model not ready."}
        if not video_source_obj.video:
             logger.error(f"VA IndexFrames: VideoSource {video_source_obj.id} not linked to canonical Video.")
             return {"indexed_frames_count": 0, "error": "VideoSource not linked to Video."}


        min_scene_len_frames_calculated = 15 
        temp_vm_for_fps = None
        try: 
            temp_vm_for_fps = VideoManager([video_file_path]); temp_vm_for_fps.start()
            fps = temp_vm_for_fps.get_framerate()
            if fps and fps > 0: min_scene_len_frames_calculated = max(int(fps * 1.5), 25) # Min 1.5 sec scene, or 25 frames
            else: logger.warning(f"VA IndexFrames: Invalid FPS ({fps}) from video, using default min_scene_len.")
        except Exception as e: logger.warning(f"VA IndexFrames: Could not get FPS: {e}")
        finally:
            if temp_vm_for_fps and temp_vm_for_fps.is_started(): temp_vm_for_fps.release()
        
        keyframe_data = self._extract_key_frames_from_video(
            video_file_path, threshold=27.0, 
            min_scene_len_frames=min_scene_len_frames_calculated, 
            downscale_factor=1 
        )

        if not keyframe_data:
            logger.warning(f"VA IndexFrames: No keyframes extracted for VSID {video_source_obj.id}")
            return {"indexed_frames_count": 0, "error": "No keyframes extracted."}

        indexed_count = 0
        points_to_qdrant = []
        # Fetch existing VFF for this source to avoid re-processing/re-hitting DB for each frame if not needed
        existing_vff_timestamps = set(VideoFrameFeature.objects.filter(
            video_source=video_source_obj, 
            feature_type=self.cnn_model_name
            ).values_list('timestamp_in_video_ms', flat=True))

        for frame_pil_img, timestamp_ms in keyframe_data:
            if timestamp_ms in existing_vff_timestamps and not getattr(settings, 'FORCE_REINDEX_VISUAL', False): # Add a setting for force reindex
                # logger.debug(f"VA IndexFrames: Skipping already indexed frame at {timestamp_ms}ms for VSID {video_source_obj.id}")
                continue

            cnn_embedding = self.extract_cnn_embedding_from_image(frame_pil_img)
            hashes = self.generate_perceptual_hash(frame_pil_img)
            phash_val = hashes.get('phash') if hashes else None
            dhash_val = hashes.get('dhash') if hashes else None

            if not cnn_embedding and not phash_val: continue

            vff_obj, created = VideoFrameFeature.objects.update_or_create(
                video_source=video_source_obj, timestamp_in_video_ms=timestamp_ms,
                feature_type=self.cnn_model_name,
                defaults={
                    'hash_value': phash_val, 
                    'feature_data_json': {'dhash': dhash_val} if dhash_val else {},
                    'updated_at': timezone.now()
                }
            )
            
            if cnn_embedding and self.qdrant_client: # And if created or embedding needs update
                points_to_qdrant.append(
                    qdrant_models.PointStruct(
                        id=vff_obj.id, vector=cnn_embedding,
                        payload={ "video_papri_id": video_source_obj.video.id, "timestamp_ms": timestamp_ms, "phash": phash_val }
                    )
                )
            indexed_count +=1
            if indexed_count % 50 == 0 and points_to_qdrant: # Batch upsert to Qdrant every 50 points
                try:
                    self.qdrant_client.upsert_points(collection_name=self.qdrant_visual_collection_name, points=points_to_qdrant, wait=False)
                    logger.info(f"VA IndexFrames: Batched {len(points_to_qdrant)} frame embeddings to Qdrant for VSID {video_source_obj.id}.")
                    points_to_qdrant = [] # Clear batch
                except Exception as e: logger.error(f"VA IndexFrames: Error upserting Qdrant batch for VSID {video_source_obj.id}: {e}", exc_info=True)
        
        if points_to_qdrant and self.qdrant_client: # Upsert any remaining points
            try:
                self.qdrant_client.upsert_points(collection_name=self.qdrant_visual_collection_name, points=points_to_qdrant, wait=False)
                logger.info(f"VA IndexFrames: Upserted final batch {len(points_to_qdrant)} frame embeddings to Qdrant for VSID {video_source_obj.id}.")
            except Exception as e: logger.error(f"VA IndexFrames: Error upserting final Qdrant batch for VSID {video_source_obj.id}: {e}", exc_info=True)

        logger.info(f"VA IndexFrames: Processed {indexed_count} keyframes for VSID {video_source_obj.id}.")
        return {"indexed_frames_count": indexed_count}
