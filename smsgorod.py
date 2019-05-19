from singleton import Singleton
from requests import get, post
import json

class Gateweay(object):

    _apiGateway = 'https://new.smsgorod.ru/apiSms/'

    def __init__(self, account):
        self.key = account.get('key','')
        self.sender = account.get('sender','VIRTA')

    def params(self):
        return {'apiKey': self.key}

    def send(self, destination, text, time = None):
        params = self.params()
        sms = {
                    "channel": "char",
                    "phone": destination,
                    "text": text,
                    "sender": self.sender
                }
        if time != None and time != '':
            sms.update({"plannedAt": time})
        params.update({'sms': 
            [
                sms
            ]
        })

        print('Params: ', params)
        headers = {
            'Content-type': 'application/json', 
            'accept': 'application/json'
        }
        res = post(self._apiGateway + 'create', json=params, headers=headers)
        print('POST: ', res, res.status_code)
        print(res.url, res.text)
        return res.json()

    def status(self, ID):
        pass
        
    def balance(self):
        pass


        


