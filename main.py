import logging

from aiogram.utils import executor
from aiogram import Bot, Dispatcher

from misc.env import TOKENS
from misc.webhook import webhook_path, webapp_host, webapp_port, webhook_url

from handlers.main import register_all_handlers

import requests

bot = Bot(token=TOKENS.BOT_TOKEN, parse_mode='HTML')


async def on_start_up(dp: Dispatcher) -> None:
    logging.warning('Starting...')
    register_all_handlers(dp)
    await bot.set_webhook(webhook_url)


async def on_shutdown() -> None:
    logging.warning('Shutting down...')
    await bot.delete_webhook()
    logging.warning('Bye!')


def start_bot():
    headers = {"api-key": webhook_path}
    r = requests.get('https://webhook.site/token' + webhook_path + '/requests?sorting=newest', headers=headers)
    for request in r.json()['data']:
        print(request)
    dp = Dispatcher(bot)
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=webhook_path,
        on_startup=on_start_up,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=webapp_host,
        port=webapp_port,
    )


if __name__ == '__main__':
    start_bot()
