import asyncio

from aiogram.utils.helper import Helper, HelperMode, ListItem
from bs4 import BeautifulSoup
import tiktoken
from aiogram import Dispatcher

from database.users_data import *


class TestStates(Helper):
    mode = HelperMode.snake_case

    TEST_STATE_0 = ListItem()
    TEST_STATE_1 = ListItem()
    TEST_STATE_2 = ListItem()
    TEST_STATE_3 = ListItem()
    TEST_STATE_4 = ListItem()
    TEST_STATE_5 = ListItem()


# Считает количество токенов в строке (для gpt-3, gpt-3.5)
async def total_tokens(s):
    encoding = tiktoken.get_encoding("gpt2")
    input_ids = encoding.encode(s)
    # print(len(input_ids))
    return len(input_ids)


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


# Собирает ссылки на задания со ссылки на урок
async def lesson_parser(_id, url):
    driver = users_data[_id].driver
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    hrefs = [a['href'] for a in soup.find_all(class_='student-task-list__task')]
    hrefs = ['https://lyceum.yandex.ru' + i for i in hrefs]
    return hrefs


async def time_end(_id, dp: Dispatcher):
    while users_data[_id].fck != 0:
        if users_data[_id].fck == -1:
            return
        users_data[_id].fck -= 1
        await asyncio.sleep(1)
    await driver_end(_id)
    kill_me = dp.current_state(user=_id)
    await kill_me.reset_state()
    users_data[_id].zaebalo = True


async def driver_end(__id):
    driver = users_data[__id].driver
    driver.quit()
