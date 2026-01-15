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
