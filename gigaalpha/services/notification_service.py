import os
import logging
import socket
from gigaalpha.helpers.telegram import TelegramBot

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Refined Notification Service focused on success summaries.
    """
    def __init__(self):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        self.bot = None
        if token and chat_id:
            self.bot = TelegramBot(token, chat_id)
        else:
            logger.warning("Telegram notification settings not found. System will log only.")

    def notify_success(self, config, results_df, total_time: str, success_count: int, total_count: int):
        """Processes raw data and sends a professional success summary."""
        if not self.bot:
            return

        icon = " ✅" if (total_count > 0 and success_count == total_count) else " ⚠️"
        upload_ratio = f"{success_count}/{total_count}{icon}" if total_count > 0 else "N/A"

        message = (
            f"✅ <b>Scan Success</b>\n"
            f"Alpha: {config.backtest.alpha_name} Gen: {config.backtest.gen_name} Configs: {len(results_df)}\n"
            f"Time: {total_time} | Upload: {upload_ratio}"
        )
        self.bot.send_message(message)
