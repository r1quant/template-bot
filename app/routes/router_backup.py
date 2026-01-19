import os
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.settings import settings

router = APIRouter()


# ---------------------------------------------------------
# Router: Backup
# ---------------------------------------------------------


@router.get("/backup/database")
def backup_db_download():
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_filename = f"backup_{timestamp}_{str(settings.environment.value)}.db"
    backup_filepath = os.path.join(settings.database_path).replace("sqlite:///", "")
    return FileResponse(path=backup_filepath, filename=backup_filename, media_type="application/octet-stream")
