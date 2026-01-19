import json
from datetime import datetime, timezone
from json import JSONDecodeError
from typing import Optional

from pydantic import field_validator
from sqlalchemy import UniqueConstraint, desc, select
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Field, Session, SQLModel

from app.database.database import engine
from app.lib.utils.interval import IntervalHelper

# ---------------------------------------------------------
# Model
# ---------------------------------------------------------


class Signal(SQLModel, table=True):
    __tablename__ = "signals"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    ticker: str
    interval: str
    date: datetime
    response: str

    updated: datetime = Field(
        # default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    @property
    def response_dict(self) -> dict:
        # 1. Immediate return if already a dict
        if isinstance(self.response, dict):
            return self.response

        # 2. Check for empty or non-string values
        if not self.response or not isinstance(self.response, str):
            return {}

        # 3. Robust parsing with error handling
        try:
            return json.loads(self.response)
        except (JSONDecodeError, TypeError):
            # Return an empty dict if the JSON is malformed
            return {}

    @field_validator("response", mode="before")
    @classmethod
    def force_response_str(cls, v: str | dict) -> str:
        if isinstance(v, dict):
            return json.dumps(v)
        return v

    @field_validator("model", mode="before")
    @classmethod
    def force_model_lowercase(cls, v: str) -> str:
        if isinstance(v, str):
            return v.lower()
        return v

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

    __table_args__ = (
        UniqueConstraint(
            "date",
            "ticker",
            "interval",
            "provider",
            "model",
            name="unique_date_ticker_interval_provider_model",
        ),
    )


# ---------------------------------------------------------
# Methods
# ---------------------------------------------------------


class signals_methods:
    def latest(
        ticker: str,
        interval: str,
        provider: str,
        model: str,
        prev_n: int = 12,
    ):
        records = []
        with Session(engine) as session:
            start = IntervalHelper.get_interval_datetime(datetime.now(timezone.utc), interval, utc=0, prev_n=prev_n)
            interval = IntervalHelper.normalize(interval)

            stmt = select(Signal)
            stmt = stmt.where(Signal.provider == str(provider).lower())
            stmt = stmt.where(Signal.ticker == str(ticker).lower())
            stmt = stmt.where(Signal.interval == str(interval).lower())
            stmt = stmt.where(Signal.model == str(model).lower())
            stmt = stmt.where(Signal.date >= start)
            stmt = stmt.order_by(desc(Signal.date))
            stmt = stmt.limit(prev_n)

            records = session.scalars(stmt).all()

        # all interval dates
        interval_dates = []
        for n in range(0, prev_n):
            interval_dates.append(IntervalHelper.get_interval_datetime(datetime.now(timezone.utc), interval, utc=0, prev_n=n))

        # merge interval dates with records
        recordsmapbydate = {item.date: item for item in records}
        records = [recordsmapbydate.get(dt, Signal(date=dt)) for dt in interval_dates]

        return records

    def search(
        ticker: str | None,
        provider: str | None,
        interval: str | None,
        model: str | None,
        start: datetime = None,
        limit: int = 10,
    ):
        records = []
        with Session(engine) as session:
            stmt = select(Signal)

            if ticker is not None:
                stmt = stmt.where(Signal.ticker == str(ticker).lower())
            if interval is not None:
                interval = IntervalHelper.normalize(interval)
                stmt = stmt.where(Signal.interval == str(interval).lower())
            if provider is not None:
                stmt = stmt.where(Signal.provider == str(provider).lower())
            if model is not None:
                stmt = stmt.where(Signal.model == str(model).lower())
            if start is not None:
                stmt = stmt.where(Signal.date >= start)
            stmt = stmt.order_by(desc(Signal.date))
            stmt = stmt.limit(limit)

            records = session.scalars(stmt).all()
        return records

    def upsert(values):
        # convert to a list of dict
        values = [
            item.model_dump(include={"provider", "ticker", "model", "interval", "date", "response"})
            if isinstance(item, Signal)
            else item
            for item in values
        ]

        for item in values:
            if isinstance(item.get("response"), dict):
                item["response"] = json.dumps(item["response"])

            item["provider"] = str(item["provider"]).lower()
            item["model"] = str(item["model"]).lower()
            item["ticker"] = str(item["ticker"]).lower()
            item["interval"] = IntervalHelper.normalize(item["interval"])
            item["date"] = IntervalHelper.get_interval_datetime(datetime.now(timezone.utc), item["interval"], utc=0)
            item["updated"] = datetime.now(timezone.utc)

        with Session(engine) as session:
            stmt = insert(Signal).values(values)

            # add the upsert logic and the returning clause
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["provider", "model", "ticker", "interval", "date"],
                set_={"response": stmt.excluded.response, "updated": datetime.now(timezone.utc)},
            ).returning(Signal)

            # execute and fetch all returned rows
            result = session.scalars(upsert_stmt, execution_options={"populate_existing": True})
            saved_records = result.all()
            session.commit()
            for record in saved_records:
                session.refresh(record)

            return saved_records
        return []

    def save(value):
        records = signals_methods.upsert([value])
        return records[0]
