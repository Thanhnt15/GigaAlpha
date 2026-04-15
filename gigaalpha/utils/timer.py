import time
import logging
from contextlib import ContextDecorator

logger = logging.getLogger(__name__)

class Timer(ContextDecorator):
    """
    A professional execution timer context manager and decorator.
    Usage:
        with Timer("Backtest Phase"):
            run_backtest()
    """
    def __init__(self, task_name: str = "Task"):
        self.task_name = task_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration_mins = (end_time - self.start_time) / 60
        if exc_type is None:
            logger.info(f"{self.task_name} completed in {duration_mins:.4f} minutes")
        else:
            logger.error(f"{self.task_name} failed after {duration_mins:.4f} minutes with error: {exc_val}")
        return False  # Do not suppress exceptions
