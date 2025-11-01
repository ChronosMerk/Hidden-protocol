import os
import logging
import contextlib
from typing import Optional, Set

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.types import Message, FSInputFile

from app.services.download_video import DownloadVideo
from app.utils.urls import first_url, domain_ok

log = logging.getLogger(__name__)

class VideoRouter:
    def __init__(
        self,
        downloader: DownloadVideo,
        allowed_group_ids: Set[int],            # только эти группы
        topic_chat_id: Optional[int] = None,    # группа для спец-треда
        topic_thread_id: Optional[int] = None,  # id темы
    ):
        self.router = Router()
        self.downloader = downloader
        self.allowed_group_ids = allowed_group_ids
        self.topic_chat_id = topic_chat_id
        self.topic_thread_id = topic_thread_id
        self._register()

    def _register(self):
        self.router.message.register(self.handle_url, F.text.regexp(r"https?://\S+"))

    async def handle_url(self, m: Message):
        url = first_url(m.text)
        if not url or not domain_ok(url):
            return False

        user_id = m.from_user.id
        chat_id = m.chat.id
        chat_type = m.chat.type

        # Разрешённые контексты: ЛС или разрешённая группа
        is_private = chat_type == ChatType.PRIVATE
        is_allowed_group = chat_type in {ChatType.GROUP, ChatType.SUPERGROUP} and chat_id in self.allowed_group_ids
        if not (is_private or is_allowed_group):
            log.info("skip_forbidden_context user=%s chat=%s type=%s url=%s", user_id, chat_id, chat_type, url)
            return False  # не наш контекст → пусть обработают другие (или тишина)

        # Куда слать результат
        if is_private:
            target_chat_id = chat_id
            target_thread_id = None
        else:
            # Группа: в спец-тред указанной группы
            target_chat_id = self.topic_chat_id or chat_id
            target_thread_id = self.topic_thread_id

        # Индикация
        chat_action_kwargs = {}
        if target_thread_id is not None:
            chat_action_kwargs["message_thread_id"] = target_thread_id
        await m.bot.send_chat_action(target_chat_id, "upload_video", **chat_action_kwargs)

        username = f"@{m.from_user.username}" if m.from_user.username else m.from_user.full_name
        caption = f"🎬 Отправлено пользователем: {username}\n🌐 Ссылка: {url}"
        caption = caption[:1024]

        filepath = None
        try:
            log.info("download_start user=%s chat=%s private=%s url=%s", user_id, chat_id, is_private, url)
            res = await self.downloader.download(url)
            filepath = res["filepath"]

            send_kwargs = {
                "chat_id": target_chat_id,
                "video": FSInputFile(filepath),     # отправляем как видео
                "caption": caption,
                "disable_notification": True,
            }
            if target_thread_id is not None:
                send_kwargs["message_thread_id"] = target_thread_id

            await m.bot.send_video(**send_kwargs)
            log.info("download_ok user=%s chat=%s sent_to=%s thread=%s file=%s", user_id, chat_id, target_chat_id, target_thread_id, filepath)

            if not is_private:
                with contextlib.suppress(Exception):
                    await m.delete()

        except Exception as e:
            log.exception("download_fail user=%s chat=%s url=%s err=%s", user_id, chat_id, url, e)
            await m.answer("⚠️ Не удалось скачать или отправить видео. Проверь ссылку.")
        finally:
            if filepath:
                with contextlib.suppress(Exception):
                    os.remove(filepath)
