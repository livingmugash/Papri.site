
# backend/ai_agents/content_analysis_agent.py
from .transcript_analyzer import TranscriptAnalyzer
from .visual_analyzer import VisualAnalyzer # Add this

class ContentAnalysisAgent:
    def __init__(self):
        self.transcript_analyzer = TranscriptAnalyzer()
        self.visual_analyzer = VisualAnalyzer() # Instantiate
        print("ContentAnalysisAgent initialized.")

    def analyze_video_content(self, video_source_obj, raw_video_data_item):
        analysis_results = {}
        print(f"CAAgent: Analyzing content for VideoSource ID {video_source_obj.id} - {video_source_obj.original_url}")

        # --- 1. Transcript Analysis ---
        # ... (as before) ...
        try:
            transcript_analysis = self.transcript_analyzer.process_transcript_for_video_source(video_source_obj, raw_video_data_item)
            if transcript_analysis: analysis_results['transcript_analysis'] = transcript_analysis
        except Exception as e:
            print(f"CAAgent: Error transcript analysis VSID {video_source_obj.id}: {e}"); analysis_results['transcript_error'] = str(e)


        # --- 2. Visual Frame Indexing (Called here, but actual processing is STUBBED in VisualAnalyzer) ---
        # This step is about indexing frames from the video source, not analyzing a query image.
        # It needs access to the video file/stream, which is a complex part.
        # For now, we'll call it, and it will use its internal stubs/simulations.
        if video_source_obj.video: # Ensure canonical video exists
            try:
                # How do we get video_file_path_or_stream here?
                # SOIAgent might download videos temporarily for analysis, or provide a stream URL.
                # This is a major architectural decision/challenge.
                # For now, pass None to trigger VisualAnalyzer's simulation.
                video_path_for_analysis = None # Placeholder - this needs to be the actual video path/URL
                
                # This call is for INDEXING video frames, not for searching a query image.
                # We might only do this for newly added videos or on a schedule.
                # Let's assume for now it's part of the initial processing if video_path_for_analysis is available.
                if video_path_for_analysis: # Only if we actually have the video
                    visual_frame_indexing_results = self.visual_analyzer.index_video_frames(
                        video_source_obj,
                        video_path_for_analysis
                    )
                    analysis_results['visual_frame_indexing'] = visual_frame_indexing_results
                    print(f"CAAgent: Visual frame indexing process called for VSID {video_source_obj.id}. Result: {visual_frame_indexing_results}")
                else:
                    print(f"CAAgent: No video path for visual frame indexing of VSID {video_source_obj.id}. Skipping.")
                    analysis_results['visual_frame_indexing'] = {"status": "skipped_no_video_path"}


            except Exception as e:
                print(f"CAAgent: Error during visual frame indexing for VSID {video_source_obj.id}: {e}")
                analysis_results['visual_frame_indexing_error'] = str(e)
        else:
            print(f"CAAgent: VideoSource {video_source_obj.id} not linked to canonical Video. Skipping visual frame indexing.")


        return analysis_results
