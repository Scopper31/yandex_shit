#! /usr/bin/env python
# -*- coding: utf-8 -*-
import config
import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from utils import TestStates
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import sqlite3
from sqlite3 import Error
import sql
import re
import time
from datetime import datetime
import openai
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import tiktoken
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from content import key


openai.api_key = key

template = 'Python, dont write any comments, provide answer in code block\nThe problem: '
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

markup2 = InlineKeyboardMarkup().add(button1).add(button2).add(button3)


stop_b = InlineKeyboardButton('Прервать', callback_data='stop')
stop_markup = InlineKeyboardMarkup().add(stop_b)


class User:
    def __init__(self, login='', passwd=''):
        self.login = login
        self.passwd = passwd
        self.links = []


users_data = {}


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
    #print('order_info')
    #print(pre_checkout_q.order_info)
    if not hasattr(pre_checkout_q.order_info, 'email'):
        return await bot.answer_pre_checkout_query(
            pre_checkout_q.id,
            ok=False,
            error_message='не введен логин Яндекс лицея')
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    #print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    sqlite_connection = sql.sql_connection()
    sql.add_subscriber(sqlite_connection, payment_info['order_info']['email'])
    sqlite_connection.close()
    for k, v in payment_info.items():
        pass
        #print(f"{k} = {v}")

    #print(payment_info)
    #print(message.successful_payment)
    await bot.send_message(message.chat.id, f"Платёж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")


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
    users_data[message.from_user.id] = User()
    users_data[message.from_user.id].login = message.text
    print(users_data)

    sqlite_connection = sql.sql_connection()
    if not sql.check_existence(sqlite_connection, users_data[message.from_user.id].login):
        await message.delete()
        await bot.send_message(message.from_user.id, '❌')
        state = dp.current_state(user=message.from_user.id)
        await state.reset_state()
        await message.reply('У вас нет подписки((( сори', reply=False)
    else:
        await message.delete()
        await bot.send_message(message.from_user.id, '🆗')
        state = dp.current_state(user=message.from_user.id)
        await state.set_state(TestStates.all()[2])
        await message.reply('Пароль:', reply=False)


@dp.message_handler(state=TestStates.TEST_STATE_2[0])
async def second_test_state_case_met(message: types.Message):
    users_data[message.from_user.id].passwd = message.text
    await message.delete()
    await bot.send_message(message.from_user.id, '🆗')
    state = dp.current_state(user=message.from_user.id)
    await state.set_state(TestStates.all()[3])
    await bot.send_message(message.from_user.id,
                           'Присылай ссылки на уроки и задания (одно сообщение - одна ссылка):',
                           reply_markup=stop_markup)


@dp.message_handler(state=TestStates.TEST_STATE_3[0])
async def third_test_state_case_met(message: types.Message):
    if type(check_url(message.text)) == list:
        await message.reply('Погнали!', reply=False)

        if len(users_data[message.from_user.id].links) == 0:
            users_data[message.from_user.id].links.append(message.text)
            await make_task(message.from_user.id)
        else:
            users_data[message.from_user.id].links.append(message.text)

        #await message.reply(f'Задача выполнена', reply=False)
    else:
        await message.delete()
        await message.reply('Ссылка говно!', reply=False)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


#1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling


def check_url(url):
    url = url.replace('https://', '')
    url = url.split('/')
    domain = url[0]
    if domain == "lyceum.yandex.ru":
        if 'courses' == url[1]:
            if 'groups' == url[3]:
                if 'lessons' == url[5]:
                    if 'tasks' == url[7]:
                        return ['task']
                    else:
                        return ['lesson']
                else:
                    return "Нужна сслыка на задание/урок, не на курс"
            else:
                return "Проверьте ссылку"
        else:
            return "Выберите курс и урок, бот работает с задачами, а не с курсами"
    else:
        return "Проверьте ссылку"


def extract_between(input_string, start_symbol, end_symbol):
    substrings = set()
    start_index = 0
    while True:
        start_index = input_string.find(start_symbol, start_index)
        if start_index == -1:
            break
        end_index = input_string.find(end_symbol, start_index + 1)
        if end_index == -1:
            break
        substrings.add(input_string[start_index + 1: end_index])
        start_index = end_index + 1
    return substrings


def lines(code):
    ans = []
    code = code.replace(' ** ', '**').replace(' **', '**').replace('** ', '**').replace('**', ' ** ')
    s1 = extract_between(code, "'", "'")
    s2 = extract_between(code, '"', '"')
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


def remove_comments(src):
    return re.sub('#.*', '', src)


def total_tokens(s):
    encoding = tiktoken.get_encoding("gpt2")
    input_ids = encoding.encode(s)
    print(len(input_ids))
    return len(input_ids)


def answer(s):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=s,
        temperature=0.5,
        max_tokens=4097 - total_tokens(s),
        top_p=1.0,
        frequency_penalty=0.2,
        presence_penalty=0.0,
    )
    return response["choices"][0]["text"]


def lesson_parser(html):
    soup = BeautifulSoup(html, 'html.parser')
    hrefs = [a['href'] for a in soup.find_all(class_='student-task-list__task')]
    hrefs = ['https://lyceum.yandex.ru' + i for i in hrefs]
    return hrefs


