import httpx
import yfinance as yf

from app.settings import logging, settings

# ---------------------------------------------------------
# Interval Helper
# ---------------------------------------------------------


class IntervalHelper:
    m5 = "m5"
    m15 = "m15"
    h1 = "h1"
    h4 = "h4"
    d1 = "d1"

    def normalize(value):
        """
        help to maintain a single format for values in the database
        """
        v = IntervalHelper
        intervalDict = {
            5: v.m5, "m5": v.m5, "5": v.m5, # m5
            15: v.m15, "m15": v.m15, "15": v.m15, # m15
            60: v.h1, "1h": v.h1, "1H": v.h1, "h1": v.h1, "H1": v.h1, # h1
            240: v.h4, "4h": v.h4, "4H": v.h4, "h4": v.h4, "H4": v.h4, # h4
            "d1": v.d1, "1d": v.d1, "D1": v.d1, "1D": v.d1, "D": v.d1, # d1
        }  # fmt: off

        return intervalDict.get(value, value)

    def to_yahoo_format(interval):
        intervalDict = {
            5: "5m", "m5": "5m", "5": "5m",  # 5m
            15: "15m", "m15": "15m", "15": "15m",  # 15m
            60: "1h", "1H": "1h", "h1": "1h", "H1": "1h", # 1h
            "d1": "1d", "1d": "1d", "D1": "1d", "1D": "1d", "D": "1d",  # 1d
        }  # fmt: off
        return intervalDict.get(interval, interval)


# ---------------------------------------------------------
# Providers (yahoo-finance)
# ---------------------------------------------------------


class Providers:
    def yahoofinance(
        ticker,
        start=None,
        end=None,
        interval="1d",
        period="max",
        auto_adjust=False,
        normalize=True,
        progress=False,
        group_by="ticker",
    ):
        yf_data = yf.download(
            ticker,
            start=start,
            end=end,
            group_by=group_by,
            auto_adjust=auto_adjust,
            progress=progress,
            interval=interval,
            period=period,
        )

        if normalize:
            yf_data.drop(["Adj Close"], axis=1, level=1, inplace=True)
            yf_data.rename(columns={ "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)  # fmt: off
            yf_data.rename_axis("date", inplace=True)

        if type(ticker) is str:
            yf_data = yf_data[ticker]
            yf_data = yf_data.sort_index()
            yf_data["date"] = yf_data.index

        return yf_data


# ---------------------------------------------------------
# Notifier
# ---------------------------------------------------------


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
            logging.warning("telegram_chat_id is empty")
            return

        if not settings.notifier_telegram_chat_id:
            return

        if not message_text:
            logging.warning("telegram: message is empty")
            return

        url = f"https://api.telegram.org/bot{settings.notifier_telegram_token}/sendMessage"
        payload = {"chat_id": settings.notifier_telegram_chat_id, "text": message_text, "parse_mode": "Markdown"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=payload, timeout=10.0)
                response.raise_for_status()
                logging.info("telegram: message sent to chat")
                return "ok"
            except httpx.HTTPStatusError as e:
                logging.warning(f"telegram: background task failed: {e.response.status_code} - {e.response.text}")
                return "failed"
            except httpx.RequestError as e:
                logging.warning(f"telegram: background task network error: {e}")
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
            logging.warning("discord: message is empty")
            return

        url = f"{settings.notifier_discord_webhook_url}"
        payload = {"content": message_text}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, data=payload, timeout=10.0)
                response.raise_for_status()
                logging.info("discord: message sent to chat")
                return "ok"
            except httpx.HTTPStatusError as e:
                logging.warning(f"discrod: background task failed: {e.response.status_code} - {e.response.text}")
                return "failed"
            except httpx.RequestError as e:
                logging.warning(f"discord: background task network error: {e}")
                return "failed"
