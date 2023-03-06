import config
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

#https://surik00.gitbooks.io/aiogram-lessons/content/chapter4.html
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '6064341811:AAFJlrN3bV8fHUuL0eO_VbZcKerBH2cH9Io'
PAYMENTS_TOKEN = '381764678:TEST:51884'

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(bot)

PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000 * 100)  # в копейках (руб)

button1 = InlineKeyboardButton('Купить подписку', callback_data='buy_b')
button2 = InlineKeyboardButton('Решить задачи', callback_data='solve_b')
button3 = InlineKeyboardButton('Информация', callback_data='info_b')

markup2 = InlineKeyboardMarkup().add(button1).add(button2).add(button3)

@dp.callback_query_handler(lambda c: c.data == 'buy_b')
async def process_callback_buy2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
        await bot.send_message(callback_query.from_user.id, "Тестовый платеж!!!")

    await bot.send_invoice(callback_query.from_user.id,
                           title="Подписка на бота",
                           description="Активация подписки на бота на 1 месяц",
                           provider_token=PAYMENTS_TOKEN,
                           currency="rub",
                           photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium-subscription.jpg",
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           need_email=True,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")


@dp.callback_query_handler(lambda c: c.data == 'solve_b')
async def process_callback_solve(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Мне нужны твои данные. От банковской карты уже есть. Нужны еще логин и пароль от яндекс аккаунnта с лицеем')


@dp.callback_query_handler(lambda c: c.data == 'info_b')
async def process_callback_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'В другой жизни!')


@dp.message_handler(commands=['start', 'menu'])
async def send_welcome(message: types.Message):
   await bot.send_message(message.chat.id, "Привет!\nЯ бот-помощник от sanyasupertank!\nЕсли у тебя нет времени решать задачи, я сделаю все за тебя автоматически.", reply_markup=markup2)

@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):

    if hasattr(pre_checkout_query.order_info, 'email'):
        return await bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message='не введен логин Яндекс лицея')
    else:
        pass
        #add_to_base(pre_checkout_query.order_info['email'])
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    await bot.send_message(message.chat.id,
                           f"Платёж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")



#commands = {'/start': 'Запустить бота', '/solve': 'Решить задачи', '/buy': 'Решить задачи', '/info': 'Решить задачи', '/menu': 'Решить задачи'}



#1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
