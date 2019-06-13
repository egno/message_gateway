from singleton import Singleton
from requests import get, post
import json

class Gateway(object):

    _apiGateway = 'https://new.smsgorod.ru/apiSms/'

    def __init__(self, account):
        self.key = account.get('key','')
        self.sender = account.get('sender','UNO.salon')

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
        response=res.json()
        status=response.get('status','error') != 'error'
        return {'success': status, 'response': response}

    def status(self, ID):
        pass
        
    def balance(self):
        pass


        


