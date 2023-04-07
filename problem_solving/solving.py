# Реализация очереди
async def make_task(_id):
    while len(users_data[_id].links) != 0:
        # print(_data_links)
        await solve(users_data[_id].links[0], _id)
        if len(users_data[_id].links) != 0:
            users_data[_id].links.pop(0)


# Функция нарешивания задач
async def solve(lesson_url, _id):
    # print(lesson_url)
    lesson_type = 'program'
    fla = 0

    driver = users_data[_id].driver
    await asyncio.sleep(0.2)

    try:

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        texts = soup.find_all('h2')
        jjj = 0
        for e in texts:
            if 'Формат ввода' in e:
                jjj = 1
        if jjj == 0:
            lesson_type = 'func/class'
    except:
        # print(1)
        return

    try:
        if 'не зарегестрированны' in driver.page_source.lower():
            driver.refresh()
        driver.get(lesson_url)
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return
    await asyncio.sleep(2)
    try:
        task_html = driver.page_source
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return
    try:
        if 'Зачтено' in driver.page_source or (
                'Вердикт' in driver.page_source and not 'Доработать' in driver.page_source):
            return

        if 'problem-statement' not in task_html:
            ActionChains(driver).click(
                driver.find_element(By.CLASS_NAME, "y4ef2d--task-description-opener").find_element(By.CLASS_NAME,
                                                                                                   "nav-tab.nav-tab_view_button")).perform()
            await asyncio.sleep(1)
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

    await asyncio.sleep(1)

    try:
        if 'Открыть редактор' in task_html:
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_type_link.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
    except:
        # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
        return

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

    for zzz in range(5):

        await asyncio.sleep(2)
        try:

            ans = str(await answer(prompt))
            ans = ans.strip()
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return
        if ans[0] == '.' or ans[0] == ':':
            ans = ans[1::].strip()
        # print(ans)
        # print('-' * 50)
        ans = await remove_comments(ans)
        # print(ans)
        # print('-' * 50)
        try:
            ans = await pep8(ans)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return
        # print(ans)
        # print('-' * 50)
        ans = ans.strip()
        ans = await lines(ans)

        try:
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
            ActionChains(driver).key_down('\ue009').send_keys("a").key_up('\ue009').send_keys('\ue003').perform()
            await asyncio.sleep(0.2)
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME, "CodeMirror-line")).perform()
            await asyncio.sleep(0.2)
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

        try:
            for e in ans:
                if '```' not in e:
                    ActionChains(driver).send_keys('\ue011').send_keys(e).perform()
        except:
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

        await asyncio.sleep(0.5)
        try:
            if fla == 0:
                await asyncio.sleep(
                    max(0, 300 + int((datetime.datetime.now() - users_data[_id].send_time).total_seconds())))
                # print('fhfhfhfhfhfh')
                fla = 1
            users_data[_id].send_time = datetime.datetime.now()
            ActionChains(driver).click(driver.find_element(By.CLASS_NAME,
                                                           "Button2.Button2_size_l.Button2_theme_action.Button2_view_lyceum.y1b87d--comments__link")).perform()
        except:
            print(1)
            # print('Что-то пошло не так. Проверьте ссылку и попробуйте еще раз.')
            return

        try:
            shit = 0
            for t in range(100):
                driver.refresh()
                await asyncio.sleep(3)
                if 'Доработать' in driver.page_source and t > 15:
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