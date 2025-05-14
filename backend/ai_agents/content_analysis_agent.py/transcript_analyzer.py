# backend/ai_agents/content_analysis_agent.py

from .transcript_analyzer import TranscriptAnalyzer
# from .visual_analyzer import VisualAnalyzer # We'll add this later

class ContentAnalysisAgent:
    def __init__(self):
        self.transcript_analyzer = TranscriptAnalyzer()
        # self.visual_analyzer = VisualAnalyzer()
        print("ContentAnalysisAgent initialized.")

    def analyze_video_content(self, video_source_obj, raw_video_data_item):
        """
        Analyzes content for a given video_source object.
        raw_video_data_item: The dictionary item fetched by SOIAgent for this source.
                             This might contain direct transcript or link to it.
        video_source_obj: The VideoSource model instance.
        """
        analysis_results = {}
        print(f"CAAgent: Analyzing content for VideoSource ID {video_source_obj.id} - {video_source_obj.original_url}")

        # --- 1. Transcript Analysis ---
        try:
            # The raw_video_data_item might already have transcript text or a link.
            # Or TranscriptAnalyzer might need to fetch it based on platform_name and video_id.
            transcript_analysis = self.transcript_analyzer.process_transcript_for_video_source(
                video_source_obj, 
                raw_video_data_item 
            )
            if transcript_analysis:
                analysis_results['transcript_analysis'] = transcript_analysis
                print(f"CAAgent: Transcript analysis completed for VideoSource ID {video_source_obj.id}. Keywords: {len(transcript_analysis.get('keywords', []))}")
            else:
                print(f"CAAgent: No transcript analysis data for VideoSource ID {video_source_obj.id}")

        except Exception as e:
            print(f"CAAgent: Error during transcript analysis for VideoSource ID {video_source_obj.id}: {e}")
            analysis_results['transcript_error'] = str(e)

        # --- 2. Visual Analysis (Placeholder for now) ---
        # visual_analysis_results = self.visual_analyzer.analyze_frames(video_source_obj)
        # analysis_results['visual_analysis'] = visual_analysis_results
        # print(f"CAAgent: Visual analysis completed for VideoSource ID {video_source_obj.id}")

        return analysis_results
