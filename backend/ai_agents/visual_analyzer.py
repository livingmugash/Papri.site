# backend/ai_agents/visual_analyzer.py
import tensorflow as tf
from tensorflow.keras.applications import resnet50 # Using ResNet50 as a common example
# from tensorflow.keras.applications import efficientnet_v2 # Or EfficientNetV2S if preferred and set up
from tensorflow.keras.preprocessing import image as keras_image
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess_input
# from tensorflow.keras.applications.efficientnet_v2 import preprocess_input as effnet_preprocess_input
import numpy as np
from PIL import Image as PILImage
import imagehash # For perceptual hashing
import os
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector # For scene change detection
from scenedetect.scene_manager import save_images # To save keyframes easily
import tempfile # To handle temporary image files from keyframes
from qdrant_client import QdrantClient, models as qdrant_models
from django.conf import settings


class VisualAnalyzer:
    def __init__(self):
        print("VisualAnalyzer: Initializing...")
        self.cnn_model_name = "ResNet50" # Or "EfficientNetV2S"
        self.target_size = (224, 224) # ResNet50 default input size

        try:
            if self.cnn_model_name == "ResNet50":
                # Using include_top=False to get features before classification layer
                # Pooling='avg' gives a fixed-size feature vector per image
                self.cnn_model = resnet50.ResNet50(weights='imagenet', include_top=False, pooling='avg')
                self.preprocess_input_func = resnet_preprocess_input
                self.cnn_embedding_dim = self.cnn_model.output_shape[-1] # Should be 2048 for ResNet50 with avg pooling
            # elif self.cnn_model_name == "EfficientNetV2S":
            #     self.cnn_model = efficientnet_v2.EfficientNetV2S(weights='imagenet', include_top=False, pooling='avg')
            #     self.preprocess_input_func = effnet_preprocess_input
            #     self.target_size = (384, 384) # Check EfficientNetV2S default input size
            #     self.cnn_embedding_dim = self.cnn_model.output_shape[-1]
            else:
                raise ValueError(f"Unsupported CNN model name: {self.cnn_model_name}")
            
            print(f"VisualAnalyzer: CNN model '{self.cnn_model_name}' loaded. Embedding dim: {self.cnn_embedding_dim}")
        except Exception as e:
            print(f"VisualAnalyzer: CRITICAL - Failed to load CNN model '{self.cnn_model_name}': {e}")
            self.cnn_model = None
            self.cnn_embedding_dim = 0
        
       # Qdrant setup for visual embeddings
        self.qdrant_visual_collection_name = settings.QDRANT_COLLECTION_VISUAL # New collection name
        self.qdrant_client = None
        if self.cnn_embedding_dim > 0: # Only if CNN model loaded
            try:
                self.qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY, timeout=10)
                self.qdrant_client.health_check()
                print(f"VisualAnalyzer: Connected to Qdrant for visual embeddings.")
                self._ensure_qdrant_visual_collection_exists() # Call method to create if not exists
            except Exception as e:
                print(f"VisualAnalyzer: CRITICAL - Qdrant connection/collection setup failed for visual: {e}")
                self.qdrant_client = None
        
        print("VisualAnalyzer initialized.")

    def _ensure_qdrant_visual_collection_exists(self):
        if not self.qdrant_client:
            print("VisualAnalyzer: Qdrant client not available for visual collection.")
            return
        try:
            try:
                self.qdrant_client.get_collection(collection_name=self.qdrant_visual_collection_name)
                print(f"Qdrant visual collection '{self.qdrant_visual_collection_name}' already exists.")
            except Exception: # Catching generic exception as "not found" varies
                print(f"VisualAnalyzer: Visual collection '{self.qdrant_visual_collection_name}' may not exist. Creating.")
                self.qdrant_client.recreate_collection(
                    collection_name=self.qdrant_visual_collection_name,
                    vectors_config=qdrant_models.VectorParams(size=self.cnn_embedding_dim, distance=qdrant_models.Distance.COSINE)
                )
                # Payload indexes for visual collection
                self.qdrant_client.create_payload_index(
                    collection_name=self.qdrant_visual_collection_name,
                    field_name="video_papri_id", # Canonical Video ID
                    field_schema=qdrant_models.PayloadSchemaType.INTEGER # Or KEYWORD if string UUIDs
                )
                self.qdrant_client.create_payload_index(
                    collection_name=self.qdrant_visual_collection_name,
                    field_name="timestamp_ms", # Timestamp of the frame
                    field_schema=qdrant_models.PayloadSchemaType.INTEGER
                )
                print(f"Qdrant visual collection '{self.qdrant_visual_collection_name}' created/ensured with payload indexes.")
        except Exception as e:
            print(f"VisualAnalyzer: Error ensuring Qdrant visual collection: {e}")

    # ... (_load_and_preprocess_image, extract_cnn_embedding_from_image, generate_perceptual_hash, process_query_image methods as before) ...

     def _store_frame_embedding_in_qdrant(self, video_frame_feature_django_id, video_papri_id, timestamp_ms, phash_value, embedding_vector):
        if not self.qdrant_client or not embedding_vector:
            print("VisualAnalyzer: Qdrant client not available or no visual embedding to store.")
            return False
        try:
            points_to_upsert = [
                qdrant_models.PointStruct(
                    id=video_frame_feature_django_id, # Use Django VideoFrameFeature.id
                    vector=embedding_vector,
                    payload={
                        "video_papri_id": video_papri_id,
                        "timestamp_ms": timestamp_ms,
                        "phash": phash_value # Store phash in payload for potential filtering/retrieval
                    }
                )
            ]
            self.qdrant_client.upsert_points(
                collection_name=self.qdrant_visual_collection_name,
                points=points_to_upsert,
                wait=True
            )
            # print(f"VA: Upserted frame embedding for VFF ID {video_frame_feature_django_id} into Qdrant.")
            return True
        except Exception as e:
            print(f"VisualAnalyzer: Error storing frame embedding in Qdrant for VFF ID {video_frame_feature_django_id}: {e}")
            return False



    def _load_and_preprocess_image(self, image_path_or_pil_image):
        if not self.cnn_model: return None
        try:
            if isinstance(image_path_or_pil_image, str): # If it's a path
                if not os.path.exists(image_path_or_pil_image):
                    print(f"VisualAnalyzer: Image path does not exist: {image_path_or_pil_image}")
                    return None
                img = keras_image.load_img(image_path_or_pil_image, target_size=self.target_size)
            elif isinstance(image_path_or_pil_image, PILImage.Image): # If it's already a PIL image
                img = image_path_or_pil_image.resize(self.target_size)
            else:
                print("VisualAnalyzer: Invalid image input type. Must be path or PIL.Image.")
                return None

            img_array = keras_image.img_to_array(img)
            img_array_expanded = np.expand_dims(img_array, axis=0)
            return self.preprocess_input_func(img_array_expanded)
        except Exception as e:
            print(f"VisualAnalyzer: Error loading/preprocessing image: {e}")
            return None

    def extract_cnn_embedding_from_image(self, image_path_or_pil_image):
        """Extracts a CNN-based feature vector from an image."""
        if not self.cnn_model:
            print("VisualAnalyzer: CNN model not loaded. Cannot extract embedding.")
            return None
        
        processed_img = self._load_and_preprocess_image(image_path_or_pil_image)
        if processed_img is None:
            return None
        
        try:
            features = self.cnn_model.predict(processed_img, verbose=0) # verbose=0 to silence progress bar
            return features[0].tolist() # [0] because predict returns a batch of features
        except Exception as e:
            print(f"VisualAnalyzer: Error extracting CNN features: {e}")
            return None

    def generate_perceptual_hash(self, image_path_or_pil_image, hash_size=8):
        """Generates a perceptual hash (pHash) for an image."""
        try:
            if isinstance(image_path_or_pil_image, str): # If it's a path
                if not os.path.exists(image_path_or_pil_image):
                    print(f"VisualAnalyzer: Image path does not exist for hashing: {image_path_or_pil_image}")
                    return None
                img = PILImage.open(image_path_or_pil_image)
            elif isinstance(image_path_or_pil_image, PILImage.Image): # If it's already a PIL image
                img = image_path_or_pil_image
            else:
                print("VisualAnalyzer: Invalid image input type for hashing. Must be path or PIL.Image.")
                return None

            # Convert to grayscale for pHash as it often works better
            phash_value = imagehash.phash(img.convert('L'), hash_size=hash_size)
            dhash_value = imagehash.dhash(img, hash_size=hash_size) # dHash can also be useful
            
            return {
                "phash": str(phash_value),
                "dhash": str(dhash_value)
                # You can add other hashes like ahash, whash if needed
            }
        except Exception as e:
            print(f"VisualAnalyzer: Error generating perceptual hash: {e}")
            return None

    def process_query_image(self, image_path):
        """Processes an uploaded query image to extract all relevant features."""
        if not os.path.exists(image_path):
            print(f"VisualAnalyzer: Query image path not found: {image_path}")
            return None
        
        print(f"VisualAnalyzer: Processing query image at path: {image_path}")
        pil_img = None
        try:
            pil_img = PILImage.open(image_path)
        except Exception as e:
            print(f"VisualAnalyzer: Could not open query image with PIL: {e}")
            return None

        cnn_embedding = self.extract_cnn_embedding_from_image(pil_img)
        hashes = self.generate_perceptual_hash(pil_img)

        if not cnn_embedding and not hashes:
            print(f"VisualAnalyzer: Failed to extract any features from query image: {image_path}")
            return None
            
        return {
            "cnn_embedding": cnn_embedding, # List of floats or None
            "perceptual_hashes": hashes,    # Dict of hashes or None
            "source_image_path": image_path # For reference
        }

    # --- Methods for Video Frame Indexing (to be called by CAAgent) ---
    # These are more complex and will be developed iteratively.

   def _extract_key_frames_from_video(self, video_file_path, threshold=27.0, min_scene_len=15, downscale_factor=0):
        """
        Uses PySceneDetect to find scene changes and extract keyframes (middle frame of each scene).
        Returns a list of tuples: (PIL.Image object for keyframe, timestamp_ms).
        
        video_file_path: Path to the video file.
        threshold: Threshold for ContentDetector (lower means more sensitive to changes).
        min_scene_len: Minimum length of a scene in frames.
        downscale_factor: Amount to downscale video during processing (0 for none, 1 for 50%, 2 for 25%, etc.).
                         Higher values speed up processing but reduce accuracy.
        """
        print(f"VisualAnalyzer: Extracting keyframes from video: {video_file_path} (threshold: {threshold})")
        keyframes_with_timestamps = []
        try:
            video_manager = VideoManager([video_file_path])
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_len))

            base_timecode = video_manager.get_base_timecode() # Important for correct timestamps

            if downscale_factor > 0:
                video_manager.set_downscale_factor(downscale_factor)
            
            video_manager.start() # Start video processing
            scene_manager.detect_scenes(frame_source=video_manager, show_progress=False) # show_progress=True for console progress
            scene_list = scene_manager.get_scene_list(base_timecode) 
            # scene_list contains tuples of (StartTimecode, EndTimecode)

            print(f"VisualAnalyzer: Detected {len(scene_list)} scenes in '{video_file_path}'.")

            if not scene_list: # Handle videos with no detectable scenes (or very short videos)
                # Get a frame from the middle of the video as a single keyframe
                duration_frames = video_manager.get_duration()[0].get_frames() # Total frames
                if duration_frames > 0:
                    middle_frame_num = duration_frames // 2
                    video_manager.seek(middle_frame_num)
                    frame_img_np = video_manager.read() # Reads the current frame as numpy array
                    if frame_img_np is not False: # Check if frame was read successfully
                        pil_img = PILImage.fromarray(frame_img_np)
                        timestamp_ms = int((middle_frame_num / video_manager.get_framerate()) * 1000)
                        keyframes_with_timestamps.append((pil_img, timestamp_ms))
                        print(f"VisualAnalyzer: No scenes detected, using middle frame {middle_frame_num} (ts: {timestamp_ms}ms) as keyframe.")
                else:
                    print(f"VisualAnalyzer: Video has 0 duration or could not read middle frame: {video_file_path}")


            # For each detected scene, extract the middle frame as a keyframe
            # PySceneDetect's save_images can also be used for more complex keyframe selection per scene
            # but getting the middle frame manually gives more control for direct PIL image use.
            for i, (start_time, end_time) in enumerate(scene_list):
                # Get middle frame number of the current scene
                middle_frame_num = start_time.get_frames() + ( (end_time.get_frames() - start_time.get_frames()) // 2 )
                
                video_manager.seek(middle_frame_num) # Seek to the frame
                frame_img_np = video_manager.read()  # Read the frame as a numpy array (BGR format usually)

                if frame_img_np is not False: # If frame was read successfully
                    # Convert BGR (OpenCV default) to RGB for PIL
                    frame_img_rgb_np = frame_img_np[:, :, ::-1].copy() # BGR to RGB
                    pil_img = PILImage.fromarray(frame_img_rgb_np)
                    timestamp_ms = int(middle_frame_num / video_manager.get_framerate() * 1000)
                    keyframes_with_timestamps.append((pil_img, timestamp_ms))
                    # print(f"  Scene {i+1}: Middle frame {middle_frame_num} extracted (Timestamp: {timestamp_ms}ms).")
                else:
                    print(f"  Scene {i+1}: Could not read middle frame {middle_frame_num}.")
            
            video_manager.release() # Release the video manager

        except Exception as e:
            print(f"VisualAnalyzer: Error during keyframe extraction for '{video_file_path}': {e}")
            if 'video_manager' in locals() and video_manager.is_started():
                video_manager.release()
        
        print(f"VisualAnalyzer: Extracted {len(keyframes_with_timestamps)} keyframes with timestamps for '{video_file_path}'.")
        return keyframes_with_timestamps

    def index_video_frames(self, video_source_obj, video_file_path): # Renamed param for clarity
        from api.models import VideoFrameFeature # Local import to avoid potential early app loading issues
        print(f"VisualAnalyzer: Starting frame indexing for VideoSource ID: {video_source_obj.id} from path: {video_file_path}")
        
        if not video_file_path or not os.path.exists(video_file_path):
            print(f"VisualAnalyzer: Video file path not provided or does not exist: {video_file_path}")
            return {"indexed_frames_count": 0, "error": "Video file not found."}

        if not self.qdrant_client or not self.cnn_model or not video_source_obj.video:
            print("VA: Qdrant client, CNN model, or linked PapriVideo not available for frame indexing.")
            return {"indexed_frames_count": 0, "error": "Client, model, or video link not ready."}

        # 1. Extract Keyframes
        # Adjust threshold and min_scene_len as needed. Lower threshold = more scenes.
        # Downscale factor can be increased for faster processing of long videos if some accuracy loss is acceptable.
        keyframe_pil_images_with_timestamps = self._extract_key_frames_from_video(
            video_file_path, threshold=27.0, min_scene_len=int(video_source_obj.video.duration_seconds * 0.05) if video_source_obj.video.duration_seconds else 15, downscale_factor=1 
        ) # Example: min scene 5% of video duration

        if not keyframe_pil_images_with_timestamps:
            print(f"VisualAnalyzer: No keyframes extracted for VideoSource ID: {video_source_obj.id}")
            return {"indexed_frames_count": 0, "error": "No keyframes extracted."}

        indexed_count = 0
        points_to_qdrant = []
        vff_objects_to_create = []

        for frame_pil_img, timestamp_ms in keyframe_pil_images_with_timestamps:
            cnn_embedding = self.extract_cnn_embedding_from_image(frame_pil_img)
            hashes = self.generate_perceptual_hash(frame_pil_img)
            phash_val = hashes.get('phash') if hashes else None
            dhash_val = hashes.get('dhash') if hashes else None

            if not cnn_embedding and not phash_val: # Skip if no useful features
                print(f"VA: No features extracted for frame at {timestamp_ms}ms for VSID {video_source_obj.id}")
                continue

            # Prepare VideoFrameFeature object for Django DB
            # We'll use bulk_create later for efficiency, so we prepare dicts or objects.
            # For update_or_create, we'd do it one by one or more complex bulk logic.
            # Let's assume for now we are creating new features or have a way to de-duplicate.
            
            # Check if this specific frame feature already exists to avoid duplicates
            existing_vff = VideoFrameFeature.objects.filter(
                video_source=video_source_obj,
                timestamp_in_video_ms=timestamp_ms,
                feature_type=self.cnn_model_name
            ).first()

            if existing_vff:
                # Update existing if necessary (e.g., if hash value changes, or re-generating embeddings)
                existing_vff.hash_value = phash_val
                existing_vff.feature_data_json = {'dhash': dhash_val} if dhash_val else existing_vff.feature_data_json
                existing_vff.save(update_fields=['hash_value', 'feature_data_json'])
                vff_obj_id = existing_vff.id
                print(f"VA: Updated existing VideoFrameFeature ID {vff_obj_id} for VSID {video_source_obj.id} at {timestamp_ms}ms.")
            else:
                vff_obj = VideoFrameFeature(
                    video_source=video_source_obj,
                    timestamp_in_video_ms=timestamp_ms,
                    feature_type=self.cnn_model_name,
                    hash_value=phash_val,
                    feature_data_json={'dhash': dhash_val} if dhash_val else None
                )
                vff_objects_to_create.append(vff_obj)
                # We need the ID for Qdrant, so if bulk_creating, this needs adjustment.
                # For now, let's save one by one to get ID for Qdrant, or handle ID assignment post bulk_create.
                # Simpler for now: save individually to get ID.
                # This is less efficient than bulk_create.
                try:
                    vff_obj.save()
                    vff_obj_id = vff_obj.id
                except Exception as db_e:
                    print(f"VA: Error saving VFF for VSID {video_source_obj.id} at {timestamp_ms}ms: {db_e}")
                    continue # Skip this frame if DB save fails
            
            if cnn_embedding and self.qdrant_client and vff_obj_id:
                points_to_qdrant.append(
                    qdrant_models.PointStruct(
                        id=vff_obj_id, 
                        vector=cnn_embedding,
                        payload={
                            "video_papri_id": video_source_obj.video.id,
                            "timestamp_ms": timestamp_ms,
                            "phash": phash_val 
                        }
                    )
                )
            indexed_count +=1
        
        # Bulk create remaining VFF objects if approach was changed
        # if vff_objects_to_create:
        #    VideoFrameFeature.objects.bulk_create(vff_objects_to_create)
        #    print(f"VA: Bulk created {len(vff_objects_to_create)} VFF objects.")
            # Then would need to fetch their IDs to add to Qdrant if not already handled.

        if points_to_qdrant and self.qdrant_client:
            try:
                self.qdrant_client.upsert_points(
                    collection_name=self.qdrant_visual_collection_name,
                    points=points_to_qdrant,
                    wait=False # Can be False for batch upserts for better performance
                )
                print(f"VisualAnalyzer: Batched {len(points_to_qdrant)} frame embeddings for upsert to Qdrant for VSID {video_source_obj.id}.")
            except Exception as e:
                print(f"VisualAnalyzer: Error upserting frame embeddings to Qdrant for VSID {video_source_obj.id}: {e}")

        print(f"VisualAnalyzer: Frame indexing processed for VSID {video_source_obj.id}. Attempted to index/update {indexed_count} keyframes.")
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
