import logging
from pathlib import Path

from aiogram.types import BufferedInputFile

from tg_bot.src.data.admitted_people import notified_people
from tg_bot.src.loader import bot


error_log: Path = Path('files', 'logs', 'error')
info_log: Path = Path('files', 'logs', 'info')

info_logger = logging.getLogger(str(info_log))
info_logger.setLevel(logging.INFO)
error_logger = logging.getLogger(str(error_log))
error_logger.setLevel(logging.ERROR)

# configuring the handler and formatter for loggers
handler_user_logger = logging.FileHandler(f"{str(info_log)}.log")
handler_error_logger = logging.FileHandler(f"{str(error_log)}.log")
formatter_logger = logging.Formatter("%(asctime)s %(message)s")

# adding a formatter to a handler
handler_user_logger.setFormatter(formatter_logger)
handler_error_logger.setFormatter(formatter_logger)

# adding handlers to loggers
info_logger.addHandler(handler_user_logger)
error_logger.addHandler(handler_error_logger)


async def report(description: str,
                 extent: str = 'info',
                 exception: Exception | None = None,
                 image: BufferedInputFile | None = None,
                 add_informed: list[int] | int | None = None) -> None:
    informed: list[int] = notified_people.copy()
    if add_informed is not None:
        if type(add_informed) is str:
            informed.append(add_informed)
        elif type(add_informed) is list:
            informed += add_informed.copy()
    for admin_id in informed:
        if image is None:
            await bot.send_message(chat_id=admin_id, text=description)
        else:
            await bot.send_photo(chat_id=admin_id, photo=image, caption=description)
    informed.clear()
    if extent == 'info':
        try:
            info_logger.info(description)
        except Exception as e:
            print(f'logging in the report has failed with:\n{e}')
        return
    error_logger.exception(description if exception is None else description + '\n' + str(exception))
