import sys
import logging
import os
import time
import socket
import urllib.request
import json
import html
from logging.handlers import RotatingFileHandler
from pathlib import Path

def cleanup_old_logs(log_dir: Path, max_days: int = 14):
    """Deletes log files older than max_days in the specified directory."""
    try:
        now = time.time()
        for item in log_dir.glob('*.log*'):
            if item.is_file():
                # Check file age
                file_age_days = (now - item.stat().st_mtime) / (60 * 60 * 24)
                if file_age_days > max_days:
                    item.unlink()
                    # We can't log this yet because setup_logging isn't finished, 
                    # but we can print to stderr
                    print(f"Cleanup: Deleted old log file {item.name}", file=sys.stderr)
    except Exception as e:
        print(f"Cleanup error: {e}", file=sys.stderr)

import fcntl

class TelegramHandler(logging.Handler):
    """A minimalist logging handler with cross-process rate limiting."""
    COOLDOWN_SECONDS = 60   # Minimum seconds between Telegram alerts
    
    def __init__(self, token: str, chat_id: str):
        super().__init__()
        self.token = token
        self.chat_id = chat_id
        # Define cooldown file path
        project_root = Path(__file__).resolve().parents[2]
        self.cooldown_file = project_root / "logs" / ".tele_cooldown"

    def _should_throttle(self) -> bool:
        """Checks if a message should be throttled using an exclusive file lock."""
        try:
            # Create file if not exists
            if not self.cooldown_file.exists():
                self.cooldown_file.touch()

            with open(self.cooldown_file, "r+") as f:
                # Acquisition of an exclusive lock (blocking)
                fcntl.flock(f, fcntl.LOCK_EX)
                
                try:
                    content = f.read().strip()
                    last_sent = float(content) if content else 0.0
                except ValueError:
                    last_sent = 0.0

                now = time.time()
                if now - last_sent < self.COOLDOWN_SECONDS:
                    return True  # Throttled
                
                # Update timestamp and release
                f.seek(0)
                f.write(str(now))
                f.truncate()
                return False
        except Exception as e:
            # Fallback: if locking fails, allow sending but print error
            print(f"Rate Limiter Lock Error: {e}", file=sys.stderr)
            return False

    def emit(self, record):
        if not self.token or not self.chat_id:
            return

        # Check if we should throttle this message
        if self._should_throttle():
            return

        try:
            log_entry = self.format(record)
            # Truncate error detail and escape HTML to prevent Telegram rejection
            short_entry = (log_entry[:3000] + '...') if len(log_entry) > 3000 else log_entry
            safe_entry = html.escape(short_entry)
            
            # Dynamic icon based on severity
            icon = "❌" if record.levelno >= logging.ERROR else "⚠️"
            title = "Error Alert" if record.levelno >= logging.ERROR else "Warning Alert"
            
            message = f"{icon} <b>{title}</b>\n\n<code>{safe_entry}</code>"
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = json.dumps({
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            # Timeout set to 5s to avoid hanging the main process
            with urllib.request.urlopen(req, timeout=5):
                pass
        except Exception as e:
            # Print to stderr instead of silent fail to help debugging
            print(f"Telegram Handler Error: {e}", file=sys.stderr)

def setup_logging():
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Prune old logs before setting up
    cleanup_old_logs(log_dir, max_days=14)
    
    if not logging.getLogger().handlers:
        from gigaalpha.helpers.system import System
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Standard formatter for Console and system.log
        simple_fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        simple_fmt.converter = System.vn_time_converter

        # Detailed formatter for system_debug.log (includes module name)
        detailed_fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        detailed_fmt.converter = System.vn_time_converter

        console_h = logging.StreamHandler(sys.stdout)
        console_h.setLevel(logging.INFO)
        console_h.setFormatter(simple_fmt)

        ui_file_h = RotatingFileHandler(log_dir / "system.log", maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
        ui_file_h.setLevel(logging.INFO)
        ui_file_h.setFormatter(simple_fmt)

        dev_file_h = RotatingFileHandler(log_dir / "system_debug.log", maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
        dev_file_h.setLevel(logging.DEBUG)
        dev_file_h.setFormatter(detailed_fmt)

        logger.addHandler(console_h)
        logger.addHandler(ui_file_h)
        logger.addHandler(dev_file_h)

        # Automated Telegram Error Reporting
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip().replace('"', '').replace("'", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip().replace('"', '').replace("'", "")
        
        if token and chat_id:
            tele_h = TelegramHandler(token, chat_id)
            tele_h.setLevel(logging.WARNING)
            tele_h.setFormatter(detailed_fmt)
            logger.addHandler(tele_h)
            # Handler initialized silently to keep terminal clean
        else:
            # Highlight missing configuration as a warning on startup
            print("\n⚠️  [MONITORING] Telegram Alert is DISABLED: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID\n", file=sys.stderr)

        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
