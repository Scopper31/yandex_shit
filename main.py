from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from handlers.main import register_all_handlers


async def on_start_up(dp: Dispatcher) -> None:
    register_all_handlers(dp)


def start_bot():
    pass
