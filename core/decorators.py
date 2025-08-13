
import logging
import functools
import time


logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"[{func.__name__}] started")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"[{func.__name__}] completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            logger.exception(f"[{func.__name__}] failed with error: {e}")
            raise
    return wrapper
