from aiogram import Dispatcher

from handlers.message_handlers import register_message_handlers
from handlers.query_handlers import register_query_handlers


def register_all_handlers(dp: Dispatcher) -> None:
    handlers = (
        register_message_handlers,
        register_query_handlers,
    )
    for handler in handlers:
        handler(dp)
