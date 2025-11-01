import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()
        self.missing = []
        self.keys = ['TOKEN', 'API_KEY_JWT', 'HOST', 'PORT']
        self.missing = [key for key in self.keys if not os.getenv(key)]
        if self.missing:
            raise ValueError(f"❌ Отсутствуют переменные в .env: {', '.join(self.missing)}")
    def get_config(self):
        raw_admins = os.getenv("ADMIN_IDS", "")
        admin_ids = {int(x) for x in raw_admins.split(",") if x.strip().isdigit()}
        raw_groups = os.getenv("ALLOWED_GROUP_IDS", "")
        allowed_group_ids = {int(x) for x in raw_groups.split(",") if x.strip().lstrip("-").isdigit()}

        return {
            "BOT_TOKEN": os.getenv("TOKEN"),
            "API_KEY_JWT": os.getenv("API_KEY_JWT"),
            "HOST": os.getenv("HOST"),
            "PORT": int(os.getenv("PORT", 8000)),
            "ADMIN_IDS": admin_ids,
            "DOWNLOAD_DIR": os.getenv("DOWNLOAD_DIR", "/app/downloads"),
            "TOPIC_CHAT_ID": int(os.getenv("TOPIC_CHAT_ID")) if os.getenv("TOPIC_CHAT_ID") else None,
            "TOPIC_THREAD_ID": int(os.getenv("TOPIC_THREAD_ID")) if os.getenv("TOPIC_THREAD_ID") else None,
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "LOG_CHAT_ID": int(os.getenv("LOG_CHAT_ID")) if os.getenv("LOG_CHAT_ID") else None,
            "LOG_THREAD_ID": int(os.getenv("LOG_THREAD_ID")) if os.getenv("LOG_THREAD_ID") else None,
            "ALLOWED_GROUP_IDS": allowed_group_ids,  # set[int]
        }

