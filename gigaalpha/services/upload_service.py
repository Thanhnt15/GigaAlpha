import logging
import time
import random
from gigaalpha.helpers.drive import GDrive

logger = logging.getLogger(__name__)

class UploadService:
    def __init__(self, local_path: str, token_path: str, target_folder_id: str):
        """Initialize with a single file path in preparation for the worker."""
        self.local_path = local_path
        self.token_path = token_path
        self.target_folder_id = target_folder_id

    def upload_to_drive(self):
        """Execute upload of a single file to Google Drive with integrated API jitter."""
        try:
            # Prevent API Thundering Herd: Force workers to sleep for a random 0.5-2.0s offset before starting
            jitter = random.uniform(0.5, 2.0)
            time.sleep(jitter)
            
            logger.info(f"Uploading file to Drive: {self.local_path} (Delay {jitter:.2f}s)")
            return GDrive.upload_files(
                token_path=self.token_path,
                file_paths=[self.local_path],
                target_folder_id=self.target_folder_id,
            )
        except Exception:
            logger.exception(f"Failed to upload file to Drive: {self.local_path}")
            return None