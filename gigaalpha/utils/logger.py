import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    if not logging.getLogger().handlers:
        from gigaalpha.helpers.system import System
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        log_fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        log_fmt.converter = System.vn_time_converter

        console_h = logging.StreamHandler(sys.stdout)
        console_h.setLevel(logging.INFO)
        console_h.setFormatter(log_fmt)

        ui_file_h = RotatingFileHandler(log_dir / "system.log", maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
        ui_file_h.setLevel(logging.INFO)
        ui_file_h.setFormatter(log_fmt)

        dev_file_h = RotatingFileHandler(log_dir / "system_debug.log", maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
        dev_file_h.setLevel(logging.DEBUG)
        dev_file_h.setFormatter(log_fmt)

        logger.addHandler(console_h)
        logger.addHandler(ui_file_h)
        logger.addHandler(dev_file_h)

        logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
