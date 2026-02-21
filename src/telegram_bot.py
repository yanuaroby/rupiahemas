"""
Telegram bot module for sending financial scripts.
Uses python-telegram-bot library.
"""

from typing import Optional

from telegram import Bot
from telegram.error import TelegramError

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramSender:
    """Send messages via Telegram Bot."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID

        if self.token:
            self.bot = Bot(token=self.token)
        else:
            self.bot = None

    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to the configured chat.

        Args:
            message: The message text to send
            parse_mode: Parse mode for formatting (Markdown or HTML)

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.token or not self.chat_id:
            print("Telegram bot token or chat ID not configured")
            print(f"Message would be: {message[:200]}...")
            return False

        if not self.bot:
            return False

        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
            )
            print(f"Message sent successfully to chat {self.chat_id}")
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending message: {e}")
            return False

    def send_rupiah_script(self, script: str) -> bool:
        """Send Rupiah script to Telegram."""
        return self.send_message(script)

    def send_gold_script(self, script: str) -> bool:
        """Send Gold script to Telegram."""
        return self.send_message(script)

    def test_connection(self) -> bool:
        """Test the Telegram bot connection."""
        if not self.bot:
            print("Bot not initialized (missing token)")
            return False

        try:
            # Get bot info to verify connection
            bot_info = self.bot.get_me()
            print(f"Connected to bot: @{bot_info.username}")
            return True
        except TelegramError as e:
            print(f"Telegram connection error: {e}")
            return False
