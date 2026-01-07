import logging
from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ChatMemberStatus, ChatType

router_join = Router()
log = logging.getLogger("hidden_protocol.join")


def prettify_chat_type(chat_type: ChatType | str) -> str:
    return {
        ChatType.GROUP: "Группа",
        ChatType.SUPERGROUP: "Супергруппа",
        ChatType.CHANNEL: "Канал",
        ChatType.PRIVATE: "Личка",
    }.get(chat_type, str(chat_type))


@router_join.my_chat_member()
async def bot_membership_changed(event: ChatMemberUpdated):
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    chat = event.chat
    chat_id = chat.id
    chat_type_raw = chat.type
    chat_type = prettify_chat_type(chat_type_raw)
    chat_title = getattr(chat, "title", None) or getattr(chat, "full_name", None) or str(chat_id)

    from_user = event.from_user
    actor = f"@{from_user.username}" if from_user and from_user.username else (
        from_user.full_name if from_user else "Неизвестно"
    )

    # Бота добавили
    if old_status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED} and \
       new_status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR}:

        pretty_log = (
            "🟢 Бот добавлен в чат\n\n"
            f"Чат: {chat_title}\n"
            f"Тип: {chat_type}\n"
            f"Chat ID: {chat_id}\n"
            f"Добавил: {actor}"
        )

        # Приветствие в сам чат (как было)
        try:
            if chat_type_raw in {ChatType.GROUP, ChatType.SUPERGROUP}:
                greet = (
                    f"🔮 Hidden Protocol подключён к чату «{chat_title}».\n"
                    "Используй /help для списка команд."
                )
            elif chat_type_raw == ChatType.CHANNEL:
                greet = (
                    f"🔮 Hidden Protocol активирован в канале «{chat_title}».\n"
                    "Готов к публикации по протоколам."
                )
            else:
                greet = (
                    "🔮 Hidden Protocol активирован.\n"
                    "Используй /help для списка команд."
                )
            await event.bot.send_message(chat_id, greet)
        except Exception:
            log.exception(
                "bot_join_greet_fail chat_id=%s type=%s title=%s",
                chat_id,
                chat_type,
                chat_title,
            )

        # Одно красивое сообщение в лог-чат
        log.info(pretty_log, extra={"notify": True})
        return

    # Бота удалили
    if old_status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR} and \
       new_status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}:

        pretty_log = (
            "🔴 Бот удалён из чата\n\n"
            f"Чат: {chat_title}\n"
            f"Тип: {chat_type}\n"
            f"Chat ID: {chat_id}\n"
            f"Удалил: {actor}"
        )
        log.info(pretty_log, extra={"notify": True})