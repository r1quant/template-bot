import asyncio

from fastapi import APIRouter

from app.lib.utils.notifier import Notifier

router = APIRouter()

# ---------------------------------------------------------
# Router: Notifications
# ---------------------------------------------------------


@router.get("/telegram")
async def send_telegram(msg: str):
    message = msg or "hello from template-bot"
    example_code_snippet = '{"status": "success" }}'
    message += f"\n```json\n{example_code_snippet}\n```"
    asyncio.create_task(Notifier.send_telegram_message_async(message))
    return {"message": message}


@router.get("/discord")
async def send_discord(msg: str):
    message = msg or "hello from template-bot"
    asyncio.create_task(Notifier.send_discord_message_async(message))
    return {"message": message}
