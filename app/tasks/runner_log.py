import asyncio

from app.core.logging import get_errors_in_log_file
from app.lib.utils.notifier import Notifier


def notify_error_in_log_file():
    has_error, error_lines = get_errors_in_log_file()

    if has_error:
        msg = "THERE'S ERROR IN THE LOG\n"
        msg += "-------------------------------"
        for error_line in error_lines:
            msg += f"\n-*[{error_line['line']}]*: {error_line['content']}"
        asyncio.create_task(Notifier.send_telegram_message_async(msg))

    return error_lines
