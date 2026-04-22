# config.py

import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_key_here":
    raise ValueError(
        "[debate-bot] OPENROUTER_API_KEY is missing or still set to the placeholder. "
        "Set a real key in debate-bot/.env before running."
    )

OPENROUTER_MODEL   = "google/gemini-2.0-flash-001"
DEBATE_OUTPUT_DIR  = "debate-bot/outputs"
SHARED_DIR         = "shared"
VERDICT_FILE       = "shared/final_verdict.json"
