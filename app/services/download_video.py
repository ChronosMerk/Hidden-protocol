import asyncio
import contextlib
import pathlib
import time
from typing import Callable, Optional, Dict, Any
import yt_dlp
from app.utils.logger import setup_logger


class DownloadVideo:
    def __init__(
        self,
        download_dir: str = "./downloads",
        ydl_opts: Optional[Dict[str, Any]] = None,
    ):
        self.dir = pathlib.Path(download_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ydl_opts = ydl_opts or {}
        self.log = setup_logger()  # использует общий конфиг логгера

    async def download(
        self,
        url: str,
        on_progress: Optional[Callable[[dict], None]] = None,
    ) -> dict:
        """
        Возвращает:
          {
            "filepath": str,
            "title": str | None,
            "ext": str | None,
            "filesize": int | None,
            "duration_sec": float
          }
        """
        t0 = time.monotonic()
        url_short = url if len(url) <= 128 else url[:125] + "..."

        def _run() -> dict:
            last_log = 0.0

            def hook(d: dict):
                nonlocal last_log
                # Пользовательский колбэк
                if on_progress:
                    with contextlib.suppress(Exception):
                        on_progress(d)

                now = time.monotonic()
                status = d.get("status")

                if status == "downloading":
                    # Троттлим логи, чтобы не засорять
                    if now - last_log >= 1.5:
                        downloaded = d.get("downloaded_bytes") or 0
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        speed = d.get("speed") or 0.0  # байт/с
                        eta = d.get("eta")  # сек
                        pct = (downloaded / total * 100.0) if total else 0.0
                        self.log.info(
                            "yt-dlp: downloading url=%s progress=%.1f%% bytes=%s/%s speed=%.1fkB/s eta=%ss",
                            url_short,
                            pct,
                            downloaded,
                            total or "unknown",
                            speed / 1024.0,
                            eta if eta is not None else "unknown",
                        )
                        last_log = now

                elif status == "finished":
                    filename = d.get("filename")
                    elapsed = d.get("elapsed")
                    self.log.info("yt-dlp: finished url=%s file=%s elapsed=%ss", url_short, filename, elapsed)

                elif status == "error":
                    self.log.error("yt-dlp: error url=%s detail=%s", url_short, d)

            # Базовые опции
            opts = dict(self.ydl_opts)
            opts.setdefault("noplaylist", True)
            opts.setdefault("restrictfilenames", True)
            opts.setdefault("format", "mp4/bestvideo+bestaudio/best")
            opts.setdefault("merge_output_format", "mp4")
            opts.setdefault("quiet", True)
            opts.setdefault("no_warnings", True)

            # Шаблон имени
            outtmpl = opts.get("outtmpl") or "%(title).200s-%(id)s.%(ext)s"
            opts["outtmpl"] = str(self.dir / outtmpl)

            # Прогресс-хуки
            hooks = list(opts.get("progress_hooks") or [])
            hooks.append(hook)
            opts["progress_hooks"] = hooks

            self.log.info("yt-dlp: start url=%s outdir=%s", url_short, self.dir)

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                filesize = info.get("filesize") or info.get("filesize_approx")
                title = info.get("title")
                ext = info.get("ext")

            t1 = time.monotonic()
            dur = t1 - t0
            if filesize:
                kb = filesize / 1024.0
                avg_kb_s = kb / dur if dur > 0 else 0.0
                self.log.info(
                    "yt-dlp: done url=%s file=%s size=%.1fKB duration=%.2fs avg=%.1fKB/s",
                    url_short,
                    filepath,
                    kb,
                    dur,
                    avg_kb_s,
                )
            else:
                self.log.info("yt-dlp: done url=%s file=%s duration=%.2fs", url_short, filepath, dur)

            return {
                "filepath": filepath,
                "title": title,
                "ext": ext,
                "filesize": filesize,
                "duration_sec": dur,
            }

        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, _run)
        except Exception as e:
            self.log.exception("yt-dlp: failed url=%s error=%s", url_short, e)
            raise
