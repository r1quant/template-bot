from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database.database import create_db_and_tables
from app.core.settings import settings
from app.cronjob import cron_initialize, cron_shutdown
from app.routes.router_cronjob import router as CronjobRouter
from app.routes.router_logs import router as LogRouter
from app.routes.router_notifications import router as NoficationsRouter
from app.routes.router_ohlc import router as OHLCRouter
from app.routes.router_settings import router as SettingsRouter

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

app.include_router(CronjobRouter)
app.include_router(LogRouter)
app.include_router(NoficationsRouter)
app.include_router(OHLCRouter)
app.include_router(SettingsRouter)


@app.get("/")
def read_root():
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "enabled_cron": settings.enabled_cron,
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
