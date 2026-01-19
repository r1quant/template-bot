from datetime import datetime
from enum import Enum

from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------
# Jinja2 Config
# ---------------------------------------------------------

pages = Jinja2Templates(directory="app/routes/pages")


def format_datetime(value: str, format: str = "%B %d, %Y' %H:%M"):
    if not value:
        return ""
    try:
        # dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return dt.strftime(format)
    except ValueError:
        return value  # Return original string if parsing fails


def enum_to_str(obj):
    return obj.value if isinstance(obj, Enum) else str(obj)


pages.env.filters["datetime_format"] = format_datetime
pages.env.filters["enum_to_str"] = enum_to_str
