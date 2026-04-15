import json
import urllib.request
import urllib.parse
import logging

logger = logging.getLogger(__name__)

class TelegramBot:
    """
    A portable Telegram bot helper using built-in urllib to avoid external dependencies.
    """
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Sends a text message to the configured Telegram chat.
        """
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        return self._post_request(url, data)

    def _post_request(self, url: str, data: dict) -> bool:
        """Helper to handle HTTP POST requests using urllib."""
        try:
            encoded_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=encoded_data, method='POST')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Telegram API returned status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False
