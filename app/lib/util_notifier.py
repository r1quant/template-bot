import httpx

from app.core.logging import logger
from app.core.settings import settings


class Notifier:
    async def send_telegram_message_async(message_text: str):
        """
        Sends a text message asynchronously to telegram
        This function will be run in the background.

        e.q: asyncio.create_task(send_telegram_message_async("hello bot"))
        """
        if not settings.notifier_telegram_token:
            return

        if settings.notifier_telegram_token and not settings.notifier_telegram_chat_id:
            logger.warning("telegram_chat_id is empty")
            return

        if not settings.notifier_telegram_chat_id:
            return

        if not message_text:
            logger.warning("telegram: message is empty")
            return

        url = f"https://api.telegram.org/bot{settings.notifier_telegram_token}/sendMessage"
        payload = {"chat_id": settings.notifier_telegram_chat_id, "text": message_text, "parse_mode": "Markdown"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=payload, timeout=10.0)
                response.raise_for_status()
                logger.info("telegram: message sent to chat")
                return "ok"
            except httpx.HTTPStatusError as e:
                logger.warning(f"telegram: background task failed: {e.response.status_code} - {e.response.text}")
                return "failed"
            except httpx.RequestError as e:
                logger.warning(f"telegram: background task network error: {e}")
                return "failed"

    async def send_discord_message_async(message_text: str):
        """
        Sends a text message asynchronously to discord
        This function will be run in the background.

        e.q: asyncio.create_task(send_discord_message_async("hello bot"))
        """
        if not settings.notifier_discord_webhook_url:
            return

        if not message_text:
            logger.warning("discord: message is empty")
            return

        url = f"{settings.notifier_discord_webhook_url}"
        payload = {"content": message_text}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=payload, timeout=10.0)
                response.raise_for_status()
                logger.info("discord: message sent to chat")
                return "ok"
            except httpx.HTTPStatusError as e:
                logger.warning(f"discrod: background task failed: {e.response.status_code} - {e.response.text}")
                return "failed"
            except httpx.RequestError as e:
                logger.warning(f"discord: background task network error: {e}")
                return "failed"
