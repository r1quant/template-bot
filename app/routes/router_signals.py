from fastapi import APIRouter

from app.database.methods import db
from app.lib.strategy import StrategyOMQS, StrategyOMQSCrossPreviousStop, StrategyOMQSWithConfidence
from app.lib.utils.interval import IntervalHelper

router = APIRouter()

# ---------------------------------------------------------
# Router: Signals
# ---------------------------------------------------------


@router.get("/signals/search")
def signals_search(
    ticker: str | None = None,
    interval: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    limit: int = 12,
):
    interval = IntervalHelper.normalize(interval)
    records = db.signals.search(provider=provider, model=model, ticker=ticker, interval=interval, limit=limit)
    return {"status": "ok", "records": records}


@router.get("/signals/latest")
def signals_latest(ticker: str, interval: str, provider: str, model: str, prev_n: int = 12):
    interval = IntervalHelper.normalize(interval)
    records = db.signals.latest(provider=provider, model=model, ticker=ticker, interval=interval, prev_n=prev_n)
    return {"status": "ok", "records": records}


@router.get("/signals/strategies/omqs/")
async def strategies_omqs(ticker: str, interval: str, model: str):
    signals = await StrategyOMQS.getSignals(ticker=ticker, interval=interval, model=model)
    return {"status": "ok", "signal": signals[0], "signals": [s.value for s in signals]}


@router.get("/signals/strategies/omqscrosspreviousstop/")
async def strategies_omqscrosspreviousstop(ticker: str, interval: str, model: str):
    signals = await StrategyOMQSCrossPreviousStop.getSignals(ticker=ticker, interval=interval, model=model)
    return {"status": "ok", "signal": signals[0], "signals": [s.value for s in signals]}


@router.get("/signals/strategies/omqswithconfidence/")
async def strategies_omqswithconfidence(ticker: str = "BTCUSDT", interval: str = "H4", model: str = "crypto"):
    signals = await StrategyOMQSWithConfidence.getSignals(ticker=ticker, interval=interval, model=model)
    return {"status": "ok", "signal": signals[0], "signals": [s.value for s in signals]}
