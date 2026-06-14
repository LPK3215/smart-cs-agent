import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek API (OpenAI-compatible)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "smart_cs.db"))

# Agent settings
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))           # Max ReAct loops
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.4"))
MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW", "8"))             # Recent messages kept in full
SUMMARY_THRESHOLD = int(os.getenv("SUMMARY_THRESHOLD", "16"))    # When to trigger summarization

# Guardrails
MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "1000"))    # Max user input chars
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "20")) # Per session
TOOL_TIMEOUT_SEC = int(os.getenv("TOOL_TIMEOUT_SEC", "30"))      # Tool execution timeout

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173").split(",")
