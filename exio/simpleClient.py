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

def setupLogger(loggerName, logFile, level=logging.DEBUG):
  logger = logging.getLogger(loggerName)
  formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)d - %(levelname)s - %(msg)s', datefmt='%Y-%m-%d %H:%M:%S')

  fileHandler = logging.FileHandler(logFile, mode='a')
  fileHandler.setFormatter(formatter)

  consoleHandler = logging.StreamHandler()
  consoleHandler.setFormatter(formatter)

  logger.setLevel(level)
  logger.addHandler(fileHandler)
  logger.addHandler(consoleHandler)

  return logger


class SimpleClient(WebsocketClient):
  def __init__(self, key="lz8pGP0YajvUUpPyDM/X6N9fCx6RP48N78HLaWJLMQs=",
          secret="O+LMRRKXDcvX2KrmxCPnVVNoZj8rRiZc9MLSlebiOIjioM9heVTRQ5j79883rS7VvMxP/XlT0650koeJx1NCSJOp0Gc79+25OjBEcTviFc/EBbYlFqdXyw==", 
          passphrase="lizeyuan",
          symbol='btc-usdt', 
          logFile=None):
    super(SimpleClient, self).__init__(symbols=symbol,
      key=key,
      secret=secret,
      passphrase=passphrase,
      channels=[{"name": "books", "symbols": [symbol]}, {"name": "orders", "symbols": [symbol]}])
      # channels=[{"name": "books", "symbols": [symbol]}])

    self.symbol = symbol
    self.router = AuthenticatedClient(key, secret, passphrase)
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
      0.4,  # noop
      0.6   # cross1Tick
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
    self.logger.info("-- SimpleClient Started! --\n")

  def onClose(self):
    self.stop = True

    self.logger.info("\n-- SimpleClient Closed! --")


  def onOrderUpdate(self, msg):
    print json.dumps(msg, indent=2)

    if msg["type"] == "accepted":
      pass
    elif msg["type"] == "canceled":
      pass
    elif msg["type"] == "executed":
      pass
    elif msg["type"] == "rejected":
      pass
    elif msg["type"] == "openOrders":
      pass
    else:
      raise Exception("Error! Unknown message type. %s" % (json.dumps(msg, indent=2)))


  def onBookUpdate(self, msg):

    print json.dumps(msg, indent=2)

    self.orderBook.onUpdate(msg)

    if not self.orderBook.isReady:
      return

    # calc fair price to cross
    bid, ask, bidSize, askSize = self.orderBook.getBBO()

    if np.isclose(self.orderBook.bidPxPre, bid) and np.isclose(self.orderBook.askPxPre, ask) and self.orderBook.bidSizePre == bidSize and self.orderBook.askSizePre == askSize:
      return 

    # get action idx
    idx = self.randChoice(self.weights)

    if idx == 0:
      pass
    elif idx == 1:
      self.logger.info("\n" + self.orderBook.printBook())

      isSell = self.randChoice(np.array([0.5, 0.5]))

      if not isSell:
        side = "buy"
        size = min(self.size, askSize)
        px = ask + 10

        order = self.router.buyIOC(self.symbol, px, size)

      else:
        side = "sell"
        size = min(self.size, bidSize)
        px = bid - 10

        order = self.router.sellIOC(self.symbol, px, size)

      self.logger.info("taker %s side=%s px=%s size=%s . order=%s" % (self.descriptions[idx], side, px, size, order))

    self.orderBook.bidPxPre = bid
    self.orderBook.askPxPre = ask
    self.orderBook.bidSizePre = bidSize
    self.orderBook.askSizePre = askSize



if __name__ == '__main__':
    
  client = SimpleClient(symbol="btc-usdt")
  client.start()
  try:
    while not client.stop:
      time.sleep(10)
  except KeyboardInterrupt:
    client.onClose()

  if client.error:
    sys.exit(1)
  else:
    sys.exit(0)
