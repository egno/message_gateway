from singleton import Singleton
from requests import get, post
import json


class Gateway(object):

    _apiGateway = 'https://new.smsgorod.ru/apiSms/'

    def __init__(self, account):
        self.key = account.get('key', '')
        self.sender = account.get('sender', 'UNO.salon')

    def params(self):
        return {'apiKey': self.key}

    def send(self, destination, text, time=None):
        if self.key is None or self.key == '':
            return {'success': False, 'details': 'No API key'}

        params = self.params()
        sms = {
            "channel": "char",
            "phone": destination,
            "text": text,
            "sender": self.sender
        }
        if time is not None and time != '':
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
        response = res.json()
        status = response.get('status', 'error') != 'error' and response.get(
            'status', 'error') != 'channel'
        return {'success': status, 'response': response}

    def status(self, IDs):
        if self.key is None or self.key == '':
            return {'success': False, 'details': 'No API key'}
        params = self.params()
        params['apiSmsIdList'] = IDs
        headers = {
            'Content-type': 'application/json',
            'accept': 'application/json'
        }
        res = post(self._apiGateway + 'get', json=params, headers=headers)
        return res.json()

    def messageList(self):
        if self.key is None or self.key == '':
            return {'success': False, 'details': 'No API key'}
        params = self.params()
        headers = {
            'Content-type': 'application/json',
            'accept': 'application/json'
        }
        res = get(self._apiGateway + 'getSmsList',
                  params=params, headers=headers)
        return res.json()

    def balance(self):
        pass

    def Parts(self, response):
        #  {"success": true, "response": {"data": [
        #       {"id": 340142999, "cost": 0, "phone": "79537680916",
        #           "sender": "UNO.salon", "source": "api",
        #           "status": "sent", "channel": "char",
        #           "message": "Новая онлайн запись к Сотрудник сотрудникович
        #                   на 09.08 11:00 в Тестовый Филиал компании",
        #           "smsCount": 2, "createdAt": 1565319610,
        #           "updatedAt": 1565319610
        #       }
        # ], "status": "success"}}

        try:
            return float(response.get('response', {}).get('data', [])[0].get('smsCount', None))
        except:
            return None
