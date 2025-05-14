# backend/api/analyzer_instances.py
# This file helps manage singleton instances of heavy objects for Celery tasks.
from backend.ai_agents.visual_analyzer import VisualAnalyzer
# from backend.ai_agents.transcript_analyzer import TranscriptAnalyzer # If needed similarly

# Instantiate once when the Celery worker process starts.
visual_analyzer_instance = VisualAnalyzer()
# transcript_analyzer_instance = TranscriptAnalyzer()

print("Analyzer instances initialized.")
