import tensorflow as tf
from tensorflow.keras.applications import resnet50
from tensorflow.keras.preprocessing import image as keras_image
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess_input
import numpy as np
from PIL import Image as PILImage
import imagehash
import os
import tempfile
import shutil # For robust temp file cleanup if needed, though TemporaryDirectory handles it.
from qdrant_client import QdrantClient, models as qdrant_models
from django.conf import settings
from django.utils import timezone
# PySceneDetect imports
from scenedetect import VideoManager, SceneManager, StatsManager
from scenedetect.detectors import ContentDetector
from scenedetect.frame_time_code import FrameTimecode
from api.models import VideoFrameFeature # Can be imported inside methods


class VisualAnalyzer:
    def __init__(self):
        print("VisualAnalyzer: Initializing...")
        self.cnn_model_name = "ResNet50" 
        self.target_size = (224, 224) 
        self.cnn_model = None; self.cnn_embedding_dim = 0
        try:
            if self.cnn_model_name == "ResNet50":
                self.cnn_model = resnet50.ResNet50(weights='imagenet', include_top=False, pooling='avg')
                self.preprocess_input_func = resnet_preprocess_input
                self.cnn_embedding_dim = self.cnn_model.output_shape[-1]
            print(f"VA: CNN model '{self.cnn_model_name}' loaded. Dim: {self.cnn_embedding_dim}")
        except Exception as e:
            print(f"VA: CRITICAL - Failed to load CNN model: {e}")

        self.qdrant_visual_collection_name = settings.QDRANT_COLLECTION_VISUAL
        self.qdrant_client = None
        if self.cnn_embedding_dim > 0:
            try:
                self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=20)
                self.qdrant_client.health_check()
                print(f"VA: Connected to Qdrant for visual collection '{self.qdrant_visual_collection_name}'.")
                self._ensure_qdrant_visual_collection_exists()
            except Exception as e:
                print(f"VA: CRITICAL - Qdrant connection/collection setup failed for visual: {e}")
                self.qdrant_client = None
        else:
            print("VA: CNN model not loaded, Qdrant client for visual not initialized.")
        print("VisualAnalyzer initialized.")

    def _ensure_qdrant_visual_collection_exists(self):
        # ... (Implementation from Step 23, ensuring collection for self.cnn_embedding_dim exists)
        if not self.qdrant_client: return
        try:
            try: self.qdrant_client.get_collection(collection_name=self.qdrant_visual_collection_name)
            except Exception: # If get_collection fails (e.g. not found)
                self.qdrant_client.recreate_collection(
                    collection_name=self.qdrant_visual_collection_name,
                    vectors_config=qdrant_models.VectorParams(size=self.cnn_embedding_dim, distance=qdrant_models.Distance.COSINE)
                )
                self.qdrant_client.create_payload_index(collection_name=self.qdrant_visual_collection_name, field_name="video_papri_id", field_schema=qdrant_models.PayloadSchemaType.INTEGER)
                self.qdrant_client.create_payload_index(collection_name=self.qdrant_visual_collection_name, field_name="timestamp_ms", field_schema=qdrant_models.PayloadSchemaType.INTEGER)
                print(f"VA: Qdrant visual collection '{self.qdrant_visual_collection_name}' created/ensured.")
        except Exception as e: print(f"VA: Error ensuring Qdrant visual collection: {e}")


    def _load_and_preprocess_image(self, image_path_or_pil_image):
        # ... (Implementation from Step 22, ensuring self.preprocess_input_func is used) ...
        if not self.cnn_model: return None
        try:
            if isinstance(image_path_or_pil_image, str):
                img = keras_image.load_img(image_path_or_pil_image, target_size=self.target_size)
            elif isinstance(image_path_or_pil_image, PILImage.Image):
                img = image_path_or_pil_image.resize(self.target_size)
            else: return None
            img_array = keras_image.img_to_array(img)
            return self.preprocess_input_func(np.expand_dims(img_array, axis=0))
        except Exception as e: print(f"VA: Error loading/preproc image: {e}"); return None


    def extract_cnn_embedding_from_image(self, image_path_or_pil_image):
        # ... (Implementation from Step 22) ...
        if not self.cnn_model: return None
        processed_img = self._load_and_preprocess_image(image_path_or_pil_image)
        if processed_img is None: return None
        try:
            features = self.cnn_model.predict(processed_img, verbose=0)
            return features[0].tolist()
        except Exception as e: print(f"VA: Error extracting CNN features: {e}"); return None

    def generate_perceptual_hash(self, image_path_or_pil_image, hash_size=8):
        # ... (Implementation from Step 22) ...
        try:
            if isinstance(image_path_or_pil_image, str): img = PILImage.open(image_path_or_pil_image)
            elif isinstance(image_path_or_pil_image, PILImage.Image): img = image_path_or_pil_image
            else: return None
            return {"phash": str(imagehash.phash(img.convert('L'), hash_size=hash_size)),
                    "dhash": str(imagehash.dhash(img, hash_size=hash_size))}
        except Exception as e: print(f"VA: Error generating pHash: {e}"); return None


    def process_query_image(self, image_path):
        # ... (Implementation from Step 22) ...
        if not os.path.exists(image_path): return None
        try: pil_img = PILImage.open(image_path)
        except Exception as e: print(f"VA: Could not open query image {image_path}: {e}"); return None
        cnn_embedding = self.extract_cnn_embedding_from_image(pil_img)
        hashes = self.generate_perceptual_hash(pil_img)
        if not cnn_embedding and not hashes: return None
        return {"cnn_embedding": cnn_embedding, "perceptual_hashes": hashes, "source_image_path": image_path}


    def _extract_key_frames_from_video(self, video_file_path, threshold=27.0, min_scene_len_frames=15, downscale_factor=1):
        print(f"VA Keyframe: Starting for '{video_file_path}' (Thresh:{threshold}, MinLen:{min_scene_len_frames}, DScale:{downscale_factor})")
        keyframes_with_timestamps = []
        video_manager = None
        stats_manager = None # Initialize
        stats_file_path = None # Initialize

        if not os.path.exists(video_file_path):
            print(f"VA Keyframe: Video file not found at '{video_file_path}'")
            return keyframes_with_timestamps

        try:
            # Using a temporary file for stats can be problematic with permissions or cleanup if process crashes.
            # For robustness, can be omitted or path carefully managed.
            # stats_file_path = os.path.join(tempfile.gettempdir(), f"{os.path.basename(video_file_path)}.stats.csv")
            # stats_manager = StatsManager(stats_file_path=stats_file_path, save_on_shutdown=False) # Don't save on shutdown, we'll manage.
            
            video_manager = VideoManager([video_file_path]) # No stats_manager for simplicity for now
            scene_manager = SceneManager() # No stats_manager passed here
            scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len_frames))
            base_timecode = video_manager.get_base_timecode()

            if downscale_factor > 0 and isinstance(downscale_factor, int):
                video_manager.set_downscale_factor(downscale_factor)
            
            video_manager.start()
            fps = video_manager.get_framerate()
            if not fps or fps <= 0: # Safety check for invalid FPS
                print(f"VA Keyframe: Invalid FPS ({fps}) for video '{video_file_path}'. Cannot process.")
                return keyframes_with_timestamps
                
            print(f"VA Keyframe: Video '{os.path.basename(video_file_path)}' opened. Duration: {base_timecode + video_manager.get_duration()[0]}, FPS: {fps}")

            scene_manager.detect_scenes(frame_source=video_manager, show_progress=False)
            scene_list = scene_manager.get_scene_list(base_timecode) # Get scenes relative to base_timecode
            
            print(f"VA Keyframe: Detected {len(scene_list)} scenes.")

            if not scene_list: # If no scenes, take a few frames spread across the video
                num_frames_if_no_scenes = 5 # How many frames to sample
                duration_total_frames = video_manager.get_duration()[0].get_frames()
                if duration_total_frames > 0:
                    interval = max(1, duration_total_frames // (num_frames_if_no_scenes + 1))
                    for i in range(1, num_frames_if_no_scenes + 1):
                        frame_num = i * interval
                        if frame_num >= duration_total_frames: break # Don't go past end
                        if video_manager.seek(frame_num) == 0:
                            frame_img_np = video_manager.read()
                            if frame_img_np is not False:
                                pil_img = PILImage.fromarray(frame_img_np[:, :, ::-1].copy())
                                timestamp_ms = int(FrameTimecode(frame_num, base_timecode).get_seconds() * 1000)
                                keyframes_with_timestamps.append((pil_img, timestamp_ms))
                    print(f"VA Keyframe: No scenes, sampled {len(keyframes_with_timestamps)} frames.")
            else:
                for i, (start_time, end_time) in enumerate(scene_list):
                    # Get middle frame of the current scene
                    middle_frame_number = start_time.get_frames() + ((end_time.get_frames() - start_time.get_frames()) // 2)
                    if video_manager.seek(middle_frame_number) == 0:
                        frame_img_np = video_manager.read()
                        if frame_img_np is not False:
                            pil_img = PILImage.fromarray(frame_img_np[:, :, ::-1].copy())
                            timestamp_ms = int(FrameTimecode(middle_frame_number, base_timecode).get_seconds() * 1000)
                            keyframes_with_timestamps.append((pil_img, timestamp_ms))
                        # else: print(f"  VA Keyframe: Scene {i+1}, Failed to read frame {middle_frame_number}.") # Too verbose
                    # else: print(f"  VA Keyframe: Scene {i+1}, Failed to seek to frame {middle_frame_number}.") # Too verbose
            
        except Exception as e:
            print(f"VA Keyframe: Error during keyframe extraction for '{video_file_path}': {type(e).__name__} - {e}")
        finally:
            if video_manager and video_manager.is_started():
                video_manager.release()
            # if stats_manager: stats_manager.save_to_csv() # Save if needed
            # if stats_file_path and os.path.exists(stats_file_path):
            #     try: os.remove(stats_file_path)
            #     except OSError: pass

        print(f"VA Keyframe: Extracted {len(keyframes_with_timestamps)} keyframes with timestamps for '{os.path.basename(video_file_path)}'.")
        return keyframes_with_timestamps


    def index_video_frames(self, video_source_obj, video_file_path):
        from api.models import VideoFrameFeature # Moved import here
        print(f"VA IndexFrames: Processing VSID {video_source_obj.id} ({video_source_obj.original_url}) from path: {video_file_path}")
        
        if not video_file_path or not os.path.exists(video_file_path):
            return {"indexed_frames_count": 0, "error": "Video file not found."}
        if not self.qdrant_client or not self.cnn_model or not video_source_obj.video:
            return {"indexed_frames_count": 0, "error": "Client, model, or canonical Video link not ready."}

        temp_vm_for_fps = None
        min_scene_len_frames_calculated = 15 # Default
        try: # Get FPS to calculate min_scene_len in frames
            temp_vm_for_fps = VideoManager([video_file_path])
            temp_vm_for_fps.start()
            fps = temp_vm_for_fps.get_framerate()
            if fps and fps > 0: min_scene_len_frames_calculated = max(int(fps * 1.0), 15) # Min 1 sec scene, or 15 frames
        except Exception as e: print(f"VA IndexFrames: Warn - Could not get FPS: {e}")
        finally:
            if temp_vm_for_fps and temp_vm_for_fps.is_started(): temp_vm_for_fps.release()
        
        keyframe_data = self._extract_key_frames_from_video(
            video_file_path, threshold=27.0, 
            min_scene_len_frames=min_scene_len_frames_calculated, 
            downscale_factor=1 # Downscale by 50%
        )

        if not keyframe_data: return {"indexed_frames_count": 0, "error": "No keyframes extracted."}

        indexed_count = 0
        points_to_qdrant = []
        processed_vff_ids_for_qdrant = [] # To avoid duplicate PointStructs if loop has issues

        for frame_pil_img, timestamp_ms in keyframe_data:
            cnn_embedding = self.extract_cnn_embedding_from_image(frame_pil_img)
            hashes = self.generate_perceptual_hash(frame_pil_img)
            phash_val = hashes.get('phash') if hashes else None
            dhash_val = hashes.get('dhash') if hashes else None

            if not cnn_embedding and not phash_val: continue

            vff_obj, created = VideoFrameFeature.objects.update_or_create(
                video_source=video_source_obj, timestamp_in_video_ms=timestamp_ms,
                feature_type=self.cnn_model_name, # Assuming CNN is primary feature type stored
                defaults={
                    'hash_value': phash_val, 
                    'feature_data_json': {'dhash': dhash_val} if dhash_val else {},
                    'updated_at': timezone.now()
                }
            )
            
            if cnn_embedding and self.qdrant_client and vff_obj.id not in processed_vff_ids_for_qdrant:
                points_to_qdrant.append(
                    qdrant_models.PointStruct(
                        id=vff_obj.id, vector=cnn_embedding,
                        payload={
                            "video_papri_id": video_source_obj.video.id,
                            "timestamp_ms": timestamp_ms,
                            "phash": phash_val 
                        }
                    )
                )
                processed_vff_ids_for_qdrant.append(vff_obj.id)
            indexed_count +=1
        
        if points_to_qdrant and self.qdrant_client:
            try:
                self.qdrant_client.upsert_points(
                    collection_name=self.qdrant_visual_collection_name,
                    points=points_to_qdrant, wait=True # Wait True for batch to ensure it's processed or errors
                )
                print(f"VA IndexFrames: Upserted {len(points_to_qdrant)} frame embeddings to Qdrant for VSID {video_source_obj.id}.")
            except Exception as e:
                print(f"VA IndexFrames: Error upserting frame embeddings batch to Qdrant for VSID {video_source_obj.id}: {e}")

        print(f"VA IndexFrames: Processed {indexed_count} keyframes for VSID {video_source_obj.id}.")
        return {"indexed_frames_count": indexed_count}


    def index_video_frames(self, video_source_obj, video_file_path_or_stream):
        """
        Orchestrates keyframe extraction, feature extraction, and storage for a video.
        """
        print(f"VisualAnalyzer: STUB - Starting frame indexing for VideoSource ID: {video_source_obj.id}")
        if not self.qdrant_client or not self.cnn_model:
            print("VisualAnalyzer: Qdrant client or CNN model not available for frame indexing.")
            return {"indexed_frames_count": 0, "error": "Client or model not ready."}

        # 1. Extract Keyframes (using PySceneDetect - STUBBED)
        # keyframe_pil_images = self.extract_key_frames_from_video(video_file_path_or_stream)
        # For testing, let's simulate a few dummy "keyframes" if no actual extraction
        # This part would be replaced by actual frame images from PySceneDetect
        if not video_file_path_or_stream: # Simulate if no path
            keyframe_pil_images = [PILImage.new('RGB', (100,100), color='red'), PILImage.new('RGB', (100,100), color='blue')]
            simulated_timestamps_ms = [1000, 5000] # Dummy timestamps
            print(f"VisualAnalyzer: Using {len(keyframe_pil_images)} SIMULATED keyframes for VideoSource ID: {video_source_obj.id}")
        else:
            # Actual keyframe extraction to be implemented here
            keyframe_pil_images = [] # Replace with actual call
            simulated_timestamps_ms = []
            print(f"VisualAnalyzer: Actual keyframe extraction from '{video_file_path_or_stream}' TBD.")


        # 2. For each keyframe, extract features and store them
        # from api.models import VideoFrameFeature # Moved import to top

        indexed_count = 0
        points_to_qdrant = []

        for i, frame_pil_img in enumerate(keyframe_pil_images):
            timestamp_ms = simulated_timestamps_ms[i] # Replace with actual timestamp from PySceneDetect

            cnn_embedding = self.extract_cnn_embedding_from_image(frame_pil_img)
            hashes = self.generate_perceptual_hash(frame_pil_img)

            if not cnn_embedding and not hashes:
                continue # Skip if no features extracted

            # Save metadata to Django DB (VideoFrameFeature)
            vff_obj, created = VideoFrameFeature.objects.update_or_create(
                video_source=video_source_obj,
                timestamp_in_video_ms=timestamp_ms,
                feature_type=self.cnn_model_name, # Primary feature type
                defaults={
                    'hash_value': hashes.get('phash') if hashes else None, # Store phash
                    'feature_data_json': {'dhash': hashes.get('dhash')} if hashes else None,
                    # 'vector_db_id' will be the Qdrant point ID (which is vff_obj.id)
                }
            )
            
            # Store CNN embedding in Qdrant if extracted
            if cnn_embedding and self.qdrant_client:
                points_to_qdrant.append(
                    qdrant_models.PointStruct(
                        id=vff_obj.id, # Use Django VideoFrameFeature.id as Qdrant point ID
                        vector=cnn_embedding,
                        payload={
                            "video_frame_feature_django_id": vff_obj.id, # Explicitly store
                            "video_papri_id": video_source_obj.video.id,
                            "timestamp_ms": timestamp_ms,
                            "phash": hashes.get('phash') if hashes else None
                        }
                    )
                )
            indexed_count +=1
        
        if points_to_qdrant and self.qdrant_client:
            try:
                self.qdrant_client.upsert_points(
                    collection_name=self.qdrant_visual_collection_name,
                    points=points_to_qdrant,
                    wait=True
                )
                print(f"VisualAnalyzer: Upserted {len(points_to_qdrant)} frame embeddings to Qdrant for VSID {video_source_obj.id}.")
            except Exception as e:
                print(f"VisualAnalyzer: Error upserting frame embeddings to Qdrant for VSID {video_source_obj.id}: {e}")

        print(f"VisualAnalyzer: Frame indexing complete for VideoSource ID {video_source_obj.id}. Indexed keyframes: {indexed_count}")
        return {"indexed_frames_count": indexed_count}
