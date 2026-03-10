"""
Telegram bot module for sending financial scripts.
Uses httpx for synchronous HTTP requests to Telegram Bot API.
"""

from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramSender:
    """Send messages via Telegram Bot using httpx with retry logic."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        # First try direct parameters, then fall back to config
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

        # Debug print at initialization
        print(f"TelegramSender init: token={bool(self.token)}, chat_id={bool(self.chat_id)}")

        # Build the API URL
        if self.token:
            self.api_url = f"https://api.telegram.org/bot{self.token}"
            # Use httpx client with retry capability
            self.client = httpx.Client(timeout=30)
            print(f"Bot API URL initialized")
        else:
            self.api_url = None
            self.client = None
            print("Bot NOT initialized - no token")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to the configured chat using Telegram Bot API.

        Args:
            message: The message text to send
            parse_mode: Parse mode for formatting (Markdown or HTML)

        Returns:
            True if message was sent successfully, False otherwise
        """
        # Debug: Print if token/chat_id exist (without showing values)
        token_set = bool(self.token)
        chat_id_set = bool(self.chat_id)
        print(f"DEBUG: Token configured: {token_set}, Chat ID configured: {chat_id_set}")
        print(f"DEBUG: Token type: {type(self.token)}, Chat ID type: {type(self.chat_id)}")
        print(f"DEBUG: Chat ID value: {self.chat_id}")

        if not self.token:
            print("ERROR: Telegram bot token is empty or not set")
            print("Check that TELEGRAM_BOT_TOKEN secret is configured in GitHub")
            return False

        if not self.chat_id:
            print("ERROR: Telegram chat ID is empty or not set")
            print("Check that TELEGRAM_CHAT_ID secret is configured in GitHub")
            return False

        if not self.api_url:
            print("ERROR: Bot API URL not initialized")
            return False

        try:
            # Use Telegram Bot API directly with httpx
            url = f"{self.api_url}/sendMessage"
            chat_id_str = str(self.chat_id)

            print(f"Attempting to send message to chat: {chat_id_str}")
            print(f"Message length: {len(message)} characters")
            print(f"Parse mode: {parse_mode}")

            payload = {
                "chat_id": chat_id_str,
                "text": message,
                "parse_mode": parse_mode
            }

            response = self.client.post(url, json=payload)
            result = response.json()

            if result.get("ok"):
                print(f"✓ Message sent successfully to chat {chat_id_str}")
                print(f"Telegram API response: {result}")
                return True
            else:
                print(f"✗ Telegram API error: {result}")
                # Try fallback without parse mode
                print("Trying fallback without parse mode...")
                payload["parse_mode"] = None
                payload["text"] = message.replace("*", "").replace("_", "").replace("[", "").replace("]", "").replace("<", "").replace(">", "")
                response = self.client.post(url, json=payload)
                result = response.json()
                if result.get("ok"):
                    print("✓ Fallback succeeded")
                    return True
                else:
                    print(f"✗ Fallback also failed: {result}")
                return False

        except httpx.HTTPError as e:
            print(f"✗ Network error: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error sending message: {e}")
            print(f"Error type: {type(e).__name__}")
            return False

    def send_rupiah_script(self, script: str) -> bool:
        """Send Rupiah script to Telegram."""
        return self.send_message(script)

    def send_gold_script(self, script: str) -> bool:
        """Send Gold script to Telegram."""
        return self.send_message(script)
