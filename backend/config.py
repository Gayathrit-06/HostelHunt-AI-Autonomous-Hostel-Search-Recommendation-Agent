import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GPLACES_API_KEY = os.getenv("GPLACES_API_KEY")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Active free model with tool-calling support on OpenRouter
DEFAULT_MODEL = "minimax/minimax-m3:free"
# Alternative fallback option:
# DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"

def validate_config():
    """Validates that required API keys are present."""
    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not GPLACES_API_KEY:
        missing.append("GPLACES_API_KEY")
    
    if missing:
        raise ValueError(f"Missing required environment variables in .env: {', '.join(missing)}")