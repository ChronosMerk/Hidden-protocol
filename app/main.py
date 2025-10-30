import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import Config
from handlers.coreHandlersCommand import CoreHandlers
from handlers.video import VideoRouter
from app.services.download_video import DownloadVideo

class RunHiddenProtocol:
    def __init__(self):
        self.cfg = Config().get_config()
        logging.basicConfig(level=self.cfg.get("LOG_LEVEL", "INFO"))

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
        await self.dp.start_polling(self.bot)

if __name__ == "__main__":
    asyncio.run(RunHiddenProtocol().run_bot())
