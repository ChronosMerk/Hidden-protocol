import os
import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta, timezone

class NotifyOrErrorFilter(logging.Filter):
    """Пропускает записи, если level>=ERROR или record.notify == True."""
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR or getattr(record, "notify", False)


# --- кастомный Formatter с таймзоной UTC+5 (Астана)
class TZFormatter(logging.Formatter):
    def converter(self, timestamp):
        # Преобразуем timestamp (в секундах) в UTC+5
        utc_time = datetime.utcfromtimestamp(timestamp)
        return utc_time + timedelta(hours=5)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def setup_logger(level: str = "INFO") -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    log = logging.getLogger("hidden_protocol")
    if log.handlers:
        return log

    log.setLevel(level.upper())

    fmt = TZFormatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консольный вывод
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(level.upper())
    log.addHandler(ch)

    # Файл с ротацией
    file_name = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5))).strftime("bot_log_%Y-%m-%d.log")
    fh = RotatingFileHandler(os.path.join("logs", file_name),
                             maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    return log