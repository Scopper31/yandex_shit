import config
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

import .main5
from utils import TestStates
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import sqlite3
from sqlite3 import Error
import sql


#https://surik00.gitbooks.io/aiogram-lessons/content/chapter4.html
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '6064341811:AAFJlrN3bV8fHUuL0eO_VbZcKerBH2cH9Io'
PAYMENTS_TOKEN = '381764678:TEST:51884'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000 * 100)  # в копейках (руб)

button1 = InlineKeyboardButton('Купить подписку', callback_data='buy_b')
button2 = InlineKeyboardButton('Решить задачи', callback_data='solve_b')
button3 = InlineKeyboardButton('Информация', callback_data='info_b')

markup2 = InlineKeyboardMarkup().add(button1).add(button2).add(button3)


stop_b = InlineKeyboardButton('Прервать', callback_data='stop')
stop_markup = InlineKeyboardMarkup().add(stop_b)

login = ''
passwd = ''
link = ''


@dp.callback_query_handler(lambda c: c.data == 'buy_b')
async def process_callback_buy2(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
        await bot.send_message(callback_query.from_user.id, "Тестовый платеж!!!")
        await bot.send_message(callback_query.from_user.id, 'В поле "Доставка" введите логин вашего Яндекс аккаунта с лицеем')

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


@dp.callback_query_handler(lambda c: c.data == 'stop', state=TestStates.all())
async def process_callback_solve(callback_query: types.CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.reset_state()
    await bot.send_message(callback_query.from_user.id, 'Ввод данных прерван')


@dp.callback_query_handler(lambda c: c.data == 'solve_b')
async def process_callback_solve(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    state = dp.current_state(user=callback_query.from_user.id)
    await state.set_state(TestStates.all()[1])
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Мне нужны твои данные. От банковской карты уже есть. Нужны еще логин и пароль от яндекс аккаунта с лицеем', reply_markup=stop_markup)
    await bot.send_message(callback_query.from_user.id, 'Логин:')


@dp.callback_query_handler(lambda c: c.data == 'info_b')
async def process_callback_info(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Информаиция:')
    await bot.send_message(callback_query.from_user.id, 'В другой жизни!')


@dp.message_handler(commands=['start', 'menu'])
async def send_welcome(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    await state.reset_state()
    await bot.send_message(message.chat.id, "Привет!\nЯ бот-помощник от sanyasupertank и popkapirat!\nЕсли у тебя нет времени решать задачи, я сделаю все за тебя автоматически.", reply_markup=markup2)


@dp.message_handler(commands=['info'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, 'мне пока лень(((')


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    print('order_info')
    print(pre_checkout_q.order_info)
    if not hasattr(pre_checkout_q.order_info, 'email'):
        return await bot.answer_pre_checkout_query(
            pre_checkout_q.id,
            ok=False,
            error_message='не введен логин Яндекс лицея')
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    sqlite_connection = sql.sql_connection()
    sql.add_subscriber(sqlite_connection, payment_info['order_info']['email'])
    sqlite_connection.close()
    for k, v in payment_info.items():
        print(f"{k} = {v}")

    print(payment_info)
    print(message.successful_payment)
    await bot.send_message(message.chat.id,
                           f"Платёж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")


@dp.message_handler()
async def zero_state_msg(msg: types.Message):
    if 'пидор' in msg.text.lower():
        await bot.send_message(msg.from_user.id, 'Бога побойся, уёбок')

    elif 'ильяпетух' in msg.text.lower():
        sqlite_connection = sql.sql_connection()
        sql.add_subscriber(sqlite_connection, msg.text.split()[1])
        sqlite_connection.close()
        await bot.send_message(msg.from_user.id, 'Ок бро, я тебя понял')
    else:
        await bot.send_message(msg.from_user.id, 'Что ты несешь?')


@dp.message_handler(state=TestStates.TEST_STATE_1[0])
async def first_test_state_case_met(message: types.Message):
    global login
    login = message.text
    sqlite_connection = sql.sql_connection()
    if not sql.check_existence(sqlite_connection, login):
        state = dp.current_state(user=message.from_user.id)
        await state.reset_state()
        await message.reply('У вас нет подписки((( сори', reply=False)
    else:
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(TestStates.all()[2])
        await message.reply('Пароль:', reply=False)


@dp.message_handler(state=TestStates.TEST_STATE_2[0])
async def first_test_state_case_met(message: types.Message):
    global passwd
    passwd = message.text
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(TestStates.all()[3])
    await message.reply('Ссылка:', reply=False)


@dp.message_handler(state=TestStates.TEST_STATE_3[0])
async def first_test_state_case_met(message: types.Message):
    global link
    link = message.text
    state = dp.current_state(user=message.from_user.id)
    print(type(main5.check_url(link)))
    print(main5.check_url(link))
    if type(main5.check_url(link)) == list:
        await message.reply('Погнали!', reply=False)
        await state.reset_state()
        main5.solve(login, passwd, link)
        await message.reply('Задача выполнена', reply=False)
    else:
        await message.reply('Ссылка говно!', reply=False)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


#1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling
if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)
