from requests import post, get
from flask import Flask, request
from flask_cors import CORS
import streamtel
import smsgorod
import beeline
import re
import json
import db
from config import CONFIG as config
import logging


DEFAULT_SMS_CONFIG = config['DEFAULT']['SMS']

app = Flask(__name__)
CORS(app)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)


def get_folder(headers):
    #print(headers)
    if 'businessid' in headers and len(headers['businessid']) > 0:
        url = 'http://localhost:3000/my_business?id=eq.'+headers['businessid']
        try:
          res = get(url, headers={'Authorization':headers['Authorization']}, timeout=3)
          j = res.json()
          return j[0]['id']
        except Exception:
          pass
    else:
        url = 'http://localhost:3000/rpc/me'
        try:
          res = post(url, headers={'Authorization':headers['Authorization']}, timeout=3)
          j = res.json()
          print(j)
          return j['id'][:9]
        except Exception:
          pass


def provider(providerName):
  providers = {
    'Stream Telecom': streamtel.Gateway,
    'SMS gorod': smsgorod.Gateway,
    'Beeline': beeline.Gateway
  }
  print('provider', providers[providerName])
  return providers[providerName]


def valid_uuid(uuid):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid)
    return bool(match)


def getDBAccountInfo(business_id):
  if business_id == None:
    return {'business_id': None}
  if not valid_uuid(business_id):
    app.logger.debug("Bad business ID: {business_id}")
    raise ValueError("Bad business ID")
  account = db.db_account(business_id)
  return account[0]


def getGateway(business_id):
  if not business_id == None and not valid_uuid(business_id):
    app.logger.debug(f"Bad business ID: {business_id}")
    raise ValueError("Bad business ID")
  if business_id == None:
    notification_settings=DEFAULT_SMS_CONFIG
    account = {'business_id': None}
  else:
    account = getDBAccountInfo(business_id)
    # print(account)
    if account == None:
      app.logger.debug("Business account not found")
      raise ValueError("Business account not found")
    notification_settings = account.get('notification_settings')
  if notification_settings == None:
    app.logger.debug("Notification settings not found")
    raise ValueError("Notification settings not found")
  providerInfo = notification_settings.get('provider')
  # print('providerInfo:', providerInfo)
  gateway = provider(providerInfo.get('name'))(providerInfo)
  # print('getGateway', gateway, account)
  return gateway, account


@app.route('/send')
def send_message():
  print('send_message: ', request.args)
  app.logger.info(f'IN: {request.args}')
  phone = request.args.get('phone')
  if phone == None:
    app.logger.debug("No phone")
    return json.dumps({'error': 'No phone'}) 
  text = request.args.get('text')
  if text == None:
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
  print('gateway, account:', gateway, account)
  transaction_id = db.db_log(account.get('business_id'), request.args)['id']
  print('Transaction: ',transaction_id)
  if transaction_id == None:
    raise ValueError("Transaction was not opened")
  res = gateway.send(phone, text, time)
  app.logger.debug(f"Response: {res}")
  db.db_log_update(transaction_id, {'response': res})
  try:
    return json.dumps({'response': res, 'transaction': transaction_id})
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
