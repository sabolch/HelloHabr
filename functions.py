import sqlite3
import telebot
import requests
import difflib
import time
from telebot import types
m_list = []

from config import token, my_login, api_access_token
# Создание бота
bot = telebot.TeleBot(token)

# История платежей - последние и следующие n платежей
# Отправляем запрос в киви, получаем json-ответ
def payment_history_last(my_login, api_access_token, rows_num, next_TxnId, next_TxnDate):
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + api_access_token
    parameters = {'rows': rows_num, 'nextTxnId': next_TxnId, 'nextTxnDate': next_TxnDate}
    h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + my_login + '/payments', params=parameters)
    return h.json()


def send_mobile(api_access_token, prv_id, to_account, comment, sum_pay):
    s = requests.Session()
    s.headers['Accept'] = 'application/json'
    s.headers['Content-Type'] = 'application/json'
    s.headers['authorization'] = 'Bearer ' + api_access_token
    postjson = {"id": "", "sum": {"amount": "", "currency": "643"},
                "paymentMethod": {"type": "Account", "accountId": "643"}, "comment": "",
                "fields": {"account": ""}}
    postjson['id'] = str(int(time.time() * 1000))
    postjson['sum']['amount'] = sum_pay
    postjson['fields']['account'] = to_account
    postjson['comment'] = comment
    res = s.post('https://edge.qiwi.com/sinap/api/v2/terms/' + prv_id + '/payments', json=postjson)
    print(res.json())
    return res.json()


# Баланс QIWI Кошелька
def balance(my_login, api_access_token):
    s = requests.Session()
    s.headers['Accept'] = 'application/json'
    s.headers['authorization'] = 'Bearer ' + api_access_token
    b = s.get('https://edge.qiwi.com/funding-sources/v2/persons/' + my_login + '/accounts')
    return b.json()['accounts'][0]['balance']['amount']


# Сравниваем две строки и получаем степень сходства от 0 до 1
def similarity(s1, s2):
    normalazed1 = s1.lower()
    normalazed2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalazed1, normalazed2)
    return matcher.ratio()


def fibonacci(x):
    sequence = []
    result = 0
    n = 1

    for i in range(x):
        result = result + n
        n = result - n
        sequence.append(result)

    golden_ratio = sequence[-1] / sequence[-2]

    return sequence, golden_ratio


# Проверка наличия у пользователя прав. Если его rules != True, то else
def check_rules(id):
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()
    sql = "SELECT rules FROM white_list WHERE id=?"
    cursor.execute(sql, [id])
    fetch_id = cursor.fetchone()
    connection.commit()

    if fetch_id is None:
        fetch_id = 'False'

    str_fetch_id = ''.join(fetch_id)
    print(f"Проверка прав пользователя: {str_fetch_id}")
    return str_fetch_id


# Определяем значение от 0 до 1
def t_say_ban(text, say_ban):
    for i in range(len(say_ban)):
        index_diff = similarity(text.split('@')[0].strip(), say_ban[i])
        m_list.append(index_diff)
    return max(m_list)


# Определяем значение от 0 до 1
def t_say_unban(text, say_unban):
    for i in range(len(say_unban)):
        index_diff = similarity(text.split('@')[0].strip(), say_unban[i])
        m_list.append(index_diff)
    return max(m_list)


# Бан пользователя>
def user_ban(text):
    user_name = text.split('@')[1].strip()
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Находим ублюдка по его username, меняем значение rules на False
    sql = """
          UPDATE white_list 
          SET rules = 'False' 
          WHERE user_name=?
          """
    cursor.execute(sql, [user_name])
    fetch_id = cursor.fetchone()
    connection.commit()
    return user_name


# Разбан пользователя
def user_unban(text):
    # Из "ban @sabolch" делаем "sabolch"
    user_name = text.split('@')[1].strip()
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Находим ублюдка по его username, меняем значение rules на True
    sql = """
          UPDATE white_list 
          SET rules = 'True' 
          WHERE user_name=?
          """
    cursor.execute(sql, [user_name])
    fetch_id = cursor.fetchone()
    connection.commit()
    return user_name



