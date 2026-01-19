from app.lib.signal import SignalProvider


class StrategyOMQSSignal:
    async def getSignals(ticker: str, interval: str, model: str, isOpenCandle: bool = True, forceCache: bool = False):
        signals = await SignalProvider.omqs(ticker=ticker, interval=interval, model=model, prev_n=10, forceCache=forceCache)
        final_signals = []
        for signal in signals:
            try:
                if signal.id:
                    cur = signal.response_dict["data"]["signal"]
                    prev = signal.response_dict["data"]["previous_signal"]
                    if isOpenCandle:
                        # the current signal is still in process, so we need to get the previous
                        final_signals.append(prev)
                    else:
                        final_signals.append(cur)

                else:
                    final_signals.append(None)

            except Exception:
                final_signals.append(None)

        return final_signals

    async def getSignal(ticker: str, interval: str, model: str, isOpenCandle: bool = True, forceCache: bool = False):
        try:
            signals = await StrategyOMQSSignal.getSignals(
                ticker=ticker, interval=interval, model=model, isOpenCandle=isOpenCandle, forceCache=forceCache
            )
            return signals[0]
        except Exception:
            return None


strategies = {
    "strategy_1": StrategyOMQSSignal,
}
