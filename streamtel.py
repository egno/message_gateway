from singleton import Singleton
from requests import get

class Gateway(object):

    _apiGateway = 'https://gateway.api.sc/get/'

    def __init__(self, account):
        self.login = account.get('login','')
        self.password = account.get('password','')
        self.sender = account.get('sender','SMS Info')

    def params(self):
        return {'user': self.login, 'pwd': self.password, 'sadr': self.sender}

    def send(self, destination, text):
        params = self.params()
        params.update({'dadr': destination, 'text': text})
        res = get(self._apiGateway, params=params)
        print(res, res.url, res.text)
        return res.text

    def status(self, ID):
        params = self.params()
        params.update({'smsid': ID})
        res = get(self._apiGateway, params=params)
        print(res, res.url, res.text)
        return res.text
        
    def balance(self):
        params = self.params()
        params.update({'balance': 1})
        res = get(self._apiGateway, params=params)
        print(res, res.url, res.text)
        return res.text



        


