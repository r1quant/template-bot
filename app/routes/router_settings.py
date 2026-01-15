from fastapi import APIRouter

from app.core.database.methods import db

router = APIRouter()

# ---------------------------------------------------------
# Router: Settings
# ---------------------------------------------------------


@router.get("/settings")
def all_settings():
    values = db.settings.all()
    return {"settings": values}


@router.get("/settings/:key")
def get_settings(key: str):
    value = db.settings.get(key)
    return {"key": key, "value": value}


@router.delete("/settings/:key")
def delete_settings(key: str):
    value = db.settings.delete(key)
    return {"key": key, "value": value}


@router.post("/settings")
def save_settings(key: str, value: str):
    db.settings.set(key, value)
    return {"key": key, "value": value}
