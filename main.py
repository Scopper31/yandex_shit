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


key = "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"
openai.api_key = key

template = 'i need only python conde without any comments to solve this problem in code block: '


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


def click_yellow_button(im):
    yellow = (255, 219, 77)

    f = 0
    for x in range(im.width):
        for y in range(im.height):
            if im.getpixel((x, y)) == yellow:
                pyautogui.click(x + 5, y + 5)
                f = 1
                break
        if f == 1:
            break


def upload(s, redactor):
    ans = answer(template + s).strip()
    pyperclip.copy(ans)
    im = pyautogui.screenshot()

    if redactor():
        click_yellow_button(im)
        time.sleep(2)

    gray = (245, 242, 240)
    f = 0
    for x in range(im.width):
        for y in range(im.height):
            if im.getpixel((x, y)) == gray:
                pyautogui.click(x + 50, y + 50)
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.hotkey('ctrl', 'v')
                f = 1
                break
        if f == 1:
            break

    click_yellow_button(im)


def task_parser(url):
    pass


def main():
    question = '''
        Лист за листом, один меньше другого, пока не останется кочерыжка.
        Напишите класс Cabbage, при инициализации принимающий три аргумента: размер самого верхнего листа, шаг изменения размера при переходе к следующему листу и размер кочерыжки.
        Класс реализует метод leaf(), который печатает размер следующего листа (меньшего предыдущего на шаг), пока размер листа не меньше кочерыжки, дальше печатается размер кочерыжки.
        '''
    redactor = True

    lesson_url = input()
    data = #from lesson_url
    for task_url in data:
        question, redactor = task_parser(task_url)
        webbrowser.open_new_tab(task_url)
        upload(question, redactor)


if __name__ == '__main__':
    main()
