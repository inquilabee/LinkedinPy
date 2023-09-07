import random
import time


def humanized_wait(min_wait: int, max_wait: int = None, multiply_factor: float = 1.5):
    max_wait = int(max_wait or min_wait * multiply_factor)
    actual_wait = random.randint(min_wait, max_wait)  # nosec
    time.sleep(actual_wait)
