#
# For authenticated requests to the exio exchange

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
             "flags":        1
             }
    return self.buy(order)

  def sellIOC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "ioc",
             "flags":        1
             }
    return self.sell(order)

  def buyGTC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "gtc",
             "flags":        1
             }
    return self.buy(order)

  def sellGTC(self, symbol, px, size):
    order = {"symbol":       symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "gtc",
             "flags":        1
             }
    return self.sell(order)

  def cancelOrder(self, symbol, oid):
    payload = {
        "symbol": symbol,
        "oid": oid
    }
    r = requests.delete(self.url + '/orders/', data=payload,
                        auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def cancelAll(self, symbol):
    return self.cancelOrder(symbol, 0)

  def getOpenOrders(self, symbol):
    payload = {"symbol": symbol}
    r = requests.get(self.url + '/orders/', data=payload,
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def getTradeHistory(self, symbol, beginTime, endTime):
    # beginTime: timestamp
    payload = {
        "symbol":   symbol,
        "begin":    str(begin),
        "end":      str(end)
    }
    r = requests.get(self.url + '/trade_history',
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def createDepositAddress(self, currency):
    payload = {
        "currency": currency  # example: USD
    }
    r = requests.post(self.url + "/deposit",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def getDepositAddress(self, margin_profile_id="", transfer_type="", currency="", amount=""):
    payload = {
        "currency": currency  # example: USD
    }
    r = requests.get(self.url + "/deposit",
                      auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def getFunds(self):
    r = requests.get(self.url + "/funds",
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def createWithdrawalRequest(self, currency, amount, destination):
    # Withdraw request successfully submitted. Note, this does not mean that funds have actually moved. Rather, it means your withdraw request was submitted, and the actual withdrawal is now pending.
    payload = {
        "currency": currency,
        "amount": amount,
        "destination": destination
    }
    r = requests.post(self.url + "/deposits/payment-method",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def getWithdrawalHistory(self):
    r = requests.get(self.url + "/withdrawal_history",
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()
