# backend/ai_agents/content_analysis_agent.py

from .transcript_analyzer import TranscriptAnalyzer
# from .visual_analyzer import VisualAnalyzer # We'll add this later

# backend/ai_agents/content_analysis_agent.py

class ContentAnalysisAgent:
    def __init__(self):
        self.transcript_analyzer = TranscriptAnalyzer()
        # VisualAnalyzer is still needed if CAAgent does any other light visual tasks,
        # but index_video_frames is a batch operation.
        self.visual_analyzer = VisualAnalyzer() 
        print("ContentAnalysisAgent initialized.")

    def analyze_video_content(self, video_source_obj, raw_video_data_item):
        """
        Primarily focuses on transcript analysis for live search context.
        Visual frame indexing is a separate batch process.
        """
        analysis_results = {}
        print(f"CAAgent: Analyzing text content for VideoSource ID {video_source_obj.id}")

        # --- Transcript Analysis ---
        try:
            transcript_analysis = self.transcript_analyzer.process_transcript_for_video_source(
                video_source_obj, raw_video_data_item
            )
            if transcript_analysis:
                analysis_results['transcript_analysis'] = transcript_analysis
        except Exception as e:
            print(f"CAAgent: Error transcript analysis VSID {video_source_obj.id}: {e}")
            analysis_results['transcript_error'] = str(e)
        
        # Visual frame INDEXING is NOT called here during a user search.
        # It's a separate batch process that populates the visual index.
        # The RARAgent will later QUERY this visual index.
        analysis_results['visual_frame_indexing_status'] = "Handled by batch process"

        return analysis_results
