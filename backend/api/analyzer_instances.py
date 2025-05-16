# backend/api/analyzer_instances.py
from backend.ai_agents.visual_analyzer import VisualAnalyzer
from backend.ai_agents.transcript_analyzer import TranscriptAnalyzer
import logging

logger = logging.getLogger(__name__)

try:
    visual_analyzer_instance = VisualAnalyzer()
    logger.info("Successfully initialized visual_analyzer_instance.")
except Exception as e:
    visual_analyzer_instance = None
    logger.error(f"Failed to initialize visual_analyzer_instance: {e}", exc_info=True)

try:
    transcript_analyzer_instance = TranscriptAnalyzer()
    logger.info("Successfully initialized transcript_analyzer_instance.")
except Exception as e:
    transcript_analyzer_instance = None
    logger.error(f"Failed to initialize transcript_analyzer_instance: {e}", exc_info=True)

# This ensures that even if one fails, the worker might still start and other tasks can run.
# The tasks themselves should check if the instance is None.
