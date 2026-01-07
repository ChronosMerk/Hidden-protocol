from typing import Dict

USER_TITLES: Dict[int, str] = {
    468056370: "Цифровой Владыка",
    595236395: "Звездный Свет",
    801954476: "Иллюминаты",
    1646538858: "Шрёдингериум",
    423562139: "Высший Разум",
    468815244: "Галактический Трибунал",
    559817205: "Вечный Маверик",
    848916899: "Верховный Консул"
}

BASE_TEXT = "Hidden protocol активен. Используй /help для списка команд."


def get_start_text(user_id: int | None) -> str:
    """
    Возвращает текст для /start с учётом звания пользователя,
    если оно есть в USER_TITLES.
    """
    title = USER_TITLES.get(user_id)
    if title:
        return f"{title}, {BASE_TEXT}"
    return BASE_TEXT