import logging
import pathlib
from logging.handlers import TimedRotatingFileHandler

from app.core.settings import settings

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging_filepath = f"data/{settings.log_file.replace('.log', '')}.log"

# Configure a logger that rotates daily at midnight, keeping 7 days of backups
file_handler = TimedRotatingFileHandler(logging_filepath, when="midnight", interval=1, backupCount=7, encoding="utf-8")


logging.basicConfig(
    level=settings.log_level,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[file_handler],
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def get_errors_in_log_file():
    logfile = pathlib.Path(logging_filepath)

    if not logfile.exists():
        return []

    error_lines = []
    with open(logfile, "r") as file:
        for line_num, line in enumerate(file, 1):
            if "erro" in line.lower():
                error_lines.append({"line": line_num, "content": line.strip()})

    has_error = len(error_lines) > 0

    return has_error, error_lines

