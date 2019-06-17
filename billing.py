from requests import get, post
from config import CONFIG as config

BILLING_GONFIG = config['BILLING']


def postTransaction(operation, params):
    url = f"{BILLING_GONFIG.get('URL','/')}transaction"
    data = params
    data['type'] = operation
    req = post(url, json=data)
    res = req.json()
    return res

def SMSReserveSum(business, amount, params=None):
    data = params or {}
    data['amount'] = amount 
    data['business'] = business
    res = postTransaction('SMSReserveSum', data)
    id = res.get('transaction',{}).get('id')
    return id, res


def SMSDelivered(business, amount, transactionId=None, params=None):
    data = params or {}
    data['amount'] = amount 
    data['business'] = business
    if not transactionId is None:
        data['reservedId'] = transactionId
    res = postTransaction('SMSDelivered', data)
    id = res.get('transaction',{}).get('id')
    return id, res

def getWaitingTransactions():
    url = f"{BILLING_GONFIG.get('URL','/')}waiting"
    req = get(url)
    res = req.json()
    return res