from requests import get, post, delete
from dotenv import load_dotenv
import os

load_dotenv()
BILLING_API_URL = os.getenv("BILLING_API_URL")

if BILLING_API_URL is None:
    raise ValueError("BILLING_API_URL is not defined")

def postTransaction(operation, params):
    url = f"{BILLING_API_URL}/transaction"
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
    url = f"{BILLING_API_URL}/waiting"
    req = get(url)
    res = None
    if not req is None:
        res = req.json()
    return res

def undoTransaction(transactionId, params=None):
    url = f"{BILLING_API_URL}/transaction/{transactionId}"
    req = delete(url)
    res = req.json()
    return res