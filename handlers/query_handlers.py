from aiogram import Dispatcher
from cringe import bot, types, User, TestStates
from cringe import sql, asyncio, threading, login_qr
from cringe import users_login, stop_markup, time_end
from cringe import users_data, PAYMENTS_TOKEN, PRICE


def register_query_handlers(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data == 'stop', state=TestStates.all())
    async def process_callback_stop(callback_query: types.CallbackQuery):
        state = dp.current_state(user=callback_query.from_user.id)
        await state.reset_state()
        users_data[callback_query.from_user.id].links = []
        users_data[callback_query.from_user.id].fck = -1
        await bot.send_message(callback_query.from_user.id, 'Ввод данных прерван')

    @dp.callback_query_handler(lambda c: c.data == 'solve_b')
    async def process_callback_solve(callback_query: types.CallbackQuery):
        await callback_query.message.delete()
        users_data[callback_query.from_user.id] = User()
        state = dp.current_state(user=callback_query.from_user.id)
        await bot.send_message(callback_query.from_user.id, 'Подтверждай вход через QR код')
        await login_qr(callback_query.from_user.id)
        sending = await bot.send_photo(callback_query.from_user.id, photo=users_data[callback_query.from_user.id].qr_code)
        sending_id = sending.message_id
        driver = users_data[callback_query.from_user.id].driver
        qr_url = driver.current_url
        while driver.current_url == qr_url:
            if 'Внутренняя ошибка: обновите страницу и попробуйте еще раз' in driver.page_source:
                await state.reset_state()
                await bot.send_message(callback_query.from_user.id, 'Давай по новой')
                return
            await asyncio.sleep(1)
        await users_login(callback_query.from_user.id)
        sqlite_connection = sql.sql_connection()
        if not sql.check_existence(sqlite_connection, users_data[callback_query.from_user.id].login.lower()):
            await bot.delete_message(callback_query.from_user.id, sending_id)
            await bot.send_message(callback_query.from_user.id, '❌')
            state = dp.current_state(user=callback_query.from_user.id)
            await state.reset_state()
            await bot.send_message(callback_query.from_user.id, 'У вас нет подписки((( сори')
        else:
            await bot.delete_message(callback_query.from_user.id, sending_id)
            await bot.send_message(callback_query.from_user.id, '🆗')
            await state.set_state(TestStates.all()[1])
            await bot.send_message(callback_query.from_user.id,
                                   'Присылай ссылки на уроки и задания (одно сообщение - одна ссылка):',
                                   reply_markup=stop_markup)
            thread_time = threading.Thread(target=asyncio.run, args=(time_end(callback_query.from_user.id),))
            thread_time.start()
            while users_data[callback_query.from_user.id].fck != 0:
                if users_data[callback_query.from_user.id].fck == -1:
                    break
                await asyncio.sleep(1)
            if users_data[callback_query.from_user.id].fck == 0:
                await bot.send_message(callback_query.from_user.id, 'бб')

    @dp.callback_query_handler(lambda c: c.data == 'info_b')
    async def process_callback_info(callback_query: types.CallbackQuery):
        await callback_query.message.delete()
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, 'Информаиция:')
        await bot.send_message(callback_query.from_user.id, 'В другой жизни!')

    @dp.pre_checkout_query_handler(lambda query: True)
    async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
        if not hasattr(pre_checkout_q.order_info, 'email'):
            return await bot.answer_pre_checkout_query(
                pre_checkout_q.id,
                ok=False,
                error_message='не введен логин Яндекс лицея')
        await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

    @dp.callback_query_handler(lambda c: c.data == 'buy_b')
    async def process_callback_buy2(callback_query: types.CallbackQuery):
        await callback_query.message.delete()
        await bot.answer_callback_query(callback_query.id)
        if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
            await bot.send_message(callback_query.from_user.id, "Тестовый платеж!!!")
            await bot.send_message(callback_query.from_user.id,
                                   'В поле "Доставка" введите логин вашего Яндекс аккаунта с лицеем')

        await bot.send_invoice(callback_query.from_user.id,
                               title="Подписка на бота",
                               description="Активация подписки на бота на 1 месяц",
                               provider_token=PAYMENTS_TOKEN,
                               currency="rub",
                               photo_url="https://www.aroged.com/wp-content/uploads/2022/06/Telegram-has-a-premium"
                                         "-subscription.jpg",
                               photo_width=416,
                               photo_height=234,
                               photo_size=416,
                               need_email=True,
                               is_flexible=False,
                               prices=[PRICE],
                               start_parameter="one-month-subscription",
                               payload="test-invoice-payload")

