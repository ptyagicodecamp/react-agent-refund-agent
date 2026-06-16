from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL_ID = os.getenv("MODEL_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_LLM = os.getenv("USE_LLM", "0") == "1"
