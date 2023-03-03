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

key = "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"
openai.api_key = key

template = 'i need only python code without any comments inside code, with observing pip8 to solve this problem in code block: '
username = "Veselayakortoshka"
password = "Popkapiratbnh79"
lesson_url = ''
one_task = -1


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
    beatify = webdriver.Chrome(options=chrome_options)
    beatify.get(url)
    inp = beatify.find_element(By.CSS_SELECTOR, "[class=CodeMirror-code]")
    pyperclip.copy(code)
    ActionChains(beatify).key_down('\ue009').send_keys("a").perform()
    ActionChains(beatify).key_down('\ue009').send_keys("v").perform()
    convert_button = beatify.find_element(By.ID, "format-code")
    ActionChains(beatify).click(convert_button).perform()
    copy_button = beatify.find_element(By.ID, "copy-result")
    ActionChains(beatify).click(copy_button).perform()
    code_pep8 = pyperclip.paste()
    return code_pep8


def main():
    question = '''
        Лист за листом, один меньше другого, пока не останется кочерыжка.
        Напишите класс Cabbage, при инициализации принимающий три аргумента: размер самого верхнего листа, шаг изменения размера при переходе к следующему листу и размер кочерыжки.
        Класс реализует метод leaf(), который печатает размер следующего листа (меньшего предыдущего на шаг), пока размер листа не меньше кочерыжки, дальше печатается размер кочерыжки.
        '''

    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")
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
        forbidden_class = [['header'], ['sample-tests']]

        soup = BeautifulSoup(task_html, 'html.parser')
        problem_statement = soup.find(class_='problem-statement')
        problem_statement_layer1 = problem_statement.findChildren(recursive=False)

        for element in problem_statement_layer1:
            if element.has_attr('h2') or not element.has_attr('class'):
                continue
            # print(element['class'])
            if element['class'] in forbidden_class:
                continue
            if len(str.strip(element.text)) != 0:
                q.append(str.strip(element.text))

        q = ''.join(q)
        print(q)
        samples = []
        sample_tests = soup.find_all(class_='sample-tests')
        for element in sample_tests:
            samples.append(element.text)
        samples = ''.join(samples)

        time.sleep(1)

        if 'Открыть редактор' in task_html:
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()

        for zzz in range(5):

            time.sleep(2)
            ans = answer(template + q).strip()
            print(ans)
            ans = remove_comments(ans)
            print(ans)
            pyperclip.copy(ans)
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-code")).perform()
            ActionChains(driver).key_down('\ue009').send_keys("a").perform()
            ActionChains(driver).key_down('\ue009').send_keys("v").perform()
            time.sleep(1)

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
