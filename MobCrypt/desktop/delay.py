import random
import time


def generate_delay(min_seconds: float = 300.0, max_seconds: float = 900.0) -> float:
    raw = random.uniform(min_seconds, max_seconds)
    seconds = int(raw)
    milliseconds = random.randint(1, 999)
    result = seconds + milliseconds / 1000.0
    return result


def format_delay(seconds: float) -> str:
    secs = int(seconds)
    millis = int((seconds - secs) * 1000)
    minutes = secs // 60
    secs = secs % 60
    return f"{minutes:02d}min{secs:02d}s{millis:03d}ms"


def wait(delay: float) -> None:
    time.sleep(delay)
