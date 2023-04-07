from os import environ
from typing import Final


class TOKENS:
    BOT_TOKEN: Final = environ.get('bot_token', 'not_defined!')
    PAYMENT_TOKEN: Final = environ.get('payment_token', 'not_defined!')
