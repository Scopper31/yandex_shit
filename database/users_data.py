import datetime

users_data = {}


class User:
    def __init__(self, login='', wanna_commit_suicide='', driver='', qr_code='', fck=1000,
                 send_time=datetime.datetime(2035, 1, 1, 1, 1)):
        self.login = login
        self.links = []
        self.driver = driver
        self.qr_code = qr_code
        self.send_time = send_time
        self.wanna_commit_suicide = wanna_commit_suicide
        self.fck = fck
