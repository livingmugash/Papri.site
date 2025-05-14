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

# Qdrant Client (will be needed for storing/searching frame embeddings later)
# from qdrant_client import QdrantClient, models as qdrant_models
# from django.conf import settings


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

    def extract_key_frames_from_video(self, video_file_path, threshold=30.0):
        """
        Uses PySceneDetect to find scene changes and extract keyframes.
        Returns a list of PIL.Image objects for keyframes.
        This is a STUB and needs scenedetect library and proper implementation.
        """
        print(f"VisualAnalyzer: STUB - Extracting keyframes from video: {video_file_path} (threshold: {threshold})")
        # TODO: Implement using PySceneDetect
        # from scenedetect import VideoManager, SceneManager
        # from scenedetect.detectors import ContentDetector
        # video_manager = VideoManager([video_file_path])
        # scene_manager = SceneManager()
        # scene_manager.add_detector(ContentDetector(threshold=threshold))
        # video_manager.set_downscale_factor(1) # Process at full res or downscale
        # video_manager.start()
        # scene_manager.detect_scenes(frame_source=video_manager)
        # scene_list = scene_manager.get_scene_list() # List of (StartTimecode, EndTimecode)
        # keyframes_pil_images = []
        # for i, scene in enumerate(scene_list):
        #     # Get middle frame of the scene, or first frame
        #     # frame_img = video_manager.get_frame_image(scene[0] + (scene[1]-scene[0])/2) # Or scene[0]
        #     # keyframes_pil_images.append(PILImage.fromarray(frame_img))
        # video_manager.release()
        return [] # Return empty list for now

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
