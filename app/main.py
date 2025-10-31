import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config import Config
from handlers.coreHandlersCommand import CoreHandlers
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

        core = CoreHandlers(admins=self.cfg["ADMIN_IDS"])
        self.dp.include_router(core.router)

        downloader = DownloadVideo(download_dir=self.cfg.get("DOWNLOAD_DIR", "./downloads"))
        video = VideoRouter(
            downloader=downloader,
            topic_chat_id=self.cfg.get("TOPIC_CHAT_ID"),
            topic_thread_id=self.cfg.get("TOPIC_THREAD_ID"),
        )
        self.dp.include_router(video.router)

    async def run_bot(self):
        loop = asyncio.get_running_loop()

        # Telegram-хендлер: только notify или ERROR+
        if self.cfg.get("LOG_CHAT_ID"):
            tg = TelegramLogHandler(
                bot=self.bot,
                chat_id=int(self.cfg["LOG_CHAT_ID"]),
                thread_id=self.cfg.get("LOG_THREAD_ID"),
                loop=loop,
                level=logging.INFO,  # базовый уровень
                disable_notification=True,
            )
            tg.addFilter(NotifyOrErrorFilter())  # <- ключевая строка
            logging.getLogger("hidden_protocol").addHandler(tg)

        # Стартовое уведомление (уйдёт в ТГ из-за notify=True)
        self.log.info("Bot starting…", extra={"notify": True})
        try:
            await self.dp.start_polling(self.bot)
        except Exception:
            # Любая ошибка поллинга уйдёт в файл и в ТГ (ERROR+)
            self.log.exception("Polling crashed")
            raise
        finally:
            self.log.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(RunHiddenProtocol().run_bot())
