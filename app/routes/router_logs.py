import os
from collections import deque
from datetime import date, timedelta

import aiofiles
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.logging import get_errors_in_log_file
from app.core.settings import settings

router = APIRouter()


# ---------------------------------------------------------
# Router: Logs
# ---------------------------------------------------------


@router.get("/logs", response_class=PlainTextResponse)
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


@router.get("/logs/has_error")
async def logs_report_error():
    has_error, error_lines = get_errors_in_log_file()
    return {"has_error": has_error, "error_lines": error_lines}
