import pytz
from datetime import datetime


class System:
    @staticmethod
    def get_now_vn() -> datetime:
        """Lấy thời gian hiện tại theo múi giờ Việt Nam"""
        return datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))

    @staticmethod
    def vn_time_converter(*args):
        """
        Hàm convert timestamp sang giờ Việt Nam cho logging.
        Hỗ trợ cả khi được gọi như hàm độc lập hoặc bound method (lấy args[-1] làm timestamp).
        """
        seconds = args[-1]
        return datetime.fromtimestamp(seconds, pytz.timezone('Asia/Ho_Chi_Minh')).timetuple()