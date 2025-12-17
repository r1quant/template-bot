import asyncio
from datetime import UTC, datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import config
from app.database import db
from app.lib.utils import Notifier
from app.settings import logger, settings
from app.tasks.refresh_ticker import refresh_ticker_by_interval

# ---------------------------------------------------------
# Cronjob: 1 minute
# ---------------------------------------------------------


async def cron_1minute():
    logger.info("executing cronjob 1minute")
    asyncio.create_task(Notifier.send_telegram_message_async("executing cronjob: 1hour"))


# ---------------------------------------------------------
# Cronjob: 10 minutes
# ---------------------------------------------------------


async def cron_10minutes():
    logger.info("executing cronjob: cron_10minutes")
    logger.info(f"tickers: {config.cronjob.refresh_tickers}")
    now_utc = datetime.now(timezone.utc)
    db.settings.set("cronjob_m10_updated_at", now_utc.strftime("%Y-%m-%d %H:%M:%S"))

    for ticker in config.cronjob.refresh_tickers:
        refresh_ticker_by_interval(ticker=ticker, interval="1h")

    asyncio.create_task(Notifier.send_telegram_message_async("executed cronjob: 10minutes"))


# ---------------------------------------------------------
# Cronjob: 1 hour
# ---------------------------------------------------------


async def cron_1hour():
    logger.info("executing cronjob: 1hour")
    logger.info(f"tickers: {config.cronjob.refresh_tickers}")
    now_utc = datetime.now(timezone.utc)
    db.settings.set("cronjob_h1_updated_at", now_utc.strftime("%Y-%m-%d %H:%M:%S"))

    for ticker in config.cronjob.refresh_tickers:
        refresh_ticker_by_interval(ticker=ticker, interval="1h")

    asyncio.create_task(Notifier.send_telegram_message_async("executed cronjob: 1hour"))


# ---------------------------------------------------------
# Cronjob: 1 day
# ---------------------------------------------------------


async def cron_1day():
    logger.info("executing cronjob: 1day")
    now_utc = datetime.now(timezone.utc)
    db.settings.set("cronjob_d1_updated_at", now_utc.strftime("%Y-%m-%d %H:%M:%S"))

    for ticker in config.cronjob.refresh_tickers:
        refresh_ticker_by_interval(ticker=ticker, interval="1d")

    asyncio.create_task(Notifier.send_telegram_message_async("executed cronjob: 1day"))


# ---------------------------------------------------------
# Cronjob: initialize
# ---------------------------------------------------------

scheduler = AsyncIOScheduler(timezone=UTC)


def cron_initialize():
    if settings.enabled_cron:
        logger.info(f"cronjob is enabled at {datetime.now(UTC)}")

        # Every 1 minutes
        # scheduler.add_job(cron_1minute, CronTrigger(day="*", hour="*", minute="*", timezone="UTC"))

        # Every 10 minutes (with 5s delay)
        # scheduler.add_job(cron_10minutes, CronTrigger(day="*", hour="*", minute="*/10", second="5", timezone="UTC"))

        # Every 1 hours (with 30s delay)
        scheduler.add_job(cron_1hour, CronTrigger(day="*", hour="*/1", minute="0", second="20", timezone="UTC"))

        # Every 1 day (with 1min delay)
        scheduler.add_job(cron_1day, CronTrigger(day="*", hour="0", minute="1", timezone="UTC"))

        scheduler.start()
    else:
        logger.info("cronjob is disabled")


def cron_shutdown():
    scheduler.shutdown()
