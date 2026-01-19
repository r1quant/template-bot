import random

import requests

from app.core.logging import logger
from app.core.settings import settings

# ---------------------------------------------------------
# OMQS API
# ---------------------------------------------------------


class OmqsAPI:
    uri = "https://om-qs.com/api/v1/models/"

    def generate_fake_signal(ticker: str, timeframe: str, model: str, min: int = 90000, max: int = 100000):
        """this method is used for test"""
        response = {
            "status": "success",
            "model": model,
            "ticker": ticker,
            "timeframe": timeframe,
            "data": {
                "stop": random.uniform(min, max),
                "signal": random.choice([0, 1]),
                "previous_stop": random.uniform(min, max),
                "previous_signal": random.choice([0, 1]),
                "price": random.uniform(min, max),
            },
        }

        return response

    def get_signal(ticker: str, timeframe: str, model: str, api_key: str | None = None):
        api_key = api_key or settings.omqs_api_key
        headers = {"Authorization": f"Api-Key {api_key}"}
        payload = {"ticker": ticker, "timeframe": timeframe, "model": model}
        logger.info(f" omqs-api: {payload=}")

        try:
            response = requests.post(OmqsAPI.uri, headers=headers, json=payload)
            status = response.status_code
            logger.info(f" omqs-api: {status=}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f" omqs-api: {type(data)} {data=}")
                return data
            else:
                logger.info(f" omqs-api: error {response.status_code}] {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            logger.info(f" omqs-api: error Connection error. Is the server running at {OmqsAPI.uri}?")

        except requests.exceptions.RequestException as e:
            logger.info(f" omqs-api: error Request exception: {e}")

    def get_signal_icon(value):
        if value >= 1:
            return "🟢"
        elif value <= 0:
            return "🔴"
        else:
            return "⚪️"
