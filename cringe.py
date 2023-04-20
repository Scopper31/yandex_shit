#! /usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import re
import threading
import time
from io import BytesIO

import openai
import sql
import tiktoken
from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ContentType

from bs4 import BeautifulSoup
from content import key
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from utils import TestStates


openai.api_key = key

template = 'Python, dont write any comments, dont write anything except code, provide answer in code block, obey pep8\nThe problem: '
sample_template = ["\nFor this example:\n", "\nIt outputs this:\n", "\nFor example if program gets this input:\n"]
funcclass_template = ["\nAn example of program that might use your code:\n",
                      "\nOutput it needs to produce:\n"]
one_task = -1

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

markup2 = InlineKeyboardMarkup().add(button2).add(button3)#.add(button1)

stop_b = InlineKeyboardButton('Прервать', callback_data='stop')
stop_markup = InlineKeyboardMarkup().add(stop_b)

yes_b = InlineKeyboardButton('Да', callback_data='yes_call')
no_b = InlineKeyboardButton('Нет', callback_data='no_call')
num_markup = InlineKeyboardMarkup().add(yes_b).add(no_b)


class User:
    def __init__(self, login='', wanna_commit_suicide='', driver='', qr_code='', fck=2000, crunch = 0,
                 send_time=datetime.datetime(2035, 1, 1, 1, 1)):

        self.crunch = crunch
        self.info_messege_ids = []
        self.tasks_messege_ids = []
        self.other_shit = []
        self.login = login
        self.links = []
        self.driver = driver
        self.qr_code = qr_code
        self.send_time = send_time
        self.wanna_commit_suicide = wanna_commit_suicide
        self.fck = fck


users_data = {}


@dp.callback_query_handler(lambda c: c.data == 'buy_b')
async def process_callback_buy2(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await bot.answer_callback_query(callback_query.id)
    if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
        await bot.send_message(callback_query.from_user.id, "Тестовый платеж!!!")
        await bot.send_message(callback_query.from_user.id,
                               'В поле "Доставка" введите логин вашего Яндекс аккаунта с лицеем')

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


@dp.message_handler(state=TestStates.TEST_STATE_5[0])
async def first_test_state_case_met(message: types.Message):
    pin = message.text
    users_data[message.from_user.id].pin = pin
    users_data[message.from_user.id].wanna_commit_suicide = True


@dp.callback_query_handler(lambda c: c.data == 'stop', state=TestStates.all())
async def process_callback_stop(callback_query: types.CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.reset_state()
    users_data[callback_query.from_user.id].links = []
    users_data[callback_query.from_user.id].fck = -1
    await delete_shit(callback_query.from_user.id)


@dp.callback_query_handler(lambda c: c.data == 'solve_b')
async def process_callback_solve(callback_query: types.CallbackQuery):
    await delete_shit(callback_query.from_user.id)
    users_data[callback_query.from_user.id].crunch = 0
    state = dp.current_state(user=callback_query.from_user.id)

    msg1 = await bot.send_message(callback_query.from_user.id, 'Подтверждай вход через QR код')
    users_data[callback_query.from_user.id].tasks_messege_ids.append(msg1.message_id)
    sticker_loading_id = '''CAACAgIAAxkBAAI_ZmQ7zdmfPRMN_wZ4Eu11i3Amn6PQAAINLwACAprZSe9yyQABpOYHZy8E'''
    stiker_loading_sending = await bot.send_sticker(chat_id=callback_query.from_user.id, sticker=sticker_loading_id)
    stiker_loading_sending_id = stiker_loading_sending.message_id
    await login_qr(callback_query.from_user.id)
    await bot.delete_message(callback_query.from_user.id, stiker_loading_sending_id)
    if users_data[callback_query.from_user.id].crunch == 0:
        sending = await bot.send_photo(callback_query.from_user.id, photo=users_data[callback_query.from_user.id].qr_code)
        sending_id = sending.message_id
        users_data[callback_query.from_user.id].tasks_messege_ids.append(sending_id)
    else:
        users_data[callback_query.from_user.id].crunch = 0
        users_data[callback_query.from_user.id].fck = -1
        return
    driver = users_data[callback_query.from_user.id].driver
    qr_url = driver.current_url
    while driver.current_url == qr_url:
        if 'Внутренняя ошибка: обновите страницу и попробуйте еще раз' in driver.page_source:
            await state.reset_state()
            msg9 = await bot.send_message(callback_query.from_user.id, 'Давай по новой')
            users_data[callback_query.from_user.id].tasks_messege_ids.append(msg9.message_id)
            return
        await asyncio.sleep(1)
    await users_login(callback_query.from_user.id)
    sqlite_connection = sql.sql_connection()
    if not sql.check_existence(sqlite_connection, users_data[callback_query.from_user.id].login.lower()):
        await bot.delete_message(callback_query.from_user.id, sending_id)

        msg2 = await bot.send_message(callback_query.from_user.id, '❌')
        users_data[callback_query.from_user.id].tasks_messege_ids.append(msg2.message_id)

        state = dp.current_state(user=callback_query.from_user.id)
        await state.reset_state()
        msg10 = await bot.send_message(callback_query.from_user.id, 'У вас нет подписки((( сори')
        users_data[callback_query.from_user.id].tasks_messege_ids.append(msg10.message_id)
    else:
        await bot.delete_message(callback_query.from_user.id, sending_id)
        msg2 = await bot.send_message(callback_query.from_user.id, '🆗')
        users_data[callback_query.from_user.id].tasks_messege_ids.append(msg2.message_id)

        await state.set_state(TestStates.all()[1])
        msg3 = await bot.send_message(callback_query.from_user.id,
                               'Присылай ссылки на уроки и задания (одно сообщение - одна ссылка):',
                               reply_markup=stop_markup)
        users_data[callback_query.from_user.id].tasks_messege_ids.append(msg3.message_id)

        thread_time = threading.Thread(target=asyncio.run, args=(time_end(callback_query.from_user.id),))
        thread_time.start()
        while users_data[callback_query.from_user.id].fck != 0:
            if users_data[callback_query.from_user.id].fck == -1:
                break
            await asyncio.sleep(1)
        if users_data[callback_query.from_user.id].fck == 0:
            await state.reset_state()
            await delete_shit(callback_query.from_user.id)


async def delete_shit(_id):
    state = dp.current_state(user=_id)
    await state.reset_state()
    users_data[_id].crunch = 1
    try:
        for shit_messege in users_data[_id].info_messege_ids:
            try:
                await bot.delete_message(_id, shit_messege)
            except:
                pass
        users_data[_id].info_messege_ids = []
    except:
        pass

    try:
        for shit_messege in users_data[_id].tasks_messege_ids:
            try:
                await bot.delete_message(_id, shit_messege)
            except:
                pass
        users_data[_id].tasks_messege_ids = []
    except:
        pass


async def delete_all(_id):
    state = dp.current_state(user=_id)
    await state.reset_state()
    users_data[_id].crunch = 1
    try:
        for shit_messege in users_data[_id].info_messege_ids:
            try:
                await bot.delete_message(_id, shit_messege)
            except:
                pass
        users_data[_id].info_messege_ids = []
    except:
        pass

    try:
        for shit_messege in users_data[_id].tasks_messege_ids:
            try:
                await bot.delete_message(_id, shit_messege)
            except:
                pass
        users_data[_id].tasks_messege_ids = []
    except:
        pass

    try:
        for shit_messege in users_data[_id].other_shit:
            try:
                await bot.delete_message(_id, shit_messege)
            except:
                pass
        users_data[_id].tasks_messege_ids = []
    except:
        pass


@dp.callback_query_handler(lambda c: c.data == 'info_b')
async def process_callback_info(callback_query: types.CallbackQuery):
    await delete_shit(callback_query.from_user.id)
    await bot.answer_callback_query(callback_query.id)
    info_sending = await bot.send_message(callback_query.from_user.id, '''Наш бот предназначен для решения задач с курсов Яндекс Лицей по языку програмирования Python. Для начала работы с ботом, нажмите кнопку "Решить задачи" и отсканируйте QR-код на экране. Затем вы сможете отправлять ссылки на задачи, которые будут автоматически решаться нашим ботом.\n\n\nИнструкция по пользованию:\nНажмите кнопку "Решить задачи".\n\nОтсканируйте QR-код на экране.\n\nОтправляйте ссылки на задачи или уроки, которые вы хотите решить.\n(Не рекомендуем отправлять задачи с ручной проверкой)\n\nБот будет автоматически решать отправленные задачи.\n\nПродолжайте отправлять ссылки на задачи.\n\n\nFAQ:\n\n1. Q: Если я скину много задач, не забанит ли меня Яндекс за слишком частое решение?\n    A: Нет, после каждой задачи бот ждет ~5 минут перед посылкой следующей.\n\n2. Q: Не будет ли проблем с плагиатом? откуда берутся решения?\n    A: Каждая посылка это новое сгенерированое решение, они могут быть похожи друг на друга, если это простая задача, но все решения генерируются заново.\n\n3. Q: Как быстро он работает?\n    A: Сами решения получаются всего за несколько секунд. Между задачами совершается перерыв в несколько минут, чтобы избежать подозрений со стороны проверяющей системы.\n\n4. Q: Как хорошо он решает задачи?\n    A: Решаются в среднем 85-95% задач, основные проблемы вызывают задачи требующие творческого подхода или задачи с непонятным условием. Всегда можно указать боту на одну и ту же задачу несколько раз, и зачастую он находится в одном шаге от правильного решения, и можно его немного подтолкнуть.\n\n\nЕсли у вас есть какие-либо проблемы с использованием бота, пожалуйста, обратитесь в нашу службу поддержки, написав на почту Bot2bit@yandex.ru''')
    users_data[callback_query.from_user.id].info_messege_ids.append(info_sending.message_id)


@dp.message_handler(commands=['start', 'menu'])
async def send_welcome(message: types.Message):
    users_data[message.from_user.id] = User()
    await delete_all(message.from_user.id)
    photo = open('hi.jpg', 'rb')
    main_msg = await bot.send_photo(message.chat.id, photo=photo, caption="Я бот-помощник от sanyasupertank и popkapirat!\nЕсли у тебя нет времени решать задачи, я сделаю все за тебя автоматически.", reply_markup=markup2)
    photo.close()
    users_data[message.from_user.id].other_shit.append(main_msg.message_id)



@dp.message_handler(commands=['info'])
async def send_info(message: types.Message):
    await delete_shit(message.from_user.id)
    msg7 = await bot.send_message(message.chat.id, '''Наш бот предназначен для решения задач с курсов Яндекс Лицей по языку програмирования Python. Для начала работы с ботом, нажмите кнопку "Решить задачи" и отсканируйте QR-код на экране. Затем вы сможете отправлять ссылки на задачи, которые будут автоматически решаться нашим ботом.\n\n\nИнструкция по пользованию:\nНажмите кнопку "Решить задачи".\n\nОтсканируйте QR-код на экране.\n\nОтправляйте ссылки на задачи или уроки, которые вы хотите решить.\n(Не рекомендуем отправлять задачи с ручной проверкой)\n\nБот будет автоматически решать отправленные задачи.\n\nПродолжайте отправлять ссылки на задачи.\n\n\nFAQ:\n\n1. Q: Если я скину много задач, не забанит ли меня Яндекс за слишком частое решение?\n    A: Нет, после каждой задачи бот ждет ~5 минут перед посылкой следующей.\n\n2. Q: Не будет ли проблем с плагиатом? откуда берутся решения?\n    A: Каждая посылка это новое сгенерированое решение, они могут быть похожи друг на друга, если это простая задача, но все решения генерируются заново.\n\n3. Q: Как быстро он работает?\n    A: Сами решения получаются всего за несколько секунд. Между задачами совершается перерыв в несколько минут, чтобы избежать подозрений со стороны проверяющей системы.\n\n4. Q: Как хорошо он решает задачи?\n    A: Решаются в среднем 85-95% задач, основные проблемы вызывают задачи требующие творческого подхода или задачи с непонятным условием. Всегда можно указать боту на одну и ту же задачу несколько раз, и зачастую он находится в одном шаге от правильного решения, и можно его немного подтолкнуть.\n\n\nЕсли у вас есть какие-либо проблемы с использованием бота, пожалуйста, обратитесь в нашу службу поддержки, написав на почту Bot2bit@yandex.ru''')
    users_data[message.from_user.id].info_messege_ids.append(msg7.message_id)
    msg8 = message.message_id
    users_data[message.from_user.id].info_messege_ids.append(msg8.message_id)


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    # print('order_info')
    # print(pre_checkout_q.order_info)
    if not hasattr(pre_checkout_q.order_info, 'email'):
        return await bot.answer_pre_checkout_query(
            pre_checkout_q.id,
            ok=False,
            error_message='не введен логин Яндекс лицея')
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    # print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    sqlite_connection = sql.sql_connection()
    sql.add_subscriber(sqlite_connection, payment_info['order_info']['email'].split('@')[0])
    sqlite_connection.close()
    for k, v in payment_info.items():
        pass
        # print(f"{k} = {v}")

    # print(payment_info)
    # print(message.successful_payment)
    await bot.send_message(message.chat.id,
                           f"Платёж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")


@dp.message_handler()
async def zero_state_msg(msg: types.Message):
    if 'пидор' in msg.text.lower():
        await bot.send_message(msg.from_user.id, 'Бога побойся, уёбок')

    elif 'бабиджон' in msg.text.lower():
        sqlite_connection = sql.sql_connection()
        if '@' in msg.text.lower():
            users_mail = msg.text.lower().split()[1].split('@')[0]
        else:
            users_mail = msg.text.lower().split()[1]

        sql.add_subscriber(sqlite_connection, users_mail)
        sqlite_connection.close()
        img = open('for_iliya.jpg', 'rb')
        await bot.send_photo(msg.from_user.id, photo=img, caption='Ок бро, я тебя понял')
        img.close()
    else:
        await bot.send_message(msg.from_user.id, 'Что ты несешь?')


async def driver_end(__id):
    users_data[__id].driver.quit()
    users_data[__id].driver = None
    users_data.pop(__id)


async def time_end(_id):
    while users_data[_id].fck != 0:
        if users_data[_id].fck == -1:
            return
        users_data[_id].fck -= 1
        await asyncio.sleep(1)
    await driver_end(_id)
    kill_me = dp.current_state(user=_id)
    await kill_me.reset_state()


@dp.message_handler(state=TestStates.TEST_STATE_1[0])
async def third_test_state_case_met(message: types.Message):
    users_data[message.from_user.id].tasks_messege_ids.append(message.message_id)
    check = await check_url(message.text)
    if type(check) == list:
        if check == ['lesson']:
            links_array = await lesson_parser(message.chat.id, message.text)
        else:
            links_array = [message.text]
        msg5 = await message.reply('Погнали!', reply=False)
        users_data[message.from_user.id].tasks_messege_ids.append(msg5.message_id)
        print(message.text)
        print(links_array)

        if len(users_data[message.from_user.id].links) == 0:
            users_data[message.from_user.id].links.extend(links_array)

            thread = threading.Thread(target=asyncio.run, args=(make_task(message.from_user.id),))
            thread.start()

        else:
            users_data[message.from_user.id].links.append(message.text)

        # await message.reply(f'Задача выполнена', reply=False)
    else:
        await message.delete()
        msg6 = await message.reply('Ссылка говно!', reply=False)
        users_data[message.from_user.id].tasks_messege_ids.append(msg6.message_id)
    users_data[message.from_user.id].fck = 2000


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


# 1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling

# Проверка что чел у нас в базе
async def users_login(_id):
    driver = users_data[_id].driver
    yandex_user_data = driver.page_source
    k = yandex_user_data.find(""""username":""") + len(""""username":""") + 1
    yandex_user_data = yandex_user_data[k:k + 100:]
    username = yandex_user_data.split('"')[0]
    users_data[_id].login = username.lower()


# poshel nahuy

# Создание сесии, добавляет qr и driver(сессию) в users_data
async def login_qr(_id):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument('--crash-dumps-dir=/tmp')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver_login = webdriver.Chrome(service=Service("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver"), options=chrome_options)
    driver_login.get("https://passport.yandex.ru/auth?origin=lyceum&retpath=https%3A%2F%2Flyceum.yandex.ru%2F")
    ActionChains(driver_login).click(
        driver_login.find_element(By.CLASS_NAME, "AuthSocialBlock-provider.AuthSocialBlock-provider_code_qr")).perform()
    await asyncio.sleep(1)
    qr = driver_login.find_element(By.CLASS_NAME, "MagicField-qr").screenshot_as_png
    users_data[_id].driver = driver_login
    qr = BytesIO(qr)
    users_data[_id].qr_code = qr


# Проверка что ссылка на яндекс, возвращает урок или задание (задание - ["task"], урок - ["lesson"]
async def check_url(url):
    url = url.replace('https://', '')
    url = url.split('/')
    domain = url[0]
    if domain == "lyceum.yandex.ru":
        if len(url) > 1:
            if 'courses' == url[1]:
                if len(url) > 3:
                    if 'groups' == url[3]:
                        if len(url) > 5:
                            if 'lessons' == url[5]:
                                if len(url) > 7:
                                    if 'tasks' == url[7]:
                                        return ['task']
                                else:
                                    return ['lesson']
    return "Проверьте ссылку"


# Вычленяет код между двумя задаными символами
async def extract_between(input_string, start_symbol, end_symbol):
    substrings = set()
    start_index = 0
    while True:
        start_index = input_string.find(start_symbol, start_index)
        if start_index == -1:
            break
        end_index = input_string.find(end_symbol, start_index + 1)
        if end_index == -1:
            break
        substrings.add(start_symbol + input_string[start_index + 1: end_index] + end_symbol)
        start_index = end_index + 1
    return substrings


# Разбтвает код на линии (не работает с кодами в которых есть сиволы ASCII с номером больше 128)
async def lines(code):
    ans = []
    code = code.replace(' ** ', '**').replace(' **', '**').replace('** ', '**').replace('**', ' ** ')
    s1 = await extract_between(code, "'", "'")
    s2 = await extract_between(code, '"', '"')
    decode = dict()
    encode = s1 | s2
    cnt = 0
    for e in encode:
        t = chr(128 + cnt)
        decode[t] = e
        code = code.replace(e, t)
        cnt += 1
    # print(decode)
    code = code.split('\n')
    for e in code:
        if '\u200b' not in e:
            ans.append(e + '\n')
        else:
            ans.append('\n')
    for i in range(len(ans)):
        for e in decode:
            ans[i] = ans[i].replace(e, decode[e])
    return ans


# Удаляет коментарии
async def remove_comments(src):
    return re.sub('#.*', '', src)


# Считает количество токенов в строке (для gpt-3, gpt-3.5)
async def total_tokens(s):
    encoding = tiktoken.get_encoding("gpt2")
    input_ids = encoding.encode(s)
    # print(len(input_ids))
    return len(input_ids)


# Генерация кода
async def answer(prompt):
    conversation = [{'role': 'user', 'content': prompt}]
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=conversation,
        temperature=0.5,
        max_tokens=4080 - await total_tokens(prompt),
        top_p=1.0,
        frequency_penalty=0.21,
        presence_penalty=0.0,
    )
    return response["choices"][0]["message"]["content"]



# Собирает ссылки на задания с ссылки на урок
async def lesson_parser(_id, url):
    driver = users_data[_id].driver
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    hrefs = [a['href'] for a in soup.find_all(class_='student-task-list__task')]
    hrefs = ['https://lyceum.yandex.ru' + i for i in hrefs]
    return hrefs


# Приводит код к pep8
async def pep8(code):
    url = "https://extendsclass.com/python-formatter.html"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--crash-dumps-dir=/tmp')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver"), options=chrome_options)
    # driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    code = await lines(code)
    ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
    ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
    await asyncio.sleep(0.2)
    ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
    await asyncio.sleep(0.2)
    for e in code:
        ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
    await asyncio.sleep(2)
    convert_button = driver.find_element(By.ID, "format-code")
    ActionChains(driver).click(convert_button).perform()
    await asyncio.sleep(5)
    result = list(BeautifulSoup(driver.page_source, 'html.parser').find_all(class_='CodeMirror-line'))
    code_pep8 = '\n'.join([line.text for line in result])
    return code_pep8


# Реализация очереди
async def make_task(_id):
    while len(users_data[_id].links) != 0:
        # print(_data_links)
        await solve(users_data[_id].links[0], _id)
        if len(users_data[_id].links) != 0:
            users_data[_id].links.pop(0)
        users_data[_id].fck = 2000


# Функция нарешивания задач
async def solve(lesson_url, _id):
    # print(lesson_url)
    lesson_type = 'program'
    fla = 0

    driver = users_data[_id].driver
    await asyncio.sleep(0.2)

    try:

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        texts = soup.find_all('h2')
        jjj = 0
        for e in texts:
            if 'Формат ввода' in e:
                jjj = 1
        if jjj == 0:
            lesson_type = 'func/class'
    except:
        # print(1)
        return

    try:
        if 'не зарегестрированны' in driver.page_source.lower():
            driver.refresh()
        driver.get(lesson_url)
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return
    await asyncio.sleep(2)
    try:
        task_html = driver.page_source
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return
    try:
        if 'Зачтено' in driver.page_source or (
                'Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
            return

        if 'problem-statement' not in task_html:
            ActionChains(driver).click(
                driver.find_element(By.CLASS_NAME, "y4ef2d--task-description-opener").find_element(By.CLASS_NAME,
                                                                                                   "nav-tab.nav-tab_view_button")).perform()
            await asyncio.sleep(1)
            task_html = driver.page_source
    except:
        # print(driver.current_url)
        # print(task_html)
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return

    q = []
    samples = []
    forbidden_class = [['header']]

    try:
        soup = BeautifulSoup(task_html, 'html.parser')
        problem_statement = soup.find(class_='problem-statement')
        problem_statement_layer1 = problem_statement.findChildren(recursive=False)
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return

    try:
        for element in problem_statement_layer1:
            if element.has_attr('h2') or not element.has_attr('class'):
                if 'Формат ввода' in element:
                    lesson_type = 'program'
                continue
            # print(element['class'])
            if element['class'] in forbidden_class:
                continue
            if element['class'] == ['sample-tests']:
                samples.append(list(element.find_all('pre')))
            elif len(str.strip(element.text)) != 0:
                q.append(str.strip(element.text))
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return

    q = ''.join(q)
    for i in range(len(samples)):
        samples[i][0] = samples[i][0].text
        samples[i][1] = samples[i][1].text
    # print(samples)

    await asyncio.sleep(1)

    try:
        if 'Открыть редактор' in task_html:
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return

    prompt = template + q
    if lesson_type == 'program':
        f = 0
        for tests in samples:
            inp = tests[0].strip()
            out = tests[1].strip()
            if f == 0:
                prompt += sample_template[2] + inp + sample_template[1] + out
                f = 1
            else:
                prompt += sample_template[0] + inp + sample_template[1] + out
    elif lesson_type == 'func/class':
        for tests in samples:
            inp = tests[0].strip()
            out = tests[1].strip()
            prompt += '\n' + funcclass_template[0] + inp + funcclass_template[1] + out + '\n'
        prompt += "\nYou need to write only the code, not the program calling it"

    for zzz in range(5):

        await asyncio.sleep(2)
        try:

            ans = str(await answer(prompt))
            ans = ans.strip()
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return
        if ans[0] == '.' or ans[0] == ':':
            ans = ans[1::].strip()
        # print(ans)
        # print('-' * 50)
        ans = await remove_comments(ans)
        # print(ans)
        # print('-' * 50)
        try:
            ans = await pep8(ans)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return
        # print(ans)
        # print('-' * 50)
        ans = ans.strip()
        ans = await lines(ans)

        try:
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
            ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
            await asyncio.sleep(0.2)
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
            await asyncio.sleep(0.2)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

        try:
            for e in ans:
                if '```' not in e:
                    ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

        await asyncio.sleep(0.5)
        try:
            if fla == 0:
                await asyncio.sleep(
                    max(0, 300 + int((datetime.datetime.now() - users_data[_id].send_time).total_seconds())))
                # print('fhfhfhfhfhfh')
                fla = 1
            users_data[_id].send_time = datetime.datetime.now()
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
        except:
            print(1)
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

        try:
            shit = 0
            for t in range(100):
                driver.refresh()
                await asyncio.sleep(3)
                if 'Доработать' in driver.page_source and t > 15:
                    break
                if 'Зачтено' in driver.page_source or (
                        'Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
                    shit = 1
                    break
            if shit == 1:
                break
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return


if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)
