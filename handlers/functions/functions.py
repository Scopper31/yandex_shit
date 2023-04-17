from aiogram import Dispatcher, Bot
from misc.env import *
from aiogram.types import Message
import requests as r
from misc.webhook import webhook_path


bot = Bot(token=TOKENS.BOT_TOKEN, parse_mode='HTML')


async def echo(msg: r.get(f'https://webhook.site/token{webhook_path}/requests?sorting=newest')):
    for request in msg.json()['data']:
        print(request)
    await msg.answer(msg.text)


def register_other_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(echo, content_types=['text'])
