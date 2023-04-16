import asyncio

from database.users_data import *

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from io import BytesIO


# Проверка, что чел у нас в базе
async def users_login(_id):
    driver = users_data[_id].driver
    yandex_user_data = driver.page_source
    k = yandex_user_data.find(""""username":""") + len(""""username":""") + 1
    yandex_user_data = yandex_user_data[k:k + 100:]
    username = yandex_user_data.split('"')[0]
    users_data[_id].login = username.lower()


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
    driver_login = webdriver.Chrome(service=Service("/lhope/.wdm/drivers/chromedriver/linux64/111.0.5563/chromedriver"),
                                    options=chrome_options)
    driver_login.get("https://passport.yandex.ru/auth?origin=lyceum&retpath=https%3A%2F%2Flyceum.yandex.ru%2F")
    ActionChains(driver_login).click(
        driver_login.find_element(By.CLASS_NAME, "AuthSocialBlock-provider.AuthSocialBlock-provider_code_qr")).perform()
    await asyncio.sleep(1)
    qr = driver_login.find_element(By.CLASS_NAME, "MagicField-qr").screenshot_as_png
    users_data[_id].driver = driver_login
    qr = BytesIO(qr)
    users_data[_id].qr_code = qr
