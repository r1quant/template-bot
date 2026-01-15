from fastapi import APIRouter

from app.cronjob import cron_d1, cron_h1

router = APIRouter()

# ---------------------------------------------------------
# Routes: Cronjob
# ---------------------------------------------------------


@router.get("/cronjob/{interval}")
async def cronjob_run(interval: str):
    if interval == "h1":
        await cron_h1()

    if interval == "d1":
        await cron_d1()

    return {"running_interval": interval}
