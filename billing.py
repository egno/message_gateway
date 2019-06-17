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
    data = {
        'amount': amount, 
        'business': business
        }
    if not params is None:
        data['info'] = params
    res = postTransaction('SMSReserveSum', data)
    id = res.get('transaction',{}).get('id')
    return id, res