import hmac
import hashlib
import time
import requests
import base64
import json
from requests.auth import AuthBase
from publicClient import PublicClient
from exioAuth import ExioAuth


class AuthenticatedClient(PublicClient):

  def __init__(self, key, secret, passphrase, apiUrl="https://api.sandbox.ex.io/v1", timeout=30):
    super(AuthenticatedClient, self).__init__(apiUrl=apiUrl)
    self.auth = ExioAuth(key, secret, passphrase)
    self.timeout = timeout

  """
  Trading related
  """

  def buy(self, order):
    order["side"] = "buy"
    r = requests.post(self.url + '/orders',
                      data=json.dumps(order),
                      auth=self.auth,
                      timeout=self.timeout)
    return r.json()

  def sell(self, order):
    order["side"] = "sell"
    r = requests.post(self.url + '/orders',
                      data=json.dumps(order),
                      auth=self.auth,
                      timeout=self.timeout)
    return r.json()

  def buyIOC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "ioc",
             "flags":        0
             }
    return self.buy(order)

  def sellIOC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "ioc",
             "flags":        0
             }
    return self.sell(order)

  def buyGTC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "gtc",
             "flags":        0
             }
    return self.buy(order)

  def sellGTC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "gtc",
             "flags":        0
             }
    return self.sell(order)

  def cancelOrder(self, symbol, oid):
    payload = {
        "symbol": symbol,
        "oid": oid
    }
    r = requests.delete(self.url + '/orders', data=json.dumps(payload),
                        auth=self.auth, timeout=self.timeout)
    return r.json()

  def cancelAll(self, symbol):
    return self.cancelOrder(symbol, 0)

  def getOpenOrders(self, symbol):
    payload = {"symbol": symbol}

    r = requests.get(self.url + '/orders', params=payload,
                     auth=self.auth, timeout=self.timeout)
    
    return r.json()

  def getTradeHistory(self, symbol, begin, end):
    # begin: datetime in ISO 8601 format
    payload = {
        "symbol":   symbol,
        "begin":    str(begin),
        "end":      str(end)
    }
    r = requests.get(self.url + '/trade_history', params=payload,
                     auth=self.auth, timeout=self.timeout)
    return r.json()

  """
  Funding related
  """

  def createDepositAddress(self, currency):
    payload = {
        "currency": currency  # btc
    }
    r = requests.post(self.url + "/deposit",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    return r.json()

  def getDepositAddress(self, currency):
    payload = {
        "currency": currency  
    }
    r = requests.get(self.url + "/deposit", data=json.dumps(payload),
                      auth=self.auth, timeout=self.timeout)
    return r.json()

  def getFunds(self):
    r = requests.get(self.url + "/funds",
                     auth=self.auth, timeout=self.timeout)
    
    return r.json()

  def getPosition(self, currency):
    funds = self.getFunds()

    fund = [fund for fund in funds["funds"] if fund["currency"] == currency][0]

    return float(fund["position"])

  def createWithdrawalRequest(self, currency, amount, destination):
    # Withdraw request successfully submitted. Note, this does not mean that funds have actually moved. Rather, it means your withdraw request was submitted, and the actual withdrawal is now pending.
    payload = {
        "currency": currency,
        "amount": amount,
        "destination": destination
    }
    r = requests.post(self.url + "/withdraw",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    
    return r.json()

  def getWithdrawalHistory(self, currency, amount, destination):
    payload = {
        "currency": currency,
        "amount": amount,
        "destination": destination
    }
    r = requests.get(self.url + "/withdrawal_history", data=json.dumps(payload), 
                     auth=self.auth, timeout=self.timeout)
    
    return r.json()
