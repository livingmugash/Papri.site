# backend/ai_agents/utils.py

# Define constants for platform names
PLATFORM_YOUTUBE = "YouTube"
PLATFORM_VIMEO = "Vimeo"
PLATFORM_DAILYMOTION = "Dailymotion"
# Add more as we expand

# You might add other utility functions here later, e.g., for:
# - Normalizing text
# - Common API error handling patterns
# - Logging configurations specific to agents

def log_agent_activity(agent_name, message, level="INFO"):
    """Simple logger for agent activities."""
    print(f"[{level}] {agent_name}: {message}")
