import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from zoneinfo import ZoneInfo


class NotifyOrErrorFilter(logging.Filter):
    """Пропускает записи, если уровень >= ERROR или record.notify == True."""
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR or getattr(record, "notify", False)


class TzFormatter(logging.Formatter):
    """Форматтер, использующий часовой пояс Asia/Almaty (+5)."""
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo("Asia/Almaty"))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def setup_logger(level: str = "INFO") -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    log = logging.getLogger("hidden_protocol")
    if log.handlers:
        return log

    log.setLevel(level.upper())

    fmt = TzFormatter(
        "%(asctime)s [%(levelname)s] %(name)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консольный вывод
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(level.upper())
    log.addHandler(ch)

    # Файл — полный лог (DEBUG+)
    file_name = datetime.now(tz=ZoneInfo("Asia/Almaty")).strftime("bot_log_%Y-%m-%d.log")
    fh = RotatingFileHandler(
        os.path.join("logs", file_name),
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)
    log.addHandler(fh)

    return log
