import asyncio

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

import re


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
    driver = webdriver.Chrome(service=Service("/lhope/.wdm/drivers/chromedriver/linux64/111.0.55"
                                              "63/chromedriver"), options=chrome_options)
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


# Разбивает код на линии (не работает с кодами в которых есть символы ASCII с номером больше 128)
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


# Вычленяет код между двумя заданными символами
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


# Удаляет комментарии
async def remove_comments(src):
    return re.sub('#.*', '', src)
