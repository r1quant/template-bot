from datetime import datetime, timedelta

from app.database import db
from app.lib.utils import IntervalHelper, Providers


def refresh_ticker_by_interval(ticker="BTC-USD", interval="1h", return_dataframe=True):
    provider = "yahoo"
    interval = IntervalHelper.to_yahoo_format(interval)

    if interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]:
        start = datetime.now() - timedelta(days=2)
    elif interval in ["1d"]:
        start = datetime.now() - timedelta(days=7)
    elif interval in ["5d"]:
        start = datetime.now() - timedelta(days=15)
    else:
        start = datetime.now() - timedelta(days=100)

    ticker_name = ticker
    ticker_interval = interval
    ticker_start = start.strftime("%Y-%m-%d")

    if provider == "yahoo":
        ticker_data = Providers.yahoofinance(ticker_name, ticker_start, interval=ticker_interval)

    records = []

    if len(ticker_data) > 0:
        # update last 10 candles
        candles = []
        for _, row in ticker_data.iloc[-10:].iterrows():
            candles.append(
                {
                    "ticker": ticker_name,
                    "interval": IntervalHelper.normalize(ticker_interval),
                    "date": datetime.strptime(row["date"].strftime("%Y-%m-%d %H:%M:00"), "%Y-%m-%d %H:%M:%S"),
                    "open": str(row["open"]),
                    "high": str(row["high"]),
                    "low": str(row["low"]),
                    "close": str(row["close"]),
                }
            )
        db.ohlc.upsert(candles)
        records = candles
        records = sorted(records, key=lambda row: row["date"], reverse=True)

    if return_dataframe:
        return ticker_data

    return ticker_data
