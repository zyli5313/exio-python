import sys
import re
import os
import pandas as pd
import numpy as np
import gzip
import time
import json
from optparse import OptionParser
from datetime import date, timedelta
from exio.authClient import AuthenticatedClient
from exio.websocketClient import WebsocketClient

class Client(object):
  def __init__(self, key, secret, passphrase, restApi, websocketApi):
    self.key = key
    self.secret = secret
    self.passphrase = passphrase
    self.restApi = restApi
    self.websocketApi = websocketApi

    self.authClient = AuthenticatedClient(key, secret, passphrase)

  def subscribe(self, channels, symbols):
    wsClient = WebsocketClient( 
          key=self.key, 
          secret=self.secret, 
          passphrase=self.passphrase,
          symbols=symbols,
          channels=channels
          )
    wsClient.start()
    print(wsClient.url, wsClient.symbols)
    try:
      while True:
        print("\nmsgNumber =", "%i \n" % wsClient.message_count)
        time.sleep(1)
    except KeyboardInterrupt:
      wsClient.close()

  def insertOrder(self, symbol, side, price, size):
    if side == "buy":
      order = self.authClient.buyGTC(symbol, price, size)
    else:
      order = self.authClient.sellGTC(symbol, price, size)

    return order

  def cancelAll(self, symbol):
    return self.authClient.cancelAll(symbol)

  def getFunds(self):
    return self.authClient.getFunds()

  def getOpenOrders(self, symbol):
    return self.authClient.getOpenOrders(symbol)

  def cli(self, command, symbol, args):
    if command == "subscribe":
      channels=[{"name": "books", "symbols": [symbol]}]
      if self.key != "":
        channels = channels.append({"name": "orders", "symbols": [symbol]})
      
      self.subscribe(channels, symbol)

    elif command == "insert":
      side, price, size = args[0], args[1], args[2]

      order = self.insertOrder(symbol, side, price, size)

      print json.dumps(order, indent=2)

    elif command == "cancel":
      result = self.cancelAll(symbol)

      print json.dumps(result, indent=2)

    elif command == "open":
      orders = self.getOpenOrders(symbol)

      print json.dumps(orders, indent=2)

    elif command == "funds":
      funds = self.getFunds()

      print json.dumps(funds, indent=2)

    else:
      raise Exception("unknown command=%s" % (command))


if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-c", "--command", dest="command", help="subscribe|insert|cancel|open|funds", metavar="CMD")
  parser.add_option("-s", "--symbol", dest="symbol", help="symbol", metavar="SYMBOL")
  parser.add_option("--restApi", dest="restApi", help="restApi", metavar="REST_API", default="https://api.sandbox.ex.io/v1")
  parser.add_option("--websocketApi", dest="websocketApi", help="websocketApi", metavar="WEBSOCKET_API", default="wss://feed.sandbox.ex.io")
  parser.add_option("--apiKey", dest="apiKey", help="apiKey", metavar="API_KEY", default="lz8pGP0YajvUUpPyDM/X6N9fCx6RP48N78HLaWJLMQs=")
  parser.add_option("--apiSecret", dest="apiSecret", help="apiSecret", metavar="API_SECRET", default="O+LMRRKXDcvX2KrmxCPnVVNoZj8rRiZc9MLSlebiOIjioM9heVTRQ5j79883rS7VvMxP/XlT0650koeJx1NCSJOp0Gc79+25OjBEcTviFc/EBbYlFqdXyw==")
  parser.add_option("--apiPassphrase", dest="apiPassphrase", help="apiPassphrase", metavar="API_PASSPHRASE", default="lizeyuan")
  
  (options, args) = parser.parse_args()

  client = Client(options.apiKey, options.apiSecret, options.apiPassphrase, options.restApi, options.websocketApi)
  client.cli(options.command, options.symbol, args)
