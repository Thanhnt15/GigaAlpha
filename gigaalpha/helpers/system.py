import pytz
from datetime import datetime


class System:
    @staticmethod
    def get_now_vn() -> datetime:
        """Lấy thời gian hiện tại theo múi giờ Việt Nam"""
        return datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))