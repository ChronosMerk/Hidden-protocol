import os
import logging
import contextlib
from typing import Optional, Set

from aiogram import Router, F
from aiogram.enums import ChatType, ChatAction
from aiogram.types import Message, FSInputFile

from app.services.download_video import DownloadVideo
from app.utils.urls import first_url, domain_ok

def _type_str(t) -> str:
    return t.value if hasattr(t, "value") else str(t)

def _is_private(chat) -> bool:
    t = chat.type
    return t == ChatType.PRIVATE or t == "private"

def _is_group(chat) -> bool:
    t = chat.type
    return t in {ChatType.GROUP, ChatType.SUPERGROUP, "group", "supergroup"}

log = logging.getLogger("hidden_protocol.video")

URL_PATTERN = r"https?://\S+"

class VideoRouter:
    def __init__(
        self,
        downloader: DownloadVideo,
        allowed_group_ids: Set[int] = frozenset(),
        topic_chat_id: Optional[int] = None,
        topic_thread_id: Optional[int] = None,
    ):
        self.router = Router()
        self.downloader = downloader
        self.allowed_group_ids = allowed_group_ids
        self.topic_chat_id = topic_chat_id
        self.topic_thread_id = topic_thread_id
        self._register()

    def _register(self):
        self.router.message.register(self.handle_url, F.text.regexp(URL_PATTERN))

    async def handle_url(self, m: Message):
        url = first_url(m.text)
        user = m.from_user
        user_id = user.id if user else None
        chat_id = m.chat.id
        chat_type = _type_str(m.chat.type)

        if not url:
            log.debug("skip_no_url user=%s chat=%s type=%s", user_id, chat_id, chat_type)
            return False
        if not domain_ok(url):
            log.info("deny_url user=%s chat=%s type=%s url=%s reason=unsupported_domain",
                     user_id, chat_id, chat_type, url, extra={"notify": True})
            return False

        is_private = _is_private(m.chat)
        is_group = _is_group(m.chat)
        is_allowed_group = is_group and (chat_id in self.allowed_group_ids)

        if not (is_private or is_allowed_group):
            log.warning("deny_context user=%s chat=%s type=%s url=%s reason=group_not_allowed",
                        user_id, chat_id, chat_type, url, extra={"notify": True})
            return False

        # --- Роутинг (приоритеты):
        # 1) если сообщение пришло в теме — отправляем в эту же тему
        if not is_private and m.message_thread_id is not None:
            target_chat_id = chat_id
            target_thread_id = m.message_thread_id
            route_note = "group_same_thread"
        # 2) иначе, если это TOPIC_CHAT_ID и задан TOPIC_THREAD_ID — отправляем туда
        elif not is_private and self.topic_chat_id and chat_id == self.topic_chat_id and self.topic_thread_id is not None:
            target_chat_id = chat_id
            target_thread_id = self.topic_thread_id
            route_note = "group_to_special_thread"
        # 3) иначе — тот же чат без темы (или ЛС)
        else:
            target_chat_id = chat_id
            target_thread_id = None if not is_private else None
            route_note = "private_echo" if is_private else "group_same_chat"

        username = f"@{user.username}" if user and user.username else (user.full_name if user else "unknown")
        caption = f"🎬 Отправлено пользователем: {username}\n🌐 Ссылка: {url}"
        caption = caption[:1024]

        # Индикация
        chat_action_kwargs = {}
        if target_thread_id is not None:
            chat_action_kwargs["message_thread_id"] = target_thread_id
        try:
            await m.bot.send_chat_action(target_chat_id, ChatAction.UPLOAD_VIDEO, **chat_action_kwargs)
        except Exception as e:
            log.exception(
                "chat_action_fail user=%s chat=%s type=%s url=%s target_chat=%s target_thread=%s err=%s",
                user_id, chat_id, chat_type, url, target_chat_id, target_thread_id, e,
                extra={"notify": True},
            )
            return

        log.info(
            "route user=%s chat=%s type=%s url=%s -> target_chat=%s target_thread=%s note=%s",
            user_id, chat_id, chat_type, url, target_chat_id, target_thread_id, route_note
        )

        filepath = None
        try:
            log.info("download_start user=%s chat=%s type=%s url=%s", user_id, chat_id, chat_type, url)
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

            log.info(
                "download_ok user=%s chat=%s type=%s url=%s file=%s sent_to=%s thread=%s",
                user_id, chat_id, chat_type, url, filepath, target_chat_id, target_thread_id
            )

            #if not is_private:
            with contextlib.suppress(Exception):
                await m.delete()

        except Exception as e:
            log.exception(
                "send_fail user=%s chat=%s type=%s url=%s target_chat=%s thread=%s err=%s",
                user_id, chat_id, chat_type, url, target_chat_id, target_thread_id, e,
                extra={"notify": True},
            )
            with contextlib.suppress(Exception):
                await m.answer("⚠️ Не удалось скачать или отправить видео. Проверь ссылку или права бота.")
        finally:
            if filepath:
                with contextlib.suppress(Exception):
                    os.remove(filepath)
                    log.debug("file_cleanup path=%s", filepath)
