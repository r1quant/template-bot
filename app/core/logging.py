import logging
from logging.handlers import TimedRotatingFileHandler

from app.core.settings import settings

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging_filepath = f"data/{settings.log_file.replace('.log', '')}.log"

# Configure a logger that rotates daily at midnight, keeping 7 days of backups
handler = TimedRotatingFileHandler(logging_filepath, when="midnight", interval=1, backupCount=7, encoding="utf-8")


logging.basicConfig(
    level=settings.log_level,  # Set the minimum logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[handler],
)

logger = logging.getLogger(__name__)
