from datetime import datetime

import pandas as pd
from pydantic import field_validator
from sqlalchemy import UniqueConstraint, desc, select
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Field, Session, SQLModel

from app.database.database import engine
from app.lib.utils.interval import IntervalHelper

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

    @field_validator("ticker", mode="before")
    @classmethod
    def force_ticker_lowercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("interval", mode="before")
    @classmethod
    def force_interval_lowercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v

    __table_args__ = (UniqueConstraint("ticker", "interval", "date", name="unique_ticker_interval_date"),)


# ---------------------------------------------------------
# Methods
# ---------------------------------------------------------


class ohlc_methods:
    def get_all(ticker=None, interval=None, return_dataframe=True, limit: int = 200):
        records = []
        with Session(engine) as session:
            stmt = select(OHLC)

            if ticker:
                stmt = stmt.where(OHLC.ticker == str(ticker).lower())

            if interval:
                interval = IntervalHelper.normalize(interval)
                stmt = stmt.where(OHLC.interval == str(interval).lower())

            stmt = stmt.order_by(desc(OHLC.date))
            stmt = stmt.limit(limit)

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
                item["ticker"] = str(item["ticker"]).lower()
                item["interval"] = IntervalHelper.normalize(item["interval"]).lower()

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
