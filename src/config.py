"""
Configuration module for the BloombergTechnoz Financial Script Bot.
Loads environment variables and defines constants.
"""

import os
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file (for local development)
load_dotenv()

# API Keys - read from environment variables (works for both local and GitHub Actions)
# GitHub Actions secrets are automatically set as environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Base URL for BloombergTechnoz
BASE_URL = "https://www.bloombergtechnoz.com"

# Search keywords
RUPIAH_KEYWORD = "rupiah"
GOLD_KEYWORDS = ["antam", "emas"]  # Try antam first, then emas as fallback

# Timezone configuration
WIB_TIMEZONE = pytz.timezone("Asia/Jakarta")
UTC_TIMEZONE = pytz.utc

# Groq model configuration
GROQ_MODEL = "llama-3.1-70b-versatile"

# Request headers for scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# Request timeout
REQUEST_TIMEOUT = 30
