import re
from urllib.parse import urlparse
from typing import Optional

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
ALLOWED_DOMAINS = {
    "instagram.com", "www.instagram.com",
    "tiktok.com", "www.tiktok.com", "vm.tiktok.com", "vt.tiktok.com",
}

def first_url(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    m = URL_RE.search(text)
    return m.group(0) if m else None

def domain_ok(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return host in ALLOWED_DOMAINS
    except Exception:
        return False
