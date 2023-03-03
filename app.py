import PySimpleGUI as sg
import main5

layout = [[sg.Text('your yandex login:', size=(15, None)), sg.InputText(size=(50, 1))],
          [sg.Text('your yandex password:', size=(15, None)), sg.InputText(size=(50, 1))],
          [sg.Text('link of the lesson:', size=(15, None)), sg.InputText(size=(50, 1))],
          [sg.Text('number of the task or -1:', size=(15, None)), sg.InputText(size=(50, 1))],
          [sg.Button('Start'), sg.Button('Stop')]]

window = sg.Window('Yandex Lyceum', layout)

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == 'Stop':
        break

    if event == 'Start':
        main5.username = values[0]
        main5.password = values[1]
        main5.lesson_url = values[2]
        main5.one_task = int(values[3])
        main5.main()
window.close()