def pep8(code):
    url = "https://extendsclass.com/python-formatter.html"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--crash-dumps-dir=/tmp')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver", options=chrome_options)
    # driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    code = lines(code)
    ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
    ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
    time.sleep(0.2)
    ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
    time.sleep(0.2)
    for e in code:
        ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
    time.sleep(2)
    convert_button = driver.find_element(By.ID, "format-code")
    ActionChains(driver).click(convert_button).perform()
    time.sleep(3)
    result = list(BeautifulSoup(driver.page_source, 'html.parser').find_all(class_='CodeMirror-line'))
    code_pep8 = '\n'.join([line.text for line in result])
    return code_pep8


def make_task(id):
    _username = users_data[id].login
    _passwd = users_data[id].passwd
    _data_links = users_data[id].links
    while (len(_data_links) != 0):
        solve(_username, _passwd, _data_links[0])
        _data_links.pop(0)


def solve(username, passwd, lesson_url):
    lesson_type = 'func/class'

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--crash-dumps-dir=/tmp')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver", options=chrome_options)
    # driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(30)
    driver.maximize_window()

    try:
        driver.get(lesson_url)
        mail_button = driver.find_element(By.CSS_SELECTOR, "[data-type=login]")
        button_pressed = mail_button.get_attribute('aria-pressed')
        if button_pressed == 'false':
            ActionChains(driver).click(mail_button).perform()
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        exit(0)
    time.sleep(0.2)
    try:
        print(driver.current_url)
        driver.find_element("name", "login").send_keys(username)
        ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                       "Button2.Button2_size_l.Button2_view_action.Button2_width_max.Button2_type_submit")).perform()
        # driver.find_element("name", "login").submit()
        time.sleep(1)
        print(driver.current_url)
        if 'Такого аккаунта нет' in driver.page_source:
            print('sanya dolbaeb chto-to slomal')
            exit(0)
        if 'Логин не указан' in driver.page_source:
            print('ya dolbaeb chto-to slomal')
            exit(0)
        driver.find_element("name", "passwd").send_keys(passwd)
        ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                       "Button2.Button2_size_l.Button2_view_action.Button2_width_max.Button2_type_submit")).perform()
        # driver.find_element("name", "passwd").submit()
        print(driver.current_url)
        w_passwd = 0
        while 'Неверный пароль' in driver.page_source and w_passwd < 3:
            # print('Неверный пароль')
            w_passwd += 1
            # passwd = # Сюда пароль вводить во второй раз
            driver.find_element("name", "passwd").send_keys(passwd)
            driver.find_element("name", "passwd").submit()
            time.sleep(1)
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        exit(0)

    time.sleep(2)
    try:
        lesson_html = driver.page_source
        data = lesson_parser(lesson_html)
        # print(data)
    except:
        print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        exit(0)

    if check_url(lesson_url) == ['task']:
        data = [lesson_url]

    for ind, task_url in enumerate(data):
        try:
            if 'не зарегестрированны' in driver.page_source.lower():
                driver.refresh()
            driver.get(task_url)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)
        time.sleep(2)
        try:
            task_html = driver.page_source
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)
        try:
            if 'Зачтено' in driver.page_source or (
                    'Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
                continue

            if 'problem-statement' not in task_html:
                ActionChains(driver).click(
                    driver.find_element(By.CLASS_NAME, "y4ef2d--task-description-opener").find_element(By.CLASS_NAME,
                                                                                                       "nav-tab.nav-tab_view_button")).perform()
                time.sleep(1)
                task_html = driver.page_source
        except:
            print(driver.current_url)
            print(task_html)
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)

        q = []
        samples = []
        forbidden_class = [['header']]

        try:
            soup = BeautifulSoup(task_html, 'html.parser')
            problem_statement = soup.find(class_='problem-statement')
            problem_statement_layer1 = problem_statement.findChildren(recursive=False)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)

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
            exit(0)

        q = ''.join(q)
        for i in range(len(samples)):
            samples[i][0] = samples[i][0].text
            samples[i][1] = samples[i][1].text
        # print(samples)

        time.sleep(1)

        try:
            if 'Открыть редактор' in task_html:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                               "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)

        for zzz in range(5):

            time.sleep(2)
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
            try:
                ans = str(answer(prompt).strip())
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)
            if ans[0] == '.' or ans[0] == ':':
                ans = ans[1::].strip()
            # print(ans)
            # print('-' * 50)
            ans = remove_comments(ans)
            # print(ans)
            # print('-' * 50)
            try:
                ans = pep8(ans)
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)
            # print(ans)
            # print('-' * 50)
            ans = lines(ans)

            try:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
                ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
                time.sleep(0.2)
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
                time.sleep(0.2)
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)

            try:
                for e in ans:
                    ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)

            time.sleep(0.5)

            try:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                               "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)

            try:
                shit = 0
                for t in range(100):
                    driver.refresh()
                    time.sleep(3)
                    if 'Доработать' in driver.page_source and t > 10:
                        break
                    if 'Зачтено' in driver.page_source or (
                            'Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
                        shit = 1
                        break
                if shit == 1:
                    break
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)


if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)
