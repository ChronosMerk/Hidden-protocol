import random
from typing import Set
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

class CoreHandlers:
    def __init__(self, admins: Set[int]):
        self.admins = admins
        self.router = Router()
        self._register()

    def _register(self):
        self.router.message.register(self.start, CommandStart())
        self.router.message.register(self.help_cmd, Command("help"))
        self.router.message.register(self.gpt_cmd, Command("gpt"))
        self.router.message.register(self.unknown_cmd, F.text.startswith("/"))

    async def start(self, m: Message):
        await m.answer("Hidden protocol активен. Используй /help для списка команд.")

    async def help_cmd(self, m: Message):
        await m.answer(
            "Команды:\n"
            "/start — запустить бота\n"
            "/help — показать справку\n"
            "Пришли ссылку на Instagram/TikTok — скачаю и пришлю видео."
        )

    async def gpt_cmd(self, m: Message):
        if m.from_user.id not in self.admins:
            return False
        await m.answer("GPT функция в разработке.")

    async def unknown_cmd(self, m: Message):
        random_responses = [
            "⛔ Неизвестная команда. Хочешь разорвать петлю? Сначала узнай, как она устроена.",
            "🔍 Сигнал нераспознан. Попробуй /help — или продолжай искать в темноте.",
            "🕳 Ты активировал пустоту. Она молчит в ответ.",
            "⚠️ Протокол не обнаружен. Возможно, он ещё не создан.",
        ]
        await m.answer(f'⛔ Ошибка 404: Команда не распознана.\n{random.choice(random_responses)}')
