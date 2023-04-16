from datetime import datetime
import requests as r


def check_payment():
    log = input()
    time_now = datetime.now().date().isoformat()
    time_now = list(map(int, time_now.split('-')))
    f = 0
    file = []
    resp = r.get('http://127.0.0.1:5000')

    # 2. If the response content is 200 - Status Ok, Save The HTML Content:
    if resp.status_code == 200:
        file = resp.text.split('<br/>')
    for i in file:
        login, ending_time = i.strip().split(':')
        ending_time = list(map(int, ending_time.split('-')))
        if log == login:
            if time_now < ending_time:
                f = 1
    if f:
        return True
    else:
        return False


def add():
    login = input()
    d, m, y = input().split()
    time = '-'.join([y, m, d])
    data = {'login': f'{login}', 'ending_time': f'{time}'}
    r.post('http://127.0.0.1:5000', data=data)


print(check_payment())
