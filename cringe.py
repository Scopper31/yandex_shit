#! /usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import re
from io import BytesIO

import openai
import tiktoken
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from bs4 import BeautifulSoup
from content import key
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from misc.env import TOKENS
openai.api_key = key

template = 'Python, dont write any comments, dont write anything except code, provide answer in code block, obey pep8\nThe problem: '
sample_template = ["\nFor this example:\n", "\nIt outputs this:\n", "\nFor example if program gets this input:\n"]
funcclass_template = ["\nAn example of program that might use your code:\n",
                      "\nOutput it needs to produce:\n"]
one_task = -1

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKENS.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())

PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=1000 * 100)  # в копейках (руб)


class User:
    def __init__(self, login='', wanna_commit_suicide='', driver='', qr_code='', fck=1000,
                 send_time=datetime.datetime(2035, 1, 1, 1, 1)):
        self.login = login
        self.links = []
        self.driver = driver
        self.qr_code = qr_code
        self.send_time = send_time
        self.wanna_commit_suicide = wanna_commit_suicide
        self.fck = fck


users_data = {}


# Собирает ссылки на задания со ссылки на урок
async def lesson_parser(_id, url):
    driver = users_data[_id].driver
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    hrefs = [a['href'] for a in soup.find_all(class_='student-task-list__task')]
    hrefs = ['https://lyceum.yandex.ru' + i for i in hrefs]
    return hrefs


async def driver_end(__id):
    driver = users_data[__id].driver
    driver.quit()


async def time_end(_id):
    while users_data[_id].fck != 0:
        if users_data[_id].fck == -1:
            return
        users_data[_id].fck -= 1
        await asyncio.sleep(1)
    await driver_end(_id)
    kill_me = dp.current_state(user=_id)
    await kill_me.reset_state()
    users_data[_id].zaebalo = True
    # za_nashih = Bot(token=BOT_TOKEN)
    # await za_nashih.send_message(_id, 'бб')
    # await za_nashih.close()
    #await bot.send_message(_id, 'бб')


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


# 1111 1111 1111 1026, 12/22, CVC 000.
# run long-polling

# Проверка, что чел у нас в базе
async def users_login(_id):
    driver = users_data[_id].driver
    yandex_user_data = driver.page_source
    k = yandex_user_data.find(""""username":""") + len(""""username":""") + 1
    yandex_user_data = yandex_user_data[k:k + 100:]
    username = yandex_user_data.split('"')[0]
    users_data[_id].login = username.lower()


# poshel nahuy

# Проверка, что ссылка на яндекс, возвращает урок или задание (задание - ["task"], урок - ["lesson"]
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


if __name__ == "__main__":
    executor.start_polling(dp, on_shutdown=shutdown)
