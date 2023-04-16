from aiogram import Dispatcher, Bot
from misc.env import *
from aiogram.types import Message


bot = Bot(token=TOKENS.BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot=bot)


async def echo(msg: Message):
    await msg.answer(msg.text)


def register_other_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(echo, content_types=['text'])
