# config.py

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_key_here":
    raise ValueError(
        "[debate-bot] GEMINI_API_KEY is missing or still set to the placeholder. "
        "Set a real key in debate-bot/.env before running."
    )

GEMINI_MODEL       = "gemini-2.0-flash"
DEBATE_OUTPUT_DIR  = "debate-bot/outputs"
SHARED_DIR         = "shared"
VERDICT_FILE       = "shared/final_verdict.json"
