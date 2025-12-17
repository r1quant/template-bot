from datetime import datetime

from sqlalchemy import UniqueConstraint, select
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Field, Session, SQLModel, create_engine

from app.settings import settings

# ---------------------------------------------------------
# Models
# ---------------------------------------------------------


class Settings(SQLModel, table=True):
    __tablename__ = "settings"
    key: str = Field(primary_key=True, unique=True, nullable=False)
    value: str = Field(nullable=False)


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


class settings_methods:
    def all():
        with Session(engine) as session:
            stmt = select(Settings)
            rows = session.scalars(stmt).all()
            if rows:
                result_dict = {row.key: row.value for row in rows}
                return result_dict

            return {}

    def get(key):
        with Session(engine) as session:
            stmt = select(Settings).where(Settings.key == key)
            row = session.scalars(stmt).first()
            if row:
                return row.value
            return None

    def set(key, value):
        with Session(engine) as session:
            stmt = select(Settings).where(Settings.key == key)
            setting = session.scalars(stmt).first()
            if setting:
                setting.value = value  # update
            else:
                setting = Settings(key=key, value=value)  # create
            session.add(setting)
            session.commit()
            session.refresh(setting)

    def delete(key):
        with Session(engine) as session:
            stmt = select(Settings).where(Settings.key == key)
            setting = session.scalars(stmt).first()
            if setting:
                session.delete(setting)
                session.commit()
            return True


class ohlc_methods:
    def get_all(ticker=None, interval=None):
        records = []
        with Session(engine) as session:
            if ticker:
                stmt = select(OHLC).where(OHLC.ticker == ticker)
            if ticker and interval:
                stmt = select(OHLC).where(OHLC.ticker == ticker, OHLC.interval == interval)
            else:
                stmt = select(OHLC)

            records = session.scalars(stmt).all()
        return records

    def upsert(values):
        with Session(engine) as session:
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


class db:
    settings = settings_methods
    ohlc = ohlc_methods


# ---------------------------------------------------------
# Connection
# ---------------------------------------------------------

connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_path, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
