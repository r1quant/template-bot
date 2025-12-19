import asyncio
import os
from collections import deque
from contextlib import asynccontextmanager
from datetime import date, timedelta

import aiofiles
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from app.cronjob import cron_d1, cron_h1, cron_initialize, cron_shutdown
from app.database import create_db_and_tables, db
from app.lib.utils import IntervalHelper, Notifier
from app.settings import settings
from app.tasks.refresh_ticker import refresh_ticker_by_interval

# ---------------------------------------------------------
# Events: lifespan
# ---------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup...
    cron_initialize()
    create_db_and_tables()
    yield
    # shutdown...
    cron_shutdown()


# ---------------------------------------------------------
# FastApi
# ---------------------------------------------------------

app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "enabled_cron": settings.enabled_cron,
    }


# ---------------------------------------------------------
# Routes: Bot Settings
# ---------------------------------------------------------


@app.get("/settings")
def all_settings():
    values = db.settings.all()
    return {"settings": values}


@app.get("/settings/:key")
def get_settings(key: str):
    value = db.settings.get(key)
    return {"key": key, "value": value}


@app.delete("/settings/:key")
def delete_settings(key: str):
    value = db.settings.delete(key)
    return {"key": key, "value": value}


@app.post("/settings")
def save_settings(key: str, value: str):
    db.settings.set(key, value)
    return {"key": key, "value": value}


# ---------------------------------------------------------
# Routes: Logs
# ---------------------------------------------------------


@app.get("/logs", response_class=PlainTextResponse)
async def show_logs(lines: int = 1000, prev: int = 0):
    log_file_path = f"data/{settings.log_file.replace('.log', '')}.log"

    if prev > 0:
        prev_date = (date.today() - timedelta(days=prev)).strftime("%Y-%m-%d")
        log_file_path = f"{log_file_path}.{prev_date}"

    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=404, detail=f"Log file '{log_file_path}' not found.")

    try:
        async with aiofiles.open(log_file_path, mode="r", encoding="utf-8") as f:
            # Read all lines, but deque only keeps the last X in memory
            # This is efficient for large files as it avoids a full list in memory.
            last_lines = deque(await f.readlines(), maxlen=max(10, lines))

        content = "".join(last_lines)

        return PlainTextResponse(content=content, headers={"Content-Disposition": "inline; filename=app.log"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")


# ---------------------------------------------------------
# Routes: Cronjob
# ---------------------------------------------------------


@app.get("/cronjob/{interval}")
async def cronjob_run(interval: str):
    if interval == "h1":
        await cron_h1()

    if interval == "d1":
        await cron_d1()

    return {"interval": interval}


# ---------------------------------------------------------
# Routes: Notifications
# ---------------------------------------------------------


@app.get("/telegram")
async def send_telegram(msg: str):
    message = msg or "hello from template-bot"
    asyncio.create_task(Notifier.send_telegram_message_async(message))
    return {"message": message}


@app.get("/discord")
async def send_discord(msg: str):
    message = msg or "hello from template-bot"
    asyncio.create_task(Notifier.send_discord_message_async(message))
    return {"message": message}


# ---------------------------------------------------------
# Routes: OHLC
# ---------------------------------------------------------


@app.get("/ohlc/{ticker}/{interval}")
def ohlc_all_by_ticker(ticker: str, interval: str):
    interval = IntervalHelper.normalize(interval)
    records = db.ohlc.get_all(ticker=ticker, interval=interval, return_dataframe=True)

    if isinstance(records, pd.DataFrame):
        return records.to_dict(orient="records")

    return records


@app.get("/ohlc/{ticker}/{interval}/refresh")
def ohlc_refresh(ticker: str, interval: str):
    interval = IntervalHelper.normalize(interval)
    records = refresh_ticker_by_interval(ticker=ticker, interval=interval)

    if isinstance(records, pd.DataFrame):
        return records.to_dict(orient="records")

    return records


# ---------------------------------------------------------
# Routes: Health
# ---------------------------------------------------------


@app.get("/health")
async def health_check():
    return {"status": "ok"}
