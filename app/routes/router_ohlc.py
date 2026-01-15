import pandas as pd
from fastapi import APIRouter

from app.core.database.methods import db
from app.lib.util_interval import IntervalHelper
from app.tasks.runner_ticker import refresh_ticker_by_interval

router = APIRouter()

# ---------------------------------------------------------
# Router: OHLC
# ---------------------------------------------------------


@router.get("/ohlc/{ticker}/{interval}")
def ohlc_all_by_ticker(ticker: str, interval: str):
    interval = IntervalHelper.normalize(interval)
    records = db.ohlc.get_all(ticker=ticker, interval=interval, return_dataframe=True)

    if isinstance(records, pd.DataFrame):
        return records.to_dict(orient="records")

    return records


@router.get("/ohlc/{ticker}/{interval}/refresh")
def ohlc_refresh(ticker: str, interval: str):
    interval = IntervalHelper.normalize(interval)
    records = refresh_ticker_by_interval(ticker=ticker, interval=interval)

    if isinstance(records, pd.DataFrame):
        return records.to_dict(orient="records")

    return records
