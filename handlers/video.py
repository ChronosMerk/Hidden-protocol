import os
import contextlib
from typing import Optional
from aiogram import Router
from aiogram import F
from aiogram.enums import ChatType
from aiogram.types import Message, FSInputFile
from app.services.download_video import DownloadVideo
from app.utils.urls import first_url, domain_ok
from app.utils.logger import setup_logger

class VideoRouter:
    def __init__(
        self,
        downloader: DownloadVideo,
        topic_chat_id: Optional[int] = None,
        topic_thread_id: Optional[int] = None,
    ):
        self.router = Router()
        self.downloader = downloader
        self.topic_chat_id = topic_chat_id
        self.topic_thread_id = topic_thread_id
        self.log = setup_logger()
        self._register()

    def _register(self):
        # ловим сообщения с URL
        self.router.message.register(self.handle_url, F.text.regexp(r"https?://\S+"))

    async def handle_url(self, m: Message):
        url = first_url(m.text)
        if not url or not domain_ok(url):
            return False

        self.log.info(f"URL от @{m.from_user.username or m.from_user.full_name}: {url}")

        is_private = (m.chat.type == ChatType.PRIVATE)
        if is_private:
            target_chat_id = m.chat.id
            target_thread_id = None
        else:
            target_chat_id = self.topic_chat_id or m.chat.id
            target_thread_id = self.topic_thread_id

        chat_action_kwargs = {}
        if target_thread_id is not None:
            chat_action_kwargs["message_thread_id"] = target_thread_id
        await m.bot.send_chat_action(target_chat_id, "upload_video", **chat_action_kwargs)

        username = f"@{m.from_user.username}" if m.from_user.username else m.from_user.full_name
        caption = f"🎬 Отправлено пользователем: {username}\n🌐 Ссылка: {url}"
        caption = caption[:1024]

        filepath = None
        try:
            res = await self.downloader.download(url)
            filepath = res["filepath"]

            send_kwargs = {
                "chat_id": target_chat_id,
                "video": FSInputFile(filepath),
                "caption": caption,
                "disable_notification": True,
            }
            if target_thread_id is not None:
                send_kwargs["message_thread_id"] = target_thread_id

            await m.bot.send_video(**send_kwargs)

            if not is_private:
                with contextlib.suppress(Exception):
                    await m.delete()

        except Exception as e:
            self.log.exception("Ошибка скачивания/отправки url=%s", url)
            await m.answer("⚠️ Не удалось скачать или отправить видео. Проверь ссылку.")
        finally:
            if filepath:
                with contextlib.suppress(Exception):
                    os.remove(filepath)
