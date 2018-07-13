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

  def __init__(self, key, secret, apiUrl="https://api.sandbox.ex.io/v1", timeout=30):
    super(AuthenticatedClient, self).__init__(apiUrl=apiUrl)
    self.auth = ExioAuth(key, secret)
    self.timeout = timeout

  def get_account(self, account_id):
    r = requests.get(self.url + '/accounts/' + account_id,
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_accounts(self):
    return self.get_account('')

  def get_account_history(self, account_id):
    result = []
    r = requests.get(self.url + '/accounts/{}/ledger'.format(account_id),
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    result.append(r.json())
    if "cb-after" in r.headers:
      self.history_pagination(account_id, result, r.headers["cb-after"])
    return result

  def history_pagination(self, account_id, result, after):
    r = requests.get(self.url + '/accounts/{}/ledger?after={}'.format(
        account_id, str(after)), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    if r.json():
      result.append(r.json())
    if "cb-after" in r.headers:
      self.history_pagination(account_id, result, r.headers["cb-after"])
    return result

  def get_account_holds(self, account_id):
    result = []
    r = requests.get(self.url + '/accounts/{}/holds'.format(account_id),
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    result.append(r.json())
    if "cb-after" in r.headers:
      self.holds_pagination(account_id, result, r.headers["cb-after"])
    return result

  def holds_pagination(self, account_id, result, after):
    r = requests.get(self.url + '/accounts/{}/holds?after={}'.format(
        account_id, str(after)), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    if r.json():
      result.append(r.json())
    if "cb-after" in r.headers:
      self.holds_pagination(account_id, result, r.headers["cb-after"])
    return result

  def buy(self, **kwargs):
    kwargs["side"] = "buy"
    r = requests.post(self.url + '/orders',
                      data=json.dumps(kwargs),
                      auth=self.auth,
                      timeout=self.timeout)
    return r.json()

  def sell(self, **kwargs):
    kwargs["side"] = "sell"
    r = requests.post(self.url + '/orders',
                      data=json.dumps(kwargs),
                      auth=self.auth,
                      timeout=self.timeout)
    return r.json()

  def buyIOC(self, symbol, px, size):
    order = {"symbol":  symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "ioc",
             "flags":        1
             }
    return self.buy(order)

  def sellIOC(self, symbol, px, size):
    order = {"symbol":  symbol,
             "token":        "1234",
             "orderType":    "limit",
             "size":         str(size),
             "price":        str(px),
             "tif":          "ioc",
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

  def get_fundings(self, result='', status='', after=''):
    if not result:
      result = []
    url = self.url + '/funding?'
    if status:
      url += "status={}&".format(str(status))
    if after:
      url += 'after={}&'.format(str(after))
    r = requests.get(url, auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    result.append(r.json())
    if 'cb-after' in r.headers:
      return self.get_fundings(result, status=status, after=r.headers['cb-after'])
    return result

  def repay_funding(self, amount='', currency=''):
    payload = {
        "amount": amount,
        "currency": currency  # example: USD
    }
    r = requests.post(self.url + "/funding/repay",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def margin_transfer(self, margin_profile_id="", transfer_type="", currency="", amount=""):
    payload = {
        "margin_profile_id": margin_profile_id,
        "type": transfer_type,
        "currency": currency,  # example: USD
        "amount": amount
    }
    r = requests.post(self.url + "/profiles/margin-transfer",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_position(self):
    r = requests.get(self.url + "/position",
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def close_position(self, repay_only=""):
    payload = {
        "repay_only": repay_only or False
    }
    r = requests.post(self.url + "/position/close",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def deposit(self, amount="", currency="", payment_method_id=""):
    payload = {
        "amount": amount,
        "currency": currency,
        "payment_method_id": payment_method_id
    }
    r = requests.post(self.url + "/deposits/payment-method",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def coinbase_deposit(self, amount="", currency="", coinbase_account_id=""):
    payload = {
        "amount": amount,
        "currency": currency,
        "coinbase_account_id": coinbase_account_id
    }
    r = requests.post(self.url + "/deposits/coinbase-account",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def withdraw(self, amount="", currency="", payment_method_id=""):
    payload = {
        "amount": amount,
        "currency": currency,
        "payment_method_id": payment_method_id
    }
    r = requests.post(self.url + "/withdrawals/payment-method",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def coinbase_withdraw(self, amount="", currency="", coinbase_account_id=""):
    payload = {
        "amount": amount,
        "currency": currency,
        "coinbase_account_id": coinbase_account_id
    }
    r = requests.post(self.url + "/withdrawals/coinbase-account",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def crypto_withdraw(self, amount="", currency="", crypto_address=""):
    payload = {
        "amount": amount,
        "currency": currency,
        "crypto_address": crypto_address
    }
    r = requests.post(self.url + "/withdrawals/crypto",
                      data=json.dumps(payload), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_payment_methods(self):
    r = requests.get(self.url + "/payment-methods",
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_coinbase_accounts(self):
    r = requests.get(self.url + "/coinbase-accounts",
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def create_report(self, report_type="", start_date="", end_date="", symbol="", account_id="", report_format="",
                    email=""):
    payload = {
        "type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "symbol": symbol,
        "account_id": account_id,
        "format": report_format,
        "email": email
    }
    r = requests.post(self.url + "/reports", data=json.dumps(payload),
                      auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_report(self, report_id=""):
    r = requests.get(self.url + "/reports/" + report_id,
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_trailing_volume(self):
    r = requests.get(self.url + "/users/self/trailing-volume",
                     auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def get_deposit_address(self, account_id):
    r = requests.post(self.url + '/coinbase-accounts/{}/addresses'.format(
        account_id), auth=self.auth, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()
