from flask import Flask, request
import json

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def check_params():
    log = request.form['login']
    t_n = request.form['time_now']
    with open('data.json') as json_file:
        data = json.load(json_file)
        if log in data:
            if t_n < data[log]:
                return 'True'
            else:
                return 'False'
        else:
            return 'False'



if __name__ == '__main__':
    app.run()
