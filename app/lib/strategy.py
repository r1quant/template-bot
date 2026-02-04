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
        value: The direction of the signal (1: Buy, -1: Sell, 0: Away)
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
                        current_signal = signal.response_dict["data"]["signal"]
                        current_signal = 1 if current_signal == 1 else -1 if current_signal == 0 else 0
                        results.append(StrategySignal(value=current_signal, source=signal))
                    else:
                        # the current signal is still in process, so we need to get the previous
                        previous_signal = signal.response_dict["data"]["previous_signal"]
                        previous_signal = 1 if previous_signal == 1 else -1 if previous_signal == 0 else 0
                        results.append(StrategySignal(value=previous_signal, source=signal))

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
            strategy_signals = await StrategyOMQS.getSignals(
                ticker=ticker, interval=interval, model=model, include_open_candle=include_open_candle, forceCache=forceCache
            )
            return strategy_signals[0]
        except Exception:
            return StrategySignal(value=None)


# -----------------------------
# OMQS CROSS PREVIOUS_STOP
# -----------------------------


class StrategyOMQSCrossPreviousStop:
    """
    Calculate strategy signals based on the omqs signal.
    The 'signal' value is ignored, it's only using the 'previous_stop'
    - Buy when the price is above previous_stop price
    - Sell when the price is below the previous_stop price
    """

    async def getSignals(
        ticker: str,
        interval: str,
        model: str,
        forceCache: bool = False,
        include_last_candle: bool = False,
    ) -> list[StrategySignal]:
        signals = await SignalProvider.omqs(ticker=ticker, interval=interval, model=model, prev_n=10, forceCache=forceCache)
        results = []
        for signal in signals:
            try:
                if signal.id:
                    if not include_last_candle:
                        current_price = signal.response_dict["data"]["price"]
                        previous_stop = signal.response_dict["data"]["previous_stop"]
                        if current_price >= previous_stop:
                            results.append(StrategySignal(value=1, source=signal))  # buy
                        else:
                            results.append(StrategySignal(value=-1, source=signal))  # sell
                    else:
                        current_price = signal.response_dict["data"]["price"]
                        current_stop = signal.response_dict["data"]["stop"]
                        if current_price >= current_stop:
                            results.append(StrategySignal(value=1, source=signal))  # buy
                        else:
                            results.append(StrategySignal(value=-1, source=signal))  # sell
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
        strategy_signals = await StrategyOMQSCrossPreviousStop.getSignals(
            ticker=ticker, interval=interval, model=model, include_open_candle=include_open_candle, forceCache=forceCache
        )

        try:
            return strategy_signals[0]
        except Exception:
            return None, None


# -----------------------------
# OMQS WITH STRENGTH
# -----------------------------


class StrategyOMQSWithStrength:
    """
    Calculate strategy signals based on the omqs signal.
    The 'signal' value is used has the main signal
    For example: when the signal is buy:
      - strength=100% when the price is above previous_stop price
      - strength=50% when the price is below the previous_stop price
      in your bot you can increase or reduce your margin based in the strength value
    """

    async def getSignals(
        ticker: str,
        interval: str,
        model: str,
        forceCache: bool = False,
        include_last_candle: bool = False,
    ) -> list[StrategySignal]:
        signals = await SignalProvider.omqs(ticker=ticker, interval=interval, model=model, prev_n=10, forceCache=forceCache)
        results = []
        for signal in signals:
            try:
                if signal.id:
                    if include_last_candle:
                        current_signal = signal.response_dict["data"]["signal"]
                        current_price = signal.response_dict["data"]["price"]
                        current_stop = signal.response_dict["data"]["stop"]
                        strength = 100 if current_price > current_stop else 50
                        current_signal = 1 if current_signal == 1 else -1 if current_signal == 0 else 0
                        results.append(StrategySignal(value=current_signal, source=signal, strength=strength))
                    else:
                        # the current signal is still in process, so we need to get the previous
                        previous_signal = signal.response_dict["data"]["previous_signal"]
                        current_price = signal.response_dict["data"]["price"]
                        previous_stop = signal.response_dict["data"]["previous_stop"]
                        strength = 100 if current_price > previous_stop else 50
                        previous_signal = 1 if previous_signal == 1 else -1 if previous_signal == 0 else 0
                        results.append(StrategySignal(value=previous_signal, source=signal, strength=strength))
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
        strategy_signals = await StrategyOMQSCrossPreviousStop.getSignals(
            ticker=ticker, interval=interval, model=model, include_open_candle=include_open_candle, forceCache=forceCache
        )

        try:
            return strategy_signals[0]
        except Exception:
            return None, None


# -----------------------------
# MAP STRATEGIES
# -----------------------------

strategies = {
    "strategy_omqs": StrategyOMQS,
    "strategy_omqs_cross_previous_stop": StrategyOMQSCrossPreviousStop,
    "strategy_omqs_with_strength": StrategyOMQSWithStrength,
}
