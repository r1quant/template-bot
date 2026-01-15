import asyncio

from fastapi import APIRouter

from app.lib.util_notifier import Notifier

router = APIRouter()

# ---------------------------------------------------------
# Router: Notifications
# ---------------------------------------------------------


@router.get("/telegram")
async def send_telegram(msg: str):
    message = msg or "hello from template-bot"
    asyncio.create_task(Notifier.send_telegram_message_async(message))
    return {"message": message}


@router.get("/discord")
async def send_discord(msg: str):
    message = msg or "hello from template-bot"
    asyncio.create_task(Notifier.send_discord_message_async(message))
    return {"message": message}
