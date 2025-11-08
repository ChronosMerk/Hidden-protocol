import re
from urllib.parse import urlparse
from typing import Optional

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

# Хосты, которые принимаем
_TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
_INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com"}

def first_url(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    m = URL_RE.search(text)
    return m.group(0) if m else None

def is_allowed_url(url: str) -> bool:
    """
    Разрешаем:
      - Любые пути на TikTok (указанные хосты)
      - Только /reel/ на Instagram
    Запрещаем остальное, включая instagram.com/p/
    """
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        path = p.path.lower()

        if host in _TIKTOK_HOSTS:
            return True

        if host in _INSTAGRAM_HOSTS and path.startswith("/reel/"):
            return True

        return False
    except Exception:
        return False
