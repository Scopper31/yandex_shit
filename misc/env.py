from os import environ
from typing import Final


class TOKENS:
    BOT_TOKEN: Final = environ.get('bot_token', 6064341811:AAFJlrN3bV8fHUuL0eO_VbZcKerBH2cH9Io)
    PAYMENT_TOKEN: Final = environ.get('payment_token', 381764678:TEST:51884)