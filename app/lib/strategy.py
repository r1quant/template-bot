from pydantic import BaseModel, Field

from app.database.model_signal import Signal
from app.lib.signal import SignalProvider

# -----------------------------
# HELPER: OUTPUT
# -----------------------------


class StrategySignal(BaseModel):
    """
    Standardize the output of trading strategies.

    Attributes:
        value: The direction of the signal (1: Buy, -1: Sell, 0: Away).
        strength: Confidence level as a percentage (1-100).
        stop_loss: The price level to exit and limit loss.
        take_profit: The target price level to exit and realize profit.
        metadata: Flexible dictionary for strategy-specific data.
    """

    value: float | None  # 1=buy, -1=sell, 0=away
    strength: float | None = Field(None, ge=1, le=100)  # eg. 20 = 20% confidence
    stop_loss: float | None = None
    take_profit: float | None = None
    metadata: dict | Signal = Field(default_factory=dict)
    source: Signal | None = None  # "source of truth" or the origin of the calculation.


# -----------------------------
# STRATEGY: OMQS
# -----------------------------


class StrategyOMQS:
    """
    Calculate strategy signals based on the omqs signal.
    """

    async def getSignals(
        ticker: str,
        interval: str,
        model: str,
        forceCache: bool = False,
        include_last_candle: bool = False,
    ) -> list[StrategySignal]:
        """
        Args:
            include_last_candle:
                If True: Include the current candle.
                Best used for execution seconds before the actual close
                If False (default): Ignore the current candle and use the last
                fully-closed signal. This ensures 'data stability' because the
                closing price is finalized and will not change.
        """
        signals = await SignalProvider.omqs(ticker=ticker, interval=interval, model=model, prev_n=10, forceCache=forceCache)
        results = []
        for signal in signals:
            try:
                if signal.id:
                    if include_last_candle:
                        cur = signal.response_dict["data"]["signal"]
                        results.append(StrategySignal(value=cur, source=signal))
                    else:
                        # the current signal is still in process, so we need to get the previous
                        prev = signal.response_dict["data"]["previous_signal"]
                        results.append(StrategySignal(value=prev, source=signal))

                else:
                    results.append(StrategySignal(value=None, source=signal))

            except Exception:
                results.append(StrategySignal(value=None, source=signal))

        return results

    async def getSignal(
        ticker: str,
        interval: str,
        model: str,
        forceCache: bool = False,
        include_open_candle: bool = True,
    ) -> StrategySignal:
        try:
            signals = await StrategyOMQS.getSignals(
                ticker=ticker, interval=interval, model=model, include_open_candle=include_open_candle, forceCache=forceCache
            )
            return signals[0]
        except Exception:
            return StrategySignal(value=None)


# -----------------------------
# MAP STRATEGIES
# -----------------------------

strategies = {
    "strategy_omqs": StrategyOMQS,
}
