import sys
import time
import datetime as dt
import numpy as np
import logging
import random
import json
from orderBook import OrderBook
from publicClient import PublicClient
from websocketClient import WebsocketClient
from authClient import AuthenticatedClient
from exioAuth import getAuthHeaders

BOOK_MSG_TYPES = set(["bookOrders", "add", "remove", "trade"])
ORDER_MSG_TYPES = set(["openOrders", "accepted", "rejected", "canceled", "executed"])
MISC_MSG_TYPES = set(["heartbeat"])
ALL_MSG_TYPES = BOOK_MSG_TYPES | ORDER_MSG_TYPES | MISC_MSG_TYPES

def setupLogger(loggerName, logFile, level=logging.DEBUG):
  logger = logging.getLogger(loggerName)
  formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)d - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

  fileHandler = logging.FileHandler(logFile, mode='a')
  fileHandler.setFormatter(formatter)

  consoleHandler = logging.StreamHandler()
  consoleHandler.setFormatter(formatter)

  logger.setLevel(level)
  logger.addHandler(fileHandler)
  logger.addHandler(consoleHandler)

  return logger


class SimpleClient(WebsocketClient):
  def __init__(self, key="qWivyDdti2mDkYQb0O/3+E8k6SyViHqzsfzIPsBKZXU=", 
          secret="RaBgGrKCkAk2NOeIC6lmZ3drz9W5b9B2MzD4QqAxHtBahB+v31SLmm/+q461EAcpQMb3nn8MbLcu5dDVHF7JdKVw2zI+BO93UpHSnrHUTjqY3afqynM+VQ==", 
          symbol='btc-usdt', 
          logFile=None):
    super(SimpleClient, self).__init__(symbols=symbol, 
      auth=True,
      key=key,
      secret=secret,
      channels=[{"name": "books", "symbols": [symbol]}, {"name": "orders", "symbols": [symbol]}])
      # channels=[{"name": "books", "symbols": [symbol]}])

    self.symbol = symbol
    self.router = AuthenticatedClient(key, secret)
    self.publicClient = PublicClient()

    self.tickSize, self.size = self.publicClient.getTickSize(self.symbol)

    # self.orderBookDict = {}
    # <symbol index, OrderBook>
    # self.orderBookDict[0] = OrderBook(symbol=symbol)
    self.orderBook = OrderBook(symbol, self.tickSize)

    if logFile is None:
      self.logFile = "../log/bot_%s.log" % (dt.datetime.today().strftime("%Y%m%d"))
    else:
      self.logFile = logFile
    self.logger = setupLogger(self.__class__.__name__, self.logFile)
    self.logger.info("===LOG START===\nsymbol=%s tickSize=%s size=%s" % (self.symbol, self.tickSize, self.size))

    # config params  
    self.descriptions = ["noop", "cross1Tick", "cross2Ticks"]   
    # must sum to one
    self.weights = np.array([
      0.3,  # noop
      0.4, # cross1Tick
      0.3 # cross2Ticks
      ])

    random.seed(100)

  def randChoice(self, weights):
    """weights must sum to 1"""
    assert np.sum(weights) == 1, np.sum(weights)

    cs = np.cumsum(weights)
    idx = sum(cs < random.random())

    return idx

  def onOpen(self):
    self._sequence = -1
    print("-- SimpleClient Started! --\n")

  def onClose(self):
    print("\n-- SimpleClient Closed! --")


  def onUpdate(self, message):

    print json.dumps(message, indent=2)

    if message["type"] in BOOK_MSG_TYPES:
      self.orderBook.onUpdate(message)

      if not self.orderBook.isReady:
        return

      # calc fair price to cross
      bid = self.orderBook.getBid()
      bids = self.orderBook.getBids(bid)
      bidSize = float(sum([b['size'] for b in bids]))
      ask = self.orderBook.getAsk()
      asks = self.orderBook.getAsks(ask)
      askSize = float(sum([a['size'] for a in asks]))
      bid = float(bid)
      ask = float(ask)

      if np.isclose(self.orderBook.bidPxPre, bid) and np.isclose(self.orderBook.askPxPre, ask) and self.orderBook.bidSizePre == bidSize and self.orderBook.askSizePre == askSize:
        return 

      # get action idx
      idx = self.randChoice(self.weights)

      if idx == 0:
        pass
      elif idx == 1:
        self.logger.info(self.orderBook.printBook())

        if bidSize > askSize:
          side = "buy"
          size = min(self.size, askSize)
          px = ask

          order = self.router.buyIOC(self.symbol, px, size)

        else:
          side = "sell"
          size = min(self.size, bidSize)
          px = bid

          order = self.router.sellIOC(self.symbol, px, size)

        self.logger.info("taker %s side=%s px=%s size=%s . order=%s" % (self.descriptions[idx], side, px, size, order))

      elif idx == 2:
        self.logger.info(self.orderBook.printBook())

        ask2 = self.orderBook._asks.succ_key(self.getAsk())
        bid2 = self.orderBook._bids.prev_key(self.getBid())
        bids2 = self.getBids(bid2)
        asks2 = self.getAsks(ask2)
        bidSize2 = float(sum([b['size'] for b in bids2]))
        askSize2 = float(sum([a['size'] for a in asks2]))
        ask2 = float(ask2)
        bid2 = float(bid2)

        if bidSize > askSize:
          side = "buy"
          size = askSize + min(self.size, askSize2)
          px = ask2

          order = self.router.buyIOC(self.symbol, px, size)
        else:
          side = "sell"
          size = bidSize + min(self.size, bidSize2)
          px = bid2

          order = self.router.sellIOC(self.symbol, px, size)

        self.logger.info("taker %s side=%s px=%s size=%s . order=%s" % (self.descriptions[idx], side, px, size, order))


      self.orderBook.bidPxPre = bid
      self.orderBook.askPxPre = ask
      self.orderBook.bidSizePre = bidSize
      self.orderBook.askSizePre = askSize

    elif message["type"] in ORDER_MSG_TYPES:
      # print json.dumps(message, indent=2)
      pass

    elif message["type"] in MISC_MSG_TYPES:
      # print json.dumps(message, indent=2)
      pass

    else:
      raise Exception("Error! Unknown message type. %s" % (json.dumps(message, indent=2)))      



if __name__ == '__main__':
    
  client = SimpleClient(symbol="btc-usdt")
  client.start()
  try:
    while True:
      time.sleep(10)
  except KeyboardInterrupt:
    client.close()

  if client.error:
    sys.exit(1)
  else:
    sys.exit(0)
