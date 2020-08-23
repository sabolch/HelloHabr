# импорт библиотеки
import requests
import time
from datetime import datetime
import telebot
import sqlite3
import difflib
import json

# Подтягиваем токен бота и все необходимое для получение средств за пиццу
from config import token, my_login, api_access_token
from functions import payment_history_last, similarity, balance, send_mobile, fibonacci, check_rules, user_ban, \
    user_unban, t_say_ban, t_say_unban
from telebot import types

# Создание бота
bot = telebot.TeleBot(token)

say_ban = ["бан", "забанить", "!бан", "мут", "!мут", "!ban", "ban", "mute", "!mute"]
say_unban = ["разбан", "разабанить", "!разбан", "размут", "!размут", "!unban", "unban", "unmute", "!unmute"]


@bot.message_handler(commands=['qiwi'])
def start_message(message):
    # последние 20 платежей на счёте киви
    last_payments = payment_history_last(my_login, api_access_token, '20', '', '')

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Создаём список из последних 200 айдишников в базе данных db_id_list
    cursor.execute("SELECT id FROM payments ORDER BY date DESC LIMIT 200")
    results = cursor.fetchall()

    db_id_list = []
    for i in range(len(results)):
        # Избавляемся от лишних знаков. Из ('19038863417') делаем 19038863417
        db_id = ''.join(results[i])
        db_id_list.append(db_id)

    print(db_id_list)

    y = len(last_payments['data']) - 1
    for i in last_payments['data']:
        pay_id = last_payments['data'][y]['txnId']
        pay_date = last_payments['data'][y]['date']
        pay_sum = last_payments['data'][y]['total']['amount']
        pay_comment = last_payments['data'][y]['comment']
        pay_provider = last_payments['data'][y]['provider']['shortName']
        pay_status = last_payments['data'][y]['status']
        pay_info = [(pay_id, pay_date, pay_sum, pay_comment, pay_provider, pay_status)]

        # Проверка наличия айди оплаты в БД. Если его нет, то добавляем все поля
        if str(pay_id) in db_id_list:
            print(f"Этот айди {pay_id} уже есть в базе данных, поэтому игнорируем.")
            pass
        else:
            cursor.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?)", pay_info)
            print(f"Вносим в базу данных: {pay_info}")
            connection.commit()

        y -= 1


# Декоратор для обработки начальной /start команды
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(True)
    markup.row('🌻', '💰', '📲', '🎲')
    bot.send_message(message.chat.id, "Привет, " + message.chat.first_name + " 🧟‍♂️", reply_markup=markup)

    bot.send_message(message.chat.id, 'Вот готовые команды на текущий момент: \n'
                                      '🖥   /dreamdesk\n'
                                      '💰   /balance\n'
                                      '📲   /payphone\n'
                                      '📖   /psalazh'
                     )
    # Получаем Telegram id пользователя (очевидно, для каждого пользователя он свой)
    user_id = message.chat.id

    bot.send_message(message.chat.id, 'Привет, анон!')

    # Проверка наличия пользователя в БД. Если его нет, то добавляем
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    sql = "SELECT * FROM white_list WHERE id=?"
    cursor.execute(sql, [user_id])
    fetch_id = cursor.fetchone()
    print(f"Фетч айди команды старт {fetch_id} .")
    connection.commit()

    if fetch_id is None:
        user_info = [(user_id, message.from_user.username, message.from_user.first_name, "True",
                      message.from_user.language_code)]
        cursor.executemany("INSERT INTO white_list VALUES (?,?,?,?,?)", user_info)
        connection.commit()
        print("Пользовать добавлен в базу данных")
    else:
        print("Пользовать уже есть в базе данных")


