import time
import logging
from contextlib import ContextDecorator

logger = logging.getLogger(__name__)

class Timer(ContextDecorator):
    """
    A minimal execution timer that can be used as a decorator or context manager.
    Usage:
        @Timer("Backtest")
        def run(): ...
        
        with Timer("Total"):
            ...
    """
    def __init__(self, task_name="Task"):
        self.task_name = task_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = (time.time() - self.start_time) / 60
        logger.info(f"{self.task_name} duration: {self.duration:.2f} minutes")
        return False
