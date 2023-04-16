
import asyncio
import datetime
import logging
import re


from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from bs4 import BeautifulSoup
from content import key


from misc.env import TOKENS
'''
openai.api_key = key
one_task = -1

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKENS.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())



users_data = {}




async def shutdown(dispatcher: Dispatcher):
    


# 1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling


# poshel nahuy







if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)'''