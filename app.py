from requests import post, get
from flask import Flask, request
from flask_cors import CORS
import streamtel
import smsgorod
import beeline
import re
import json
import billing
import logging
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
CORS(app)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)

DEFAULT_SMS_CONFIG = {
    'provider': {
        'name': os.getenv('SMS_DEFAULT_PROVIDER'),
        'key': os.getenv('SMS_DEFAULT_PROVIDER_KEY'),
        'sender': os.getenv('SMS_DEFAULT_PROVIDER_SENDER')
    },
    'price': float(os.getenv('SMS_DEFAULT_PRICE'))
}


def provider(providerName):
    providers = {
        'Stream Telecom': streamtel.Gateway,
        'SMS gorod': smsgorod.Gateway,
        'Beeline': beeline.Gateway
    }
    print('provider', providers[providerName])
    return providers[providerName]


def valid_uuid(uuid):
    regex = re.compile(
        '^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z',
        re.I)
    match = regex.match(uuid)
    return bool(match)


def getDBAccountInfo(business_id):
    if business_id is None:
        return {'business_id': None}
    if not valid_uuid(business_id):
        app.logger.debug(f"Bad business ID: {business_id}")
        raise ValueError("Bad business ID")
    notification_settings = DEFAULT_SMS_CONFIG
    account = [{'business_id': business_id,
                'notification_settings': DEFAULT_SMS_CONFIG}]
    return account[0]


def getGateway(business_id):
    app.logger.info(f'getGateway: {business_id}')
    if business_id is not None and not valid_uuid(business_id):
        app.logger.debug(f"Bad business ID: {business_id}")
        raise ValueError("Bad business ID")
    if business_id is None:
        notification_settings = DEFAULT_SMS_CONFIG
        account = {'business_id': None}
    else:
        account = getDBAccountInfo(business_id)
        if account is None:
            app.logger.debug("Business account not found")
            raise ValueError("Business account not found")
        notification_settings = account.get('notification_settings')
    if notification_settings is None:
        app.logger.debug("Notification settings not found")
        raise ValueError("Notification settings not found")
    providerInfo = notification_settings.get('provider')
    gateway = provider(providerInfo.get('name'))(providerInfo)
    app.logger.info(f'getGateway {gateway}, {account}')
    return gateway, account


@app.route('/send')
def send_message():
    print('send_message: ', request.args)
    app.logger.info(f'IN: {request.args}')
    amount = float(DEFAULT_SMS_CONFIG.get('price', 5.0))
    phone = request.args.get('phone')
    if phone is None:
        app.logger.debug("No phone")
        return json.dumps({'error': 'No phone'})
    text = request.args.get('text')
    if text is None:
        app.logger.debug("No text")
        return json.dumps({'error': 'No text'})
    business_id = request.args.get('business_id', '')
    if business_id == '':
        business_id = None
    time = request.args.get('time', '')

    try:
        gateway, account = getGateway(business_id)
    except Exception as e:
        app.logger.error("error: {0}".format(e))
        return json.dumps({'error': "{0}".format(e)})

    transaction_id = None
    transaction_result = None

    if business_id is not None:
        # пытаемся зарезервировать сумму на счете
        transaction_id, transaction_result = billing.SMSReserveSum(
            business=business_id, amount=amount, params={})
        app.logger.debug(
            f'Transaction: {transaction_id}, {transaction_result}')
        if transaction_id is None:
            return json.dumps(transaction_result or {'error',
                                                     'Transaction failed'})

    # оправляем СМС
    res = gateway.send(phone, text, time)
    app.logger.debug(f"Response: {res}")

    if transaction_id is not None:
        # Отменяем резервирование
        # TODO указать причину отмены
        transaction_id, transaction_result = billing.undoTransaction(
            transactionId=transaction_id, params={
                'gatewayResponse': res,
                'provider': DEFAULT_SMS_CONFIG.get('provider', {}).get('name')
                }
              )

    if res.get('success', False):
        # опять резервируем, но уже с ID провайдера СМС,
        # чтобы потом проверить статус СМС
        parts = gateway.Parts(res)
        app.logger.debug(f'SMS parts: {parts}')
        if parts is not None:
            amount = float(amount * float(parts))
        transaction_id, transaction_result = billing.SMSReserveSum(
          business=business_id,
          amount=amount,
          params={
            'gatewayResponse': res,
            'parts': parts,
            'provider': DEFAULT_SMS_CONFIG.get('provider', {}).get('name')})

    try:
        return json.dumps({'response': res, 'transaction': transaction_id})
    except Exception as e:
        return json.dumps({'error': "{0}".format(e)})


@app.route('/check', methods=['POST'])
def check_messages():

    data = request.get_json()

    try:
        gateway, account = getGateway(None)
    except Exception as e:
        app.logger.error("error: {0}".format(e))
        return json.dumps({'error': "{0}".format(e)})

    transactions = billing.getWaitingTransactions()

    app.logger.debug(f"transactions: {transactions}")
    IDs = [item.get('id') for item in transactions]

    if len(IDs) == 0:
        return json.dumps({'result': 'no data'})

    res = gateway.status(IDs)
    app.logger.debug(f"Message statuses: {res}")

    if res.get('status') == 'error':
        return json.dumps({'response': res})

    costs = [item for item in res.get('data')]

    app.logger.debug(f"costs: {costs}")

    for sms in costs:
        foundTransactions = [item for item in transactions if str(
            item.get('id')) == str(sms.get('id'))]
        if len(foundTransactions) != 1:
            app.logger.debug(f"Wrong SMS ID: {sms}")
            continue

        if sms.get('status') == 'delivered':
            transaction_id,
            transaction_result = billing.SMSDelivered(
                business=foundTransactions[0].get('business'),
                amount=float(sms.get('cost')),
                transactionId=foundTransactions[0].get('transaction'),
                params={
                    'smsStatus': sms,
                    'provider': foundTransactions[0].get('provider')
                })

    try:
        return json.dumps({'response': res})
    except Exception as e:
        return json.dumps({'error': "{0}".format(e)})


@app.route('/balance/<business_id>', methods=['GET'])
def balance(business_id):
    try:
        gateway = getGateway(business_id)
        res = gateway.balance()
        return json.dumps({'response': res})
    except Exception as e:
        return json.dumps({'error': "{0}".format(e)})


if __name__ == "__main__":

    app.run(host='0.0.0.0')
