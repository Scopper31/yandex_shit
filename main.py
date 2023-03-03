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


key = "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"
openai.api_key = key

template = 'i need only python code (without any comments inside code, with observing pip8) to solve this problem in code block (): '
username = "Veselayakortoshka"
password = "Popkapiratbnh79"


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


def main():
    question = '''
        Лист за листом, один меньше другого, пока не останется кочерыжка.
        Напишите класс Cabbage, при инициализации принимающий три аргумента: размер самого верхнего листа, шаг изменения размера при переходе к следующему листу и размер кочерыжки.
        Класс реализует метод leaf(), который печатает размер следующего листа (меньшего предыдущего на шаг), пока размер листа не меньше кочерыжки, дальше печатается размер кочерыжки.
        '''

    lesson_url = input('Ссылку на урок\n')
    one_task = int(input('номер задания или -1\n'))

    driver = webdriver.Chrome()
    driver.implicitly_wait(30)
    driver.get(lesson_url)
    ActionChains(driver).click(
        driver.find_element(By.CLASS_NAME, "Button2.Button2_checked.Button2_size_l.Button2_view_default")).perform()
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
        if 'Зачтено' in driver.page_source:
            continue
        if 'problem-statement' not in task_html:
            ActionChains(driver).click(
                driver.find_element(By.CLASS_NAME, "y4ef2d--task-description-opener").find_element(By.CLASS_NAME,
                                                                                                   "nav-tab.nav-tab_view_button")).perform()
            time.sleep(1)
            task_html = driver.page_source

        q = []
        soup = BeautifulSoup(task_html, 'html.parser')
        legend_elements = soup.find_all(class_='legend')
        for element in legend_elements:
            if 'header' in element:
                continue
            if 'sample-tests' in element:
                continue
            q.append(element.text)
        if 'input-specification' in task_html:
            inputus = soup.find_all(class_='input-specification')
            for e in inputus:
                q.append(e.text)
        if 'output-specification' in task_html:
            output = soup.find_all(class_='output-specification')
            for e in output:
                q.append(e.text)

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
            pyperclip.copy(ans)
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-lines")).perform()
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(1)

            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()

            shit = 0
            for t in range(100):
                pyautogui.hotkey('f5')
                time.sleep(3)
                if 'Зачтено' in driver.page_source:
                    shit = 1
                    break
                if 'Доработать' in driver.page_source and t > 10:
                    break
            if shit == 1:
                break


if __name__ == '__main__':
    main()
