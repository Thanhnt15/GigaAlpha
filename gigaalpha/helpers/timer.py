import time
import logging
from contextlib import ContextDecorator

logger = logging.getLogger(__name__)

class Timer(ContextDecorator):
    """
    A simple execution timer.
    Usage:
        with Timer("Task Name"):
            do_something()
    """
    def __init__(self, task_name="Task"):
        self.task_name = task_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (time.time() - self.start_time) / 60
        if exc_type is None:
            logger.info(f"{self.task_name} completed in {duration:.4f} minutes")
        else:
            logger.error(f"{self.task_name} failed after {duration:.4f} minutes: {exc_val}")
        return False
