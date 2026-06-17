"""FastAPI service exposing the LINE Messaging API webhook.

Production flow:
    LINE user -> LINE Platform -> POST /webhook (this app) -> handler -> reply

Extras:
  * Loading animation: as soon as a message arrives we show the animated "..."
    so the user knows น้องหอม is working while RAG runs.
  * Product carousel: product/price/browse queries get a carousel attached.

The handler may decide to stay SILENT (during a human-handoff window) — then we
send nothing, leaving the conversation to the human admin.

Security: every request is verified with the channel secret (X-Line-Signature).
"""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from loguru import logger

from .carousel import build_product_carousel
from .config import get_settings
from .handler import handle_message

settings = get_settings()
app = FastAPI(title="MooM HoM LINE RAG Assistant", version="0.3.0")

_line_config = Configuration(access_token=settings.line_channel_access_token)
_parser = WebhookParser(settings.line_channel_secret)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}


@app.post("/webhook")
async def webhook(request: Request, x_line_signature: str = Header(default="")):
    body = (await request.body()).decode("utf-8")

    try:
        events = _parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    with ApiClient(_line_config) as api_client:
        line_api = MessagingApi(api_client)
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
                _handle_text(line_api, event)

    return {"status": "ok"}


def _show_loading(line_api: MessagingApi, user_id: str) -> None:
    """Show the animated typing indicator (1:1 chats only). Best-effort."""
    if not user_id or user_id == "unknown":
        return
    try:
        line_api.show_loading_animation(
            ShowLoadingAnimationRequest(chat_id=user_id, loading_seconds=20)
        )
    except Exception as exc:  # never let the indicator break the reply
        logger.debug("loading animation skipped: {}", exc)


def _handle_text(line_api: MessagingApi, event: MessageEvent) -> None:
    user_id = getattr(event.source, "user_id", None) or "unknown"
    user_text = event.message.text

    _show_loading(line_api, user_id)

    result = handle_message(user_id, user_text)
    logger.info("user={} kind={} carousel={}", user_id, result.kind, result.show_products)

    # Silent during human handoff — let the admin take over.
    if result.reply is None:
        return

    messages = [TextMessage(text=result.reply)]
    if result.show_products:
        messages.append(build_product_carousel())

    line_api.reply_message(
        ReplyMessageRequest(reply_token=event.reply_token, messages=messages)
    )
