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
        # First try direct parameters, then fall back to config
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        
        # Debug print at initialization
        print(f"TelegramSender init: token={bool(self.token)}, chat_id={bool(self.chat_id)}")

        if self.token:
            self.bot = Bot(token=self.token)
            print(f"Bot initialized successfully")
        else:
            self.bot = None
            print("Bot NOT initialized - no token")

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to the configured chat.

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

        if not self.bot:
            print("ERROR: Bot not initialized")
            return False

        try:
            # Convert chat_id to string to handle both int and str
            chat_id_str = str(self.chat_id)
            
            print(f"Attempting to send message to chat: {chat_id_str}")
            print(f"Message length: {len(message)} characters")
            print(f"Parse mode: {parse_mode}")
            
            self.bot.send_message(
                chat_id=chat_id_str,
                text=message,
                parse_mode=parse_mode,
            )
            print(f"✓ Message sent successfully to chat {chat_id_str}")
            return True
        except TelegramError as e:
            print(f"✗ Telegram error: {e}")
            print(f"Error type: {type(e).__name__}")
            # Try fallback with no parse mode
            try:
                print("Trying fallback without parse mode...")
                self.bot.send_message(
                    chat_id=str(self.chat_id),
                    text=message.replace("*", "").replace("_", "").replace("[", "").replace("]", ""),
                )
                print("✓ Fallback succeeded")
                return True
            except Exception as fallback_error:
                print(f"✗ Fallback also failed: {fallback_error}")
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
