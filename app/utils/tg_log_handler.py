import asyncio
import logging
import textwrap
import traceback
from typing import Optional
from aiogram import Bot

TG_MAX = 4096


class TelegramLogHandler(logging.Handler):
    def __init__(
        self,
        bot: Bot,
        chat_id: int,
        thread_id: Optional[int] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        level: int = logging.INFO,
        disable_notification: bool = True,
    ):
        super().__init__(level=level)
        self.bot = bot
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.loop = loop or asyncio.get_event_loop()
        self.disable_notification = disable_notification

        # Показываем только сам message, без "INFO:" и времени
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            base = self.format(record)
            block = ""
            if record.exc_info:
                tb_text = "".join(traceback.format_exception(*record.exc_info)).replace("`", "'")
                block = textwrap.shorten(tb_text, width=TG_MAX - 100, placeholder="…")

            text = base
            if block:
                rest = TG_MAX - len(block) - 2
                text = textwrap.shorten(text, width=max(80, rest), placeholder="…")
                text = f"{text}\n{block}"
            else:
                text = textwrap.shorten(text, width=TG_MAX, placeholder="…")

            kwargs = dict(
                chat_id=self.chat_id,
                text=text,
                # БЕЗ parse_mode, чтобы ничего не ломалось из-за Markdown
                disable_notification=self.disable_notification,
            )
            if self.thread_id is not None:
                kwargs["message_thread_id"] = self.thread_id

            asyncio.run_coroutine_threadsafe(
                self.bot.send_message(**kwargs),
                self.loop,
            )
        except Exception:
            self.handleError(record)