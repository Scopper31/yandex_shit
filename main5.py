import re
import time
from datetime import datetime
import openai
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import torch
from transformers import AutoTokenizer

key = "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"
openai.api_key = key

template = 'Python, dont write any comments, provide answer in code block\nThe problem: '
sample_template = ["\nFor this example:\n", "\nIt outputs this:\n", "\nFor example if program gets this input:\n"]
funcclass_template = ["\nAn example of program that might use your code:\n",
                      "\nOutput it needs to produce:\n"]
lesson_url = ''
one_task = -1


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
    print(decode)
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
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    input_ids = torch.tensor(tokenizer.encode(s)).unsqueeze(0)
    return len(input_ids[0])
  
  
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


def solve(username, passwd, lesson_url):
    lesson_type = 'func/class'

    chrome_options = webdriver.ChromeOptions()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(30)
    driver.maximize_window()

    try:
        driver.get(lesson_url)
        mail_button = driver.find_element(By.CSS_SELECTOR, "[data-type=login]")
        button_pressed = mail_button.get_attribute('aria-pressed')
        if button_pressed == 'false':
            ActionChains(driver).click(mail_button).perform()
    except:
        print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        exit(0)
    time.sleep(0.2)
    try:
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
    except:
        print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        exit(0)

    time.sleep(2)
    try:
        lesson_html = driver.page_source
        data = lesson_parser(lesson_html)
        print(data)
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
            print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)
        time.sleep(2)
        try:
            task_html = driver.page_source
        except:
            print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
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
            print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)

        q = []
        samples = []
        forbidden_class = [['header']]

        try:
            soup = BeautifulSoup(task_html, 'html.parser')
            problem_statement = soup.find(class_='problem-statement')
            problem_statement_layer1 = problem_statement.findChildren(recursive=False)
        except:
            print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
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
            print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            exit(0)

        q = ''.join(q)
        for i in range(len(samples)):
            samples[i][0] = samples[i][0].text
            samples[i][1] = samples[i][1].text
        print(samples)

        time.sleep(1)

        try:
            if 'Открыть редактор' in task_html:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                               "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
        except:
            print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
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
                print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)
            if ans[0] == '.' or ans[0] == ':':
                ans = ans[1::].strip()
            print(ans)
            print('-' * 50)
            ans = remove_comments(ans)
            print(ans)
            print('-' * 50)
            try:
                ans = pep8(ans)
            except:
                print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)
            print(ans)
            print('-' * 50)
            ans = lines(ans)

            try:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
                ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
                time.sleep(0.2)
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
                time.sleep(0.2)
            except:
                print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)

            try:
                for e in ans:
                    ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
            except:
                print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)

            time.sleep(0.5)

            try:
                ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
            except:
                print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
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
                print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
                exit(0)


if __name__ == '__main__':
    solve()
