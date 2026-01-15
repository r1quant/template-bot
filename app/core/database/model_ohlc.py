from datetime import datetime

import pandas as pd
from sqlalchemy import UniqueConstraint, select
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Field, Session, SQLModel

from app.lib.util_interval import IntervalHelper

from .database import engine

# ---------------------------------------------------------
# Model
# ---------------------------------------------------------


class OHLC(SQLModel, table=True):
    __tablename__ = "ohlc"
    id: int | None = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    interval: str
    date: datetime
    open: str
    high: str
    low: str
    close: str
    __table_args__ = (UniqueConstraint("ticker", "interval", "date", name="unique_ticker_interval_date"),)


# ---------------------------------------------------------
# Methods
# ---------------------------------------------------------


class ohlc_methods:
    def get_all(ticker=None, interval=None, return_dataframe=True):
        records = []
        with Session(engine) as session:
            if ticker and interval:
                interval = IntervalHelper.normalize(interval)
                stmt = select(OHLC).where(OHLC.ticker == ticker.upper()).where(OHLC.interval == interval)
            elif interval:
                interval = IntervalHelper.normalize(interval)
                stmt = select(OHLC).where(OHLC.interval == interval)
            elif ticker:
                stmt = select(OHLC).where(OHLC.ticker == ticker.upper())
            else:
                stmt = select(OHLC)

            records = session.scalars(stmt).all()

        if return_dataframe:
            list_records = (row.model_dump() for row in records)
            df = pd.DataFrame(list_records)
            if not df.empty:
                df = df.set_index("date")
                df = df.sort_index()
                df["date"] = df.index
            return df

        return records

    def upsert(values):
        with Session(engine) as session:
            for item in values:
                if "ticker" in item:
                    item["ticker"] = str(item["ticker"]).upper()
                if "interval" in item:
                    item["interval"] = IntervalHelper.normalize(item["interval"])

            stmt = insert(OHLC).values(values)
            upsert_stmt = stmt.on_conflict_do_update(
                # Column(s) used to detect conflicts
                index_elements=["ticker", "interval", "date"],
                # Values to update if conflict occurs
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                },
            )
            session.exec(upsert_stmt)
            session.commit()
            return values
        return []
