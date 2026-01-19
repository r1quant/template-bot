import yfinance as yf


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
