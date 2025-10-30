import asyncio
import pathlib
from typing import Callable, Optional, Dict, Any
import yt_dlp

class DownloadVideo:
    def __init__(self, download_dir: str = "./downloads", ydl_opts: Optional[Dict[str, Any]] = None):
        self.dir = pathlib.Path(download_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ydl_opts = ydl_opts or {}

    async def download(self, url: str, on_progress: Optional[Callable[[dict], None]] = None) -> dict:
        def _run() -> dict:
            def hook(d: dict):
                if on_progress:
                    on_progress(d)

            opts = dict(self.ydl_opts)
            opts.setdefault("noplaylist", True)
            opts.setdefault("restrictfilenames", True)
            opts.setdefault("format", "mp4/bestvideo+bestaudio/best")
            opts.setdefault("merge_output_format", "mp4")
            opts.setdefault("quiet", True)
            tpl = opts.get("outtmpl") or "%(title).200s-%(id)s.%(ext)s"
            opts["outtmpl"] = str(self.dir / tpl)
            opts["progress_hooks"] = [hook]

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                return {
                    "filepath": filepath,
                    "title": info.get("title"),
                    "ext": info.get("ext"),
                    "filesize": info.get("filesize") or info.get("filesize_approx"),
                }

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)
