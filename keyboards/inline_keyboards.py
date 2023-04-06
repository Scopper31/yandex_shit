from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

button1 = InlineKeyboardButton('Купить подписку', callback_data='buy_b')
button2 = InlineKeyboardButton('Решить задачи', callback_data='solve_b')
button3 = InlineKeyboardButton('Информация', callback_data='info_b')

markup2 = InlineKeyboardMarkup().add(button1).add(button2).add(button3)

stop_b = InlineKeyboardButton('Прервать', callback_data='stop')
stop_markup = InlineKeyboardMarkup().add(stop_b)

yes_b = InlineKeyboardButton('Да', callback_data='yes_call')
no_b = InlineKeyboardButton('Нет', callback_data='no_call')

num_markup = InlineKeyboardMarkup().add(yes_b).add(no_b)
