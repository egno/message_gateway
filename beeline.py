from singleton import Singleton
from requests import get, post
import json
import xmltodict

class Gateweay(object):

    _apiGateway = 'https://beeline.amega-inform.ru/sms_send/'

    def __init__(self, account):
        self.login = account.get('login','')
        self.password = account.get('password','')
        self.sender = account.get('sender','UNO.salon')
    

    def send(self, destination, text, time = None):
        data = {
                    'user': self.login, 
                    'pass': self.password,
                    "action": "post_sms",
                    "target": f'+{destination}',
                    "message": text,
                    "sender": self.sender
                }

        headers = {
            'Content-type': 'text/xml', 
            "charset": "UTF-8"
        }
        res = post(self._apiGateway, data=data, headers=headers)
        print('POST: ', res, res.status_code)
        print(res.url, res.text)
        return xmltodict.parse(res.content)

    def status(self, ID):
        data = {
                    'user': self.login, 
                    'pass': self.password,
                    "action": "status",
                    "sms_id": ID
                }

        headers = {
            'Content-type': 'text/xml', 
            "charset": "UTF-8"
        }
        res = post(self._apiGateway, data=data, headers=headers)
        print('POST: ', res, res.status_code)
        print(res.url, res.text)
        return xmltodict.parse(res.content)
        
    def balance(self):
        pass


        


