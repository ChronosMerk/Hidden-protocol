import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

class NotifyOrErrorFilter(logging.Filter):
    """Пропускает записи, если level>=ERROR или record.notify == True."""
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= logging.ERROR or getattr(record, "notify", False)

def setup_logger(level: str = "INFO") -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    log = logging.getLogger("hidden_protocol")
    if log.handlers:
        return log

    log.setLevel(level.upper())

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консоль
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    ch.setLevel(level.upper())
    log.addHandler(ch)

    # Файл — пишем всё
    file_name = datetime.now().strftime("bot_log_%Y-%m-%d.log")
    fh = RotatingFileHandler(os.path.join("logs", file_name),
                             maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(logging.DEBUG)      # <- весь поток
    log.addHandler(fh)

    return log