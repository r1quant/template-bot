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
        confidence_ratio: Confidence level as a ratio (0-1).
        stoploss: The price level to exit and limit loss.
        takeprofit: The target price level to exit and realize profit.
        metadata: Flexible dictionary for strategy-specific data.
    """

    value: float | None  # 1=buy, -1=sell, 0=away
    confidence_ratio: float | None = Field(None, ge=0, le=1)
    stoploss: float | None = None
    takeprofit: float | None = None
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
        include_last_candle: bool = False,
    ) -> StrategySignal:
        try:
            strategy_signals = await StrategyOMQS.getSignals(
                ticker=ticker, interval=interval, model=model, include_last_candle=include_last_candle, forceCache=forceCache
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
        include_last_candle: bool = False,
    ) -> StrategySignal:
        strategy_signals = await StrategyOMQSCrossPreviousStop.getSignals(
            ticker=ticker, interval=interval, model=model, include_last_candle=include_last_candle, forceCache=forceCache
        )

        try:
            return strategy_signals[0]
        except Exception:
            return None, None


# -----------------------------
# OMQS WITH CONFIDENCE LEVEL
# -----------------------------


class StrategyOMQSWithConfidence:
    """
    Calculate strategy signals based on the omqs signal.
    The 'signal' value is used has the main signal
    For example: when the signal is buy:
      - confidence_ratio=1.0 when the price is above previous_stop price
      - confidence_ratio=0.5 when the price is below the previous_stop price
      in your bot you can increase or reduce your margin based in the confidence value
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
                if signal and signal.id:
                    if include_last_candle:
                        current_signal = signal.response_dict["data"]["signal"]
                        current_stop = signal.response_dict["data"]["stop"]
                        signal_value = 1 if current_signal == 1 else -1 if current_signal == 0 else 0
                        stop = current_stop
                    else:
                        # the current signal is still in process, so we need to get the previous
                        previous_signal = signal.response_dict["data"]["previous_signal"]
                        previous_stop = signal.response_dict["data"]["previous_stop"]
                        signal_value = 1 if previous_signal == 1 else -1 if previous_signal == 0 else 0
                        stop = previous_stop

                    stop = float(stop)
                    current_price = float(signal.response_dict["data"]["price"])

                    if signal_value == 1:
                        confidence_ratio = 1 if current_price > stop else 0.5
                    elif signal_value == -1:
                        confidence_ratio = 1 if current_price < stop else 0.5
                    else:
                        confidence_ratio = None

                    results.append(StrategySignal(value=signal_value, source=signal, confidence_ratio=confidence_ratio))
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
        include_last_candle: bool = False,
    ) -> StrategySignal:
        strategy_signals = await StrategyOMQSWithConfidence.getSignals(
            ticker=ticker, interval=interval, model=model, include_last_candle=include_last_candle, forceCache=forceCache
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
    "strategy_omqs_with_confidence": StrategyOMQSWithConfidence,
    "strategy_1": StrategyOMQS,
    "strategy_2": StrategyOMQSCrossPreviousStop,
    "strategy_3": StrategyOMQSWithConfidence,
}