# Декоратор для обработки всех текстовых сообщений
@bot.message_handler(content_types=['text'])
def all_messages(message):
    # Получаем сообщение пользователя
    print(f"Пользователь написал {message.text}")
    bot.send_message(-1001166585345, f"!")

    # Получение статуса прав пользователя
    rules = check_rules(message.chat.id)

    if rules == "True":
        # Получаем total_say_ban от 0 до 1.
        total_say_ban = t_say_ban(message.text, say_ban)
        total_say_unban = t_say_unban(message.text, say_unban)

        # Оплата мобильного телефона
        if message.text == '📲' and message.chat.id == 441945234:
            def pay_my_phone(message):
                @bot.callback_query_handler(func=lambda call_pay: True)
                def callback_worker(call_pay):
                    if call_pay.data == "yep":  # call.data это callback_data, которую мы указали при объявлении кнопки
                        bot.send_message(call_pay.message.chat.id, 'Сообщение об успешном пополнении! : )')
                        bot.edit_message_reply_markup(call_pay.message.chat.id, call_pay.message.message_id)
                        bot.delete_message(message.chat.id, message_id=msg_del)
                    elif call_pay.data == "nope":
                        bot.send_message(message.chat.id, f"Операция отменена")
                        bot.edit_message_reply_markup(call_pay.message.chat.id, call_pay.message.message_id)
                        bot.delete_message(message.chat.id, message_id=msg_del)
                        pass

                print(f"Ввод суммы [{message.text}]")

                if message.text.isdigit():
                    balance_qiwi = balance(my_login, api_access_token)

                    if int(message.text) <= int(balance_qiwi):
                        keyboard_mts = types.InlineKeyboardMarkup()  # наша клавиатура
                        key_yes = types.InlineKeyboardButton(text='Подтвердить', callback_data='yep')  # кнопка «Да»
                        keyboard_mts.add(key_yes)  # добавляем кнопку в клавиатуру
                        key_no = types.InlineKeyboardButton(text='Отменить', callback_data='nope')
                        keyboard_mts.add(key_no)

                        bot.send_message(message.chat.id,
                                         f"На номер: +{my_login} \nбудет зачислена сумма: {message.text}₽",
                                         reply_markup=keyboard_mts)
                        global msg_del
                        msg_del = message.message_id + 1
                    else:
                        bot.send_message(message.chat.id,
                                         f"На вашем счёте недостаточно средств для проведения платежа. \n"
                                         f"Баланс счёта: {str(balance_qiwi)}₽")
                        msg_del = message.message_id + 1
                else:
                    bot.send_message(message.chat.id, f"Введите сумму числом. Только цифры 🤷🏻‍♂️")
                    bot.register_next_step_handler(message, pay_my_phone)

            bot.send_message(message.chat.id, f"Введите сумму:")
            # send_mobile(api_access_token, '1', '9187289906', 'Оплата телефона с помощью бота', '1')
            bot.register_next_step_handler(message, pay_my_phone)

        # Узнать баланс кошелька
        elif message.text == '💰' and message.chat.id == 441945234:
            # все балансы
            balances = balance(my_login, api_access_token)
            bot.send_message(message.chat.id, f"Ваш баланс: {balances} ₽")

        # Числа Фибоначчи
        elif message.text == '🌻':
            def get_fibonacci_number(message):  # получаем число
                global number
                number = message.text

                if number.isdigit():
                    result_fibonacci = fibonacci(int(number))
                    fib_number = list(result_fibonacci)[0]
                    fib_number = str(fib_number).replace('[', '').replace(']', '')
                    print(fib_number)
                    fib_sequence = list(result_fibonacci)[1]
                    fib_sequence = str(fib_sequence).replace('[', '').replace(']', '')
                    print(fib_sequence)

                    bot.send_message(message.chat.id, f"{number} - имеет следующую последовательность Фибоначчи: \n"
                                                      f"{fib_number}\n"
                                                      f"Золотым сечением данной последовательности является число: "
                                                      f"{fib_sequence}")

                    keyboard = types.InlineKeyboardMarkup()
                    key_yes = types.InlineKeyboardButton(text='❤️', callback_data='yes')  # кнопка «Да»
                    keyboard.add(key_yes)
                    key_no = types.InlineKeyboardButton(text='😡', callback_data='no')
                    keyboard.add(key_no)
                    bot.send_message(message.from_user.id, text=f"Вам понравилось качество нашего обслуживания?",
                                     reply_markup=keyboard)

                else:
                    bot.send_message(message.chat.id, f"Введите число")
                    bot.register_next_step_handler(message, get_fibonacci_number)

                    # следующий шаг – функция get_name

            @bot.callback_query_handler(func=lambda call: True)
            def callback_worker(call):
                if call.data == "yes":  # call.data это callback_data, которую мы указали при объявлении кнопки
                    bot.send_sticker(message.chat.id,
                                     'CAACAgIAAxkBAAID0l9BbMxW6Q0_yRZ7ahHsU8CQO6c7AALHAAMWHfwLeXVXmujsd1AbBA')

                    msg_id = message.message_id + 4
                    bot.delete_message(message.chat.id, msg_id)

                elif call.data == "no":
                    bot.send_sticker(message.chat.id,
                                     'CAACAgIAAxkBAAID0F9BbHvp_tcecJxgEApxkT3ZEnIIAAKsAAM60N8BRmmum8GHZ5wbBA')

                    msg_id = message.message_id + 4
                    bot.delete_message(message.chat.id, msg_id)

            # Фибоначчи

            bot.send_message(message.chat.id, "Введите число, чтобы получить последовельность чисел Фибоначчи"
                                              " и его золотое сечение 🙂")
            bot.register_next_step_handler(message, get_fibonacci_number)

        # Бан пользователя
        elif (total_say_ban > 0.80) and message.chat.id == 441945234:
            user_name = user_ban(message.text)
            bot.send_message(message.chat.id, f"Пользователь @{user_name} забанен.")

        # Разбан пользователя
        elif (total_say_unban > 0.80) and message.chat.id == 441945234:
            user_name = user_unban(message.text)
            bot.send_message(message.chat.id, f"Пользователь @{user_name} разбанен.")

        else:
            bot.send_message(message.chat.id, f"Вы написали: {message.text}")

    else:
        print("У пользователя нет прав")
        bot.send_message(message.chat.id, "Вы забанены администратором. \nДля разбана, свяжитесь с @sabolch")


# Запускаем бота, чтобы работал 24/7
if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=123)
