import asyncio
from datetime import UTC, datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import config
from app.core.logging import logger
from app.core.settings import settings
from app.database.methods import db
from app.lib.utils.notifier import Notifier
from app.tasks.runner_ticker import refresh_ticker_by_interval

# ---------------------------------------------------------
# Cronjob: 4 hour
# ---------------------------------------------------------


async def cron_h4():
    logger.info("executing cronjob: H4")
    now_utc = datetime.now(timezone.utc)
    db.settings.set("cronjob_h4_updated_at", now_utc.strftime("%Y-%m-%d %H:%M:%S"))

    msg = "----H4---"
    for ticker in config.cronjob.refresh_tickers:
        result = refresh_ticker_by_interval(ticker=ticker, interval="h4")
        last_candle = result.iloc[-1]
        msg += f"\n{ticker.replace('-USD', '')}: ${float(last_candle['close']):.2f}"

    asyncio.create_task(Notifier.send_telegram_message_async(msg))


# ---------------------------------------------------------
# Cronjob: 1 day
# ---------------------------------------------------------


async def cron_d1():
    logger.info("executing cronjob: D1")
    now_utc = datetime.now(timezone.utc)
    db.settings.set("cronjob_d1_updated_at", now_utc.strftime("%Y-%m-%d %H:%M:%S"))

    msg = "----DAILY---"
    for ticker in config.cronjob.refresh_tickers:
        result = refresh_ticker_by_interval(ticker=ticker, interval="d1")
        last_candle = result.iloc[-1]
        msg += f"\n{ticker.replace('-USD', '')}: ${float(last_candle[-1]['close']):.2f}"

    asyncio.create_task(Notifier.send_telegram_message_async(msg))


# ---------------------------------------------------------
# Cronjob: initialize
# ---------------------------------------------------------

scheduler = AsyncIOScheduler(timezone=UTC)

utc_plus_1 = timezone(timedelta(hours=1))
utc_minus_3 = timezone(timedelta(hours=-3))


def cron_initialize():
    if settings.enabled_cron:
        logger.info(f"cronjob is enabled at {datetime.now(UTC)}")

        scheduler.add_job(cron_h4, CronTrigger(day="*", hour="*/4", minute="0", second="20", timezone=utc_plus_1))
        scheduler.add_job(cron_d1, CronTrigger(day="*", hour="0", minute="1", timezone="UTC"))

        scheduler.start()
    else:
        logger.info("cronjob is disabled")


def cron_shutdown():
    if settings.enabled_cron:
        scheduler.shutdown()
