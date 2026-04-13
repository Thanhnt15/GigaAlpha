from gigaalpha.helpers.drive import GDrive

class UploadService:
    def __init__(self, local_path: str, token_path: str, target_folder_id: str):
        """Khởi tạo với đường dẫn file cục bộ và thông tin cấu hình Drive."""
        self.local_path = local_path
        self.token_path = token_path
        self.target_folder_id = target_folder_id

    def upload_to_drive(self):
        """Thực hiện upload file excel lên Google Drive."""
        return GDrive.upload_files(
            token_path=self.token_path,
            file_paths=[self.local_path],
            target_folder_id=self.target_folder_id,
        )