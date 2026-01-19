import asyncio
import json

from app.core.logging import logger
from app.database.methods import db
from app.database.model_signal import Signal
from app.lib.api.omqs import OmqsAPI
from app.lib.utils.interval import IntervalHelper
from app.lib.utils.notifier import Notifier

# ---------------------------------------------------------
# OMQS Provider
# ---------------------------------------------------------


def omqs_signal_notify_telegram(signals: list, ticker: str, interval: str):
    try:
        icons_msg = ""
        if signals[1].id:
            icons_msg += OmqsAPI.get_signal_icon(signals[1].response_dict["data"]["previous_signal"])

        icons_msg += OmqsAPI.get_signal_icon(signals[0].response_dict["data"]["previous_signal"])
        icons_msg += " ↦ "
        icons_msg += OmqsAPI.get_signal_icon(signals[0].response_dict["data"]["signal"])

        price = signals[0].response_dict["data"]["price"]
        stop = signals[0].response_dict["data"]["stop"]
        side_price_icon = "⏈" if price >= stop else "⏇"

        message = ""
        message += f"{str(ticker).upper()} {interval} {icons_msg} ${price} {side_price_icon}"

        # Notifier.send_telegram_message(message)
        asyncio.create_task(Notifier.send_telegram_message_async(message))

    except Exception as e:
        logger.error(f"failed to omqs_notify_telegram {e}")


class SignalProvider:
    async def omqs(ticker: str, interval: str, model: str, prev_n: int = 10, forceCache: bool = False):
        """
        - get latest signals from the database
        - if not found the last signal then
          - it'll get the signal from the om-qs.com and store in the database
        """
        interval = IntervalHelper.normalize(interval)
        signals = db.signals.latest(
            ticker=ticker,
            interval=interval,
            provider="omqs",
            model=model,
            prev_n=prev_n,
        )

        try:
            if forceCache is False:
                if signals[0].id is None:
                    timeframe = IntervalHelper.to_omqs_api_format(interval=interval)
                    # response = OmqsAPI.generate_fake_signal(ticker=ticker, timeframe=interval, model=model)
                    response = OmqsAPI.get_signal(ticker=ticker, timeframe=timeframe, model=model)
                    logger.info(f"get signal from om-qs.com: {ticker=} {timeframe=} response={response}")
                    if response is not None:
                        signal = Signal(
                            ticker=ticker, interval=interval, provider="omqs", model=model, response=json.dumps(response)
                        )
                        record = db.signals.save(signal)
                        if record.id:
                            signals[0] = record
                            print(f"[GET SIGNAL] {ticker=} {timeframe=}")
                            omqs_signal_notify_telegram(signals, ticker=ticker, interval=interval)

                    else:
                        logger.error(f"response returns empty: {ticker=} {timeframe=}")

        except Exception as e:
            logger.error(f"error to get signals from SignalProvider.omqs: {ticker=} {interval=} {e}")

        return signals
