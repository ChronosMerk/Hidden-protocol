import asyncio
import logging
from aiogram import Bot, Dispatcher

from app.config import Config
from handlers.coreHandlersCommand import CoreHandlers
from handlers.joinHandlers import router_join
from handlers.video import VideoRouter
from app.services.download_video import DownloadVideo
from app.utils.logger import setup_logger, NotifyOrErrorFilter
from app.utils.tg_log_handler import TelegramLogHandler


class RunHiddenProtocol:
    def __init__(self):
        self.cfg = Config().get_config()
        self.log = setup_logger(self.cfg.get("LOG_LEVEL", "INFO"))

        self.bot = Bot(token=self.cfg["BOT_TOKEN"])
        self.dp = Dispatcher()

        # Команды
        core = CoreHandlers(admins=self.cfg["ADMIN_IDS"])
        self.dp.include_router(core.router)

        self.dp.include_router(router_join)

        # Видео с ограничениями: только ЛС и ALLOWED_GROUP_IDS
        downloader = DownloadVideo(download_dir=self.cfg.get("DOWNLOAD_DIR", "./downloads"))
        video = VideoRouter(
            downloader=downloader,
            allowed_group_ids=self.cfg["ALLOWED_GROUP_IDS"],                 # <-- важно
            topic_chat_id=self.cfg.get("TOPIC_CHAT_ID"),
            topic_thread_id=self.cfg.get("TOPIC_THREAD_ID"),
        )
        self.dp.include_router(video.router)

    async def run_bot(self):
        loop = asyncio.get_running_loop()

        # Логи в Telegram: уведомления (extra["notify"]=True) и ошибки (ERROR+)
        if self.cfg.get("LOG_CHAT_ID"):
            tg = TelegramLogHandler(
                bot=self.bot,
                chat_id=int(self.cfg["LOG_CHAT_ID"]),
                thread_id=self.cfg.get("LOG_THREAD_ID"),
                loop=loop,
                level=logging.INFO,
                disable_notification=True,
            )
            tg.addFilter(NotifyOrErrorFilter())
            logging.getLogger("hidden_protocol").addHandler(tg)

        self.log.info("✅Bot starting…", extra={"notify": True})
        try:
            await self.dp.start_polling(self.bot)
        except Exception:
            self.log.exception("Polling crashed")
            raise
        finally:
            self.log.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(RunHiddenProtocol().run_bot())
