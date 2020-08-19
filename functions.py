import requests
import difflib
import time

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
    return b.json()

# Сравниваем две строки и получаем степень сходства от 0 до 1
def similarity(s1, s2):
    normalazed1 = s1.lower()
    normalazed2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalazed1, normalazed2)
    return matcher.ratio()