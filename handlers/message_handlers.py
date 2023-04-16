import threading

from aiogram import Dispatcher, Bot
from aiogram.types.message import ContentType

from problem_solving.solving import *
from keyboards.inline_keyboards import *
from database import sql
from misc.utils.utils import *
from cringe import types, asyncio
from misc.env import *

users_data = {}

bot = Bot(token=TOKENS.BOT_TOKEN, parse_mode='HTML')


def register_message_handlers(dp: Dispatcher):
    @dp.message_handler(state=TestStates.TEST_STATE_5[0])
    async def first_test_state_case_met(message: types.Message):
        pin = message.text
        users_data[message.from_user.id].pin = pin
        users_data[message.from_user.id].wanna_commit_suicide = True

    @dp.message_handler(commands=['start', 'menu'])
    async def send_welcome(message: types.Message):
        state = dp.current_state(user=message.from_user.id)
        await state.reset_state()
        await bot.send_message(message.chat.id,
                               "Привет!\nЯ бот-помощник от sanyasupertank и popkapirat!\nЕсли у тебя нет времени "
                               "решать задачи, я сделаю все за тебя автоматически.",
                               reply_markup=markup2)

    @dp.message_handler(commands=['info'])
    async def send_welcome(message: types.Message):
        await bot.send_message(message.chat.id, 'мне пока лень(((')

    @dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
    async def successful_payment(message: types.Message):
        payment_info = message.successful_payment.to_python()
        sqlite_connection = sql.sql_connection()
        sql.add_subscriber(sqlite_connection, payment_info['order_info']['email'].split('@')[0])
        sqlite_connection.close()
        await bot.send_message(message.chat.id,
                               f"Платёж на сумму {message.successful_payment.total_amount // 100} "
                               f"{message.successful_payment.currency} прошел успешно!")

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
    async def third_test_state_case_met(message: types.Message):
        check = await check_url(message.text)
        if type(check) == list:
            if check == ['lesson']:
                links_array = await lesson_parser(message.chat.id, message.text)
            else:
                links_array = [message.text]
            await message.reply('Погнали!', reply=False)
            print(message.text)
            print(links_array)

            if len(users_data[message.from_user.id].links) == 0:
                users_data[message.from_user.id].links.extend(links_array)

                thread = threading.Thread(target=asyncio.run, args=(make_task(message.from_user.id),))
                thread.start()

            else:
                users_data[message.from_user.id].links.append(message.text)
        else:
            await message.delete()
            await message.reply('Ссылка говно!', reply=False)
        users_data[message.from_user.id].fck = 1000
