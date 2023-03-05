from flask import Flask, request
import json


app = Flask(__name__)


@app.route("/", methods=['GET', 'POST'])
def main():
    view = ''
    if request.method == 'POST':
        log = request.form['login']
        e_t = request.form['ending_time']
        with open('data.txt', 'w') as file:
            file.write(log + ':' + e_t)
    with open('data.txt') as file:
        li = file.readlines()
        view += '<br/>'.join(li)
    return view


if __name__ == '__main__':
    app.run()
