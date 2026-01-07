from __future__ import annotations
from typing import Annotated

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Config
from app.utils.logger import setup_logger


cfg = Config().get_config()
log = setup_logger(cfg.get("LOG_LEVEL", "INFO"))
bot = Bot(token=cfg["BOT_TOKEN"])
app = FastAPI(title="Hidden Protocol Bot API", version="1.0.0")


async def verify_token(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None
) -> None:
    """Проверяем заголовок авторизации на валидность токена."""

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or token != cfg["API_KEY_JWT"]:
        log.warning("HTTP API: unauthorized access attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class SendMessageRequest(BaseModel):
    """Описание входных данных запроса на отправку сообщения."""

    chat_id: Annotated[int | str, Field(description="ID или username чата Telegram")]
    text: Annotated[str, Field(min_length=1, max_length=4096, description="Текст сообщения")]
    thread_id: Annotated[int | None, Field(default=None, description="ID треда для форумов")] = None
    parse_mode: Annotated[str | None, Field(default=None, description="Parse mode Telegram")] = None
    disable_notification: Annotated[bool, Field(default=False, description="Не уведомлять получателя")] = False


class SendMessageResponse(BaseModel):
    """Ответ API c информацией об отправленном сообщении."""

    message: bool = True
    chat_id: int | str
    thread_id: int | None = None
    message_id: int


@app.get("/health", response_model=dict)
async def healthcheck() -> dict:
    """Простейший эндпоинт для проверки живости API."""

    return {"message": "ok"}


@app.post("/send-message", response_model=SendMessageResponse)
async def send_message(
    payload: SendMessageRequest, _authorized: None = Depends(verify_token)
) -> SendMessageResponse:
    """Отправляем текстовое сообщение через бота в чат или тред."""

    # Собираем аргументы для метода бота send_message
    send_kwargs = dict(
        chat_id=payload.chat_id,
        text=payload.text,
        disable_notification=payload.disable_notification,
    )
    if payload.parse_mode:
        send_kwargs["parse_mode"] = payload.parse_mode
    if payload.thread_id is not None:
        send_kwargs["message_thread_id"] = payload.thread_id

    try:
        message = await bot.send_message(**send_kwargs)
    except TelegramBadRequest as exc:  # Неверные параметры чата/треда/формата
        log.warning("HTTP API: bad request for chat %s: %s", payload.chat_id, exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TelegramAPIError as exc:
        log.error("HTTP API: telegram api error for chat %s: %s", payload.chat_id, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Telegram API error") from exc

    log.info(
        "HTTP API: message sent chat=%s thread=%s message_id=%s",
        payload.chat_id,
        payload.thread_id,
        message.message_id,
    )

    return SendMessageResponse(
        chat_id=payload.chat_id,
        thread_id=payload.thread_id,
        message_id=message.message_id,
    )


@app.on_event("shutdown")
async def _shutdown() -> None:
    """Закрываем сессию бота при завершении работы API."""

    await bot.session.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.http_api:app",
        host=cfg.get("HOST", "0.0.0.0"),
        port=cfg.get("PORT", 8000),
        reload=False,
    )