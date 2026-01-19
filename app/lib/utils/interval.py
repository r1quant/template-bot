from datetime import datetime, timedelta, timezone


class IntervalHelper:
    m5 = "m5"
    m15 = "m15"
    h1 = "h1"
    h4 = "h4"
    d1 = "d1"

    def normalize(value):
        """
        help to maintain a single format for values in the database
        """
        v = IntervalHelper
        intervalDict = {
            5: v.m5, "m5": v.m5, "5": v.m5, # m5
            15: v.m15, "m15": v.m15, "15": v.m15, # m15
            60: v.h1, "1h": v.h1, "1H": v.h1, "h1": v.h1, "H1": v.h1, # h1
            240: v.h4, "4h": v.h4, "4H": v.h4, "h4": v.h4, "H4": v.h4, # h4
            "d1": v.d1, "1d": v.d1, "D1": v.d1, "1D": v.d1, "D": v.d1, # d1
        }  # fmt: off

        return intervalDict.get(value, value)

    def to_yahoo_format(interval):
        intervalDict = {
            5: "5m", "m5": "5m", "5": "5m",  # 5m
            15: "15m", "m15": "15m", "15": "15m",  # 15m
            60: "1h", "1H": "1h", "h1": "1h", "H1": "1h", # 1h
            "d1": "1d", "1d": "1d", "D1": "1d", "1D": "1d", "D": "1d",  # 1d
        }  # fmt: off
        return intervalDict.get(interval, interval)

    def to_omqs_api_format(interval):
        intervalDict = {
            5: "5m", "m5": "5m", "5": "5m",  # 5m
            15: "15m", "m15": "15m", "15": "15m",  # 15m
            60: "1h", "1H": "1h", "h1": "1h", "H1": "1h", # 1h
            240: "4h", "4H": "4h", "h4": "4h", "H4": "4h", # 1h
            "d1": "1d", "1d": "1d", "D1": "1d", "1D": "1d", "D": "1d",  # 1d
        }  # fmt: off
        return intervalDict.get(interval, interval)

    def get_interval_in_seconds(interval):
        interval_map = {"m1": 60, "m5": 300, "m15": 900, "m30": 1800, "h1": 3600, "h4": 14400, "d1": 86400}

        if interval not in interval_map:
            raise ValueError(f"Unsupported interval: {interval}")

        return interval_map.get(interval, interval)

    def get_interval_datetime(
        dt: datetime,
        interval: str,
        next_n: int | None = None,
        prev_n: int | None = None,
        utc=0,
    ) -> datetime:
        """
        Floors a datetime object to the nearest specified interval using UTC
        to avoid local timezone shifts.
        """
        interval_seconds = IntervalHelper.get_interval_in_seconds(interval)

        # 1. Ensure we work with a UTC timestamp
        # If 'time' is naive, .replace(tzinfo=timezone.utc) treats it as UTC
        # If 'time' is aware, .astimezone(timezone.utc) converts it
        utc_time = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

        ts = utc_time.timestamp()

        # 2. Floor the timestamp
        floored_ts = (ts // interval_seconds) * interval_seconds

        if next_n is not None:
            floored_ts += interval_seconds * next_n

        if prev_n is not None:
            floored_ts -= interval_seconds * prev_n

        # 3. Convert back from UTC and remove tzinfo to return a naive object
        # Using datetime.fromtimestamp(ts, timezone.utc) is the modern Python 3.11+ way
        _utc = timezone(timedelta(hours=utc))
        result = datetime.fromtimestamp(floored_ts, tz=_utc)

        return result.replace(tzinfo=None)
