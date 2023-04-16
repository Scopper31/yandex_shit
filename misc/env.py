import os
from typing import Final


class TOKENS:
    BOT_TOKEN: Final = os.environ.get('bot_token', '6064341811:AAFJlrN3bV8fHUuL0eO_VbZcKerBH2cH9Io')
    PAYMENT_TOKEN: Final = os.environ.get('payment_token', 'not_defined!')
