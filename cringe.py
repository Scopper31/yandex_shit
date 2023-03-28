#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import re
import time
from io import BytesIO
import openai
import sql
import tiktoken
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.message import ContentType
from bs4 import BeautifulSoup
from content import key
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from utils import TestStates
import datetime

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

yes_b = InlineKeyboardButton('Да', callback_data='yes_call')
no_b = InlineKeyboardButton('Нет', callback_data='no_call')
num_markup = InlineKeyboardMarkup().add(yes_b).add(no_b)


class User:
    def __init__(self, login='', wanna_commit_suicide='', driver='', qr_code='', send_time=datetime.datetime.now()):
        self.login = login
        self.links = []
        self.driver = driver
        self.qr_code = qr_code
        self.send_time = send_time
        self.wanna_commit_suicide = wanna_commit_suicide


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


@dp.callback_query_handler(lambda c: c.data == 'yes_call', state=TestStates.all())
async def process_callback_yes(callback_query: types.CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.set_state(TestStates.all()[5])
    await bot.send_message(callback_query.from_user.id, 'Гони пинкод')


@dp.message_handler(state=TestStates.TEST_STATE_5[0])
async def first_test_state_case_met(message: types.Message):
    pin = message.text
    users_data[message.from_user.id].pin = pin
    users_data[message.from_user.id].wanna_commit_suicide = True


@dp.callback_query_handler(lambda c: c.data == 'no_call', state=TestStates.all())
async def process_callback_no(callback_query: types.CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.reset_state()
    await bot.send_message(callback_query.from_user.id, 'Помянем. Иди в жопу')
    users_data[callback_query.from_user.id].wanna_commit_suicide = False


@dp.callback_query_handler(lambda c: c.data == 'stop', state=TestStates.all())
async def process_callback_stop(callback_query: types.CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    await state.reset_state()
    await bot.send_message(callback_query.from_user.id, 'Ввод данных прерван')


@dp.callback_query_handler(lambda c: c.data == 'solve_b')
async def process_callback_solve(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    users_data[callback_query.from_user.id] = User()
    state = dp.current_state(user=callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, 'Подтверждай вход через QR код')
    await login_qr(callback_query.from_user.id)
    await bot.send_photo(callback_query.from_user.id, photo=users_data[callback_query.from_user.id].qr_code)
    driver = users_data[callback_query.from_user.id].driver
    qr_url = driver.current_url
    while driver.current_url == qr_url:
        if 'Внутренняя ошибка: обновите страницу и попробуйте еще раз' in driver.page_source:
            await state.reset_state()
            await bot.send_message(callback_query.from_user.id, 'Давай по новой')
            return
        time.sleep(1)
    users_login(callback_query.from_user.id)
    sqlite_connection = sql.sql_connection()
    if not sql.check_existence(sqlite_connection, users_data[callback_query.from_user.id].login):
        await bot.send_message(callback_query.from_user.id, '❌')
        state = dp.current_state(user=callback_query.from_user.id)
        await state.reset_state()
        await bot.send_message(callback_query.from_user.id, 'У вас нет подписки((( сори')
    else:
        await bot.send_message(callback_query.from_user.id, '🆗')
        await state.set_state(TestStates.all()[1])
        await bot.send_message(callback_query.from_user.id,
                               'Присылай ссылки на уроки и задания (одно сообщение - одна ссылка):',
                               reply_markup=stop_markup)


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
    await bot.send_message(message.chat.id,
                           "Привет!\nЯ бот-помощник от sanyasupertank и popkapirat!\nЕсли у тебя нет времени решать задачи, я сделаю все за тебя автоматически.",
                           reply_markup=markup2)


@dp.message_handler(commands=['info'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, 'мне пока лень(((')


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
    sql.add_subscriber(sqlite_connection, payment_info['order_info']['email'])
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

    elif 'ильяпетух' in msg.text.lower():
        sqlite_connection = sql.sql_connection()
        sql.add_subscriber(sqlite_connection, msg.text.split()[1])
        sqlite_connection.close()
        await bot.send_message(msg.from_user.id, 'Ок бро, я тебя понял')
    else:
        await bot.send_message(msg.from_user.id, 'Что ты несешь?')


@dp.message_handler(state=TestStates.TEST_STATE_1[0])
async def third_test_state_case_met(message: types.Message):
    if type(check_url(message.text)) == list:
        if check_url(message.text) == ['task']:
            links_array = lesson_parser(message.text)
        else:
            links_array = [message.text]
        await message.reply('Погнали!', reply=False)

        if len(users_data[message.from_user.id].links) == 0:
            users_data[message.from_user.id].links.extend(links_array)
            await make_task(message.from_user.id)
        else:
            users_data[message.from_user.id].links.append(message.text)

        # await message.reply(f'Задача выполнена', reply=False)
    else:
        await message.delete()
        await message.reply('Ссылка говно!', reply=False)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


# 1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling

# Проверка что чел у нас в базе
def users_login(_id):
    driver = users_data[_id].driver
    yandex_user_data = driver.page_source
    k = yandex_user_data.find(""""username":""") + len(""""username":""") + 1
    yandex_user_data = yandex_user_data[k:k + 100:]
    username = yandex_user_data.split('"')[0]
    users_data[_id].login = username


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
    driver_login = webdriver.Chrome("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver",
                                    options=chrome_options)
    driver_login.get("https://passport.yandex.ru/auth?origin=lyceum&retpath=https%3A%2F%2Flyceum.yandex.ru%2F")
    ActionChains(driver_login).click(
        driver_login.find_element(By.CLASS_NAME, "AuthSocialBlock-provider.AuthSocialBlock-provider_code_qr")).perform()
    time.sleep(1)
    qr = driver_login.find_element(By.CLASS_NAME, "MagicField-qr").screenshot_as_png
    users_data[_id].driver = driver_login
    qr = BytesIO(qr)
    users_data[_id].qr_code = qr


# Проверка что ссылка на яндекс, возвращает урок или задание (задание - ["task"], урок - ["lesson"]
def check_url(url):
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


# Разбтвает код на линии (не работает с кодами в которых есть сиволы ASCII с номером больше 128)
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


# Удаляет коментарии
def remove_comments(src):
    return re.sub('#.*', '', src)


# Считает количество токенов в строке (для gpt-2 и gpt-3)
def total_tokens(s):
    encoding = tiktoken.get_encoding("gpt2")
    input_ids = encoding.encode(s)
    # print(len(input_ids))
    return len(input_ids)


# Генерация кода
def answer(s):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=s,
        temperature=0.5,
        max_tokens=4097 - total_tokens(s),
        top_p=1.0,
        frequency_penalty=0.23,
        presence_penalty=0.0,
    )
    return response["choices"][0]["text"]


# Собирает ссылки на задания с ссылки на урок
def lesson_parser(html):
    soup = BeautifulSoup(html, 'html.parser')
    hrefs = [a['href'] for a in soup.find_all(class_='student-task-list__task')]
    hrefs = ['https://lyceum.yandex.ru' + i for i in hrefs]
    return hrefs


# Приводит код к pep8
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
    driver = webdriver.Chrome("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver",
                              options=chrome_options)
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


# Реализация очереди
async def make_task(_id):
    _data_links = users_data[_id].links
    while (len(_data_links) != 0):
        solve(_data_links[0], _id)
        _data_links.pop(0)


# Функция нарешивания задач
def solve(lesson_url, _id):
    lesson_type = 'func/class'

    driver = users_data[_id].driver

    try:
        driver.get(lesson_url)
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return
    time.sleep(0.2)

    try:
        lesson_html = driver.page_source
        data = lesson_parser(lesson_html)
        # print(data)
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return

    if check_url(lesson_url) == ['task']:
        data = [lesson_url]

    for ind, task_url in enumerate(data):
        try:
            if 'не зарегестрированны' in driver.page_source.lower():
                driver.refresh()
            driver.get(task_url)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return
        time.sleep(2)
        try:
            task_html = driver.page_source
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return
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

        time.sleep(1)

        try:
            if 'Открыть редактор' in task_html:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                               "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

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
                return
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
                return
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
                return

            try:
                for e in ans:
                    ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                return

            time.sleep(0.5)
            fla = 0
            try:
                if fla == 0:  
                    time.sleep(max(0, 300 - (datetime.datetime.now() - users_data[_id].time).total_seconds))
                    fla = 1
                users_data[_id].time = datetime.datetime.now()
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                               "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
            except:
                # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                return

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
                return


if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)
