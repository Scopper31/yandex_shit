import pyautogui
from flask import Flask, request
import logging
import json
import os
import os
import time
import openai
import pyperclip
import webbrowser
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import re
from datetime import datetime

key = "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"
openai.api_key = key

template = 'i need only python code without any comments inside code, with abiding pep8 to solve this problem in code block: '
username = "Veselayakortoshka"
password = "Popkapiratbnh79"
lesson_url = ''
one_task = -1


def check_payment():
    url = 'bababuy'
    ime_now = datetime.now().timetuple()
    time_now = (ime_now[0], ime_now[1], ime_now[2])
    data = {'login': username, 'time_now': time_now}
    return bool(r.get(url, params=data))


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
    s1 = extract_between(code, "'", "'")
    s2 = extract_between(code, '"', '"')
    decode = dict()
    encode = s1 | s2
    for e in encode:
        decode[str(datetime.now())] = e
        code = code.replace(e, str(datetime.now()))
        time.sleep(0.01)
    code = code.replace(' ** ', '**').replace(' **', '**').replace('** ', '**').replace('**', ' ** ')
    code = code.split('\n')
    for e in code:
        if e != '\u200b':
            ans.append(e + '\n')
        else:
            ans.append('\n')
    for i in range(len(ans)):
        for e in decode:
            ans[i] = ans[i].replace(e, decode[e])
    return ans

def remove_comments(src):
    return re.sub('#.*', '', src)

def answer(s):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=s,
        temperature=0.5,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.5,
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
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    code = lines(code)
    ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
    ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
    time.sleep(0.2)
    ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
    time.sleep(0.2)
    for e in code:
        ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
    convert_button = driver.find_element(By.ID, "format-code")
    ActionChains(driver).click(convert_button).perform()
    time.sleep(3)
    result = list(BeautifulSoup(driver.page_source, 'html.parser').find_all(class_='CodeMirror-line'))
    code_pep8 = '\n'.join([line.text for line in result])
    return code_pep8


def main():
    question = '''
        Лист за листом, один меньше другого, пока не останется кочерыжка.
        Напишите класс Cabbage, при инициализации принимающий три аргумента: размер самого верхнего листа, шаг изменения размера при переходе к следующему листу и размер кочерыжки.
        Класс реализует метод leaf(), который печатает размер следующего листа (меньшего предыдущего на шаг), пока размер листа не меньше кочерыжки, дальше печатается размер кочерыжки.
        '''

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(30)
    driver.maximize_window()

    driver.get(lesson_url)
    mail_button = driver.find_element(By.CSS_SELECTOR, "[data-type=login]")
    button_pressed = mail_button.get_attribute('aria-pressed')
    if button_pressed == 'false':
        ActionChains(driver).click(mail_button).perform()
    time.sleep(0.2)
    driver.find_element("name", "login").send_keys(username)
    driver.find_element("name", "login").submit()
    driver.find_element("name", "passwd").send_keys(password)
    driver.find_element("name", "passwd").submit()
    w_passwd = 0
    while 'Неверный пароль' in driver.page_source and w_passwd < 3:
        print('Неверный пароль')
        w_passwd += 1
        # passwd = # Сюда пароль вводить во второй раз
        driver.find_element("name", "passwd").send_keys(passwd)
        driver.find_element("name", "passwd").submit()
        time.sleep(1)
    time.sleep(2)
    lesson_html = driver.page_source
    data = lesson_parser(lesson_html)
    print(data)

    for ind, task_url in enumerate(data):
        if one_task != -1:
            if ind + 1 != one_task:
                continue
        driver.get(task_url)
        time.sleep(2)
        task_html = driver.page_source
        if 'Зачтено' in driver.page_source or ('Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
            continue

        if 'problem-statement' not in task_html:
            ActionChains(driver).click(
                driver.find_element(By.CLASS_NAME, "y4ef2d--task-description-opener").find_element(By.CLASS_NAME,
                                                                                                   "nav-tab.nav-tab_view_button")).perform()
            time.sleep(1)
            task_html = driver.page_source

        q = []
        samples = []
        forbidden_class = [['header']]

        soup = BeautifulSoup(task_html, 'html.parser')
        problem_statement = soup.find(class_='problem-statement')
        problem_statement_layer1 = problem_statement.findChildren(recursive=False)

        for element in problem_statement_layer1:
            if element.has_attr('h2') or not element.has_attr('class'):
                continue
            # print(element['class'])
            if element['class'] in forbidden_class:
                continue
            if element['class'] == ['sample-tests']:
                samples.append(list(element.find_all('pre')))
            if len(str.strip(element.text)) != 0:
                q.append(str.strip(element.text))

        q = ''.join(q)
        for i in range(len(samples)):
            samples[i][0] = samples[i][0].text
            samples[i][1] = samples[i][1].text
        print(samples)

        time.sleep(1)

        if 'Открыть редактор' in task_html:
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()

        for zzz in range(5):

            time.sleep(2)
            ans = answer(template + q).strip()
            print(ans)
            print('-' * 50)
            ans = remove_comments(ans)
            print(ans)
            print('-' * 50)
            ans = pep8(ans)
            print(ans)
            print('-' * 50)
            ans = lines(ans)
            
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
            ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
            time.sleep(0.2)
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
            time.sleep(0.2)

            for e in ans:
                ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
            
            time.sleep(0.5)
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()

            shit = 0
            for t in range(100):
                driver.refresh()
                time.sleep(3)
                if 'Доработать' in driver.page_source and t > 10:
                    break
                if 'Зачтено' in driver.page_source or ('Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
                    shit = 1
                    break
            if shit == 1:
                break


if __name__ == '__main__':
    main()
