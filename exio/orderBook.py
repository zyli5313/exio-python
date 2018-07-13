#
# Live order book updated from the exio Websocket Feed

import json
from sortedcontainers import SortedDict
# from decimal import Decimal
from publicClient import PublicClient
from llist import dllist, dllistnode

def numDigits(tickSize):
  numDigit = 0
  while tickSize < 1 - 1e-6:
    tickSize *= 10
    numDigit += 1

  return numDigit

class OrderBook(object):

  def __init__(self, symbol, tickSize):
    self.symbol = symbol
    self.tickSize = tickSize
    self.asks = SortedDict()
    self.bids = SortedDict()
    self.client = PublicClient()
    self.sequence = -1

    self.isReady = False

    self.numDigit = numDigits(tickSize)
    self.multiplier = 10 ** self.numDigit

    # latest values of bid-ask spread
    self.bidPxPre = 0.0
    self.askPxPre = 0.0
    self.bidSizePre = 0
    self.askSizePre = 0

    # <oid, node>
    self.seqToOrderDict = {}
    self.seqToPxDict = {} # internal px, not real px

  # def reset_book(self):
  #     self.asks = SortedDict()
  #     self.bids = SortedDict()
  #     res = self.client.get_product_order_book(symbol=self.symbol, level=3)
  #     for bid in res['bids']:
  #         self.add({
  #             'id': bid[2],
  #             'side': 'buy',
  #             'price': Decimal(bid[0]),
  #             'size': Decimal(bid[1])
  #         })
  #     for ask in res['asks']:
  #         self.add({
  #             'id': ask[2],
  #             'side': 'sell',
  #             'price': Decimal(ask[0]),
  #             'size': Decimal(ask[1])
  #         })
  #     self.sequence = res['sequence']

  def onUpdate(self, message):

    if message["type"] == "bookOrders":
      for order in message["orders"]:
        self.add(order)

      self.sequence = 0
      print self.printBook()
      return

    sequence = int(message['sequence'])
    # if self.sequence == -1:
    #     self.reset_book()
    #     return
    if sequence <= self.sequence:
      # ignore older messages (e.g. before order book initialization from
      # getProductOrderBook)
      return
    elif self.sequence != 0 and sequence > self.sequence + 1:
      self.onSequenceGap(self.sequence, sequence)
      # return

    msgType = message['type']
    if msgType == 'add':
      self.add(message)
    elif msgType == 'remove':
      self.remove(message)
    elif msgType == 'trade':
      self.trade(message)
    # elif msgType == 'change':
    #     self.change(message)

    self.sequence = sequence

  def onSequenceGap(self, gap_start, gap_end):
    # self.reset_book()
    print('Error: messages missing ({} - {}). Re-initializing  book at sequence.'.format(
        gap_start, gap_end, self.sequence))

    exit(-1)

  def add(self, order):
    order = {
        'oid': str(order['oid']),
        "sequence": int(order["sequence"]),
        'side': str(order['side']),
        # 'price': Decimal(order['price']),
        # 'size': Decimal(order.get('size'))
        "price": int(float(order["price"]) * self.multiplier),
        "size": float(order["size"])
    }

    node = dllistnode(order)
    self.seqToOrderDict[order["sequence"]] = node
    self.seqToPxDict[order["sequence"]] = order["price"]

    if order['side'] == 'buy':
      bids = self.getBids(order['price'])
      
      if bids is None:
        bids = dllist([node])
      else:
        bids.append(node)

      self.setBids(order['price'], bids)
    else:
      asks = self.getAsks(order['price'])
      
      if asks is None:
        asks = dllist([node])
      else:
        asks.append(node)
      self.setAsks(order['price'], asks)

    if len(self.bids) > 0 and len(self.asks) > 0:
      self.isReady = True

  def remove(self, order):
    sequence = int(order["sequence"])

    if sequence in self.seqToOrderDict:
      node = self.seqToOrderDict[sequence]
      price = self.seqToPxDict[sequence]

      if order['side'] == 'buy':
        bids = self.getBids(price)
        if bids is not None:
          bids.remove(node)

          if len(bids) > 0:
            self.setBids(price, bids)
          else:
            self.removeBids(price)
      else:
        asks = self.getAsks(price)
        if asks is not None:
          asks.remove(node)
          if len(asks) > 0:
            self.setAsks(price, asks)
          else:
            self.removeAsks(price)

      if len(self.bids) == 0 or len(self.asks) == 0:
        self.isReady = False
    
      del self.seqToOrderDict[sequence]
      del self.seqToPxDict[sequence]
    else:
      raise Exception(order)

  def trade(self, order):
    price = int(float(order["price"]) * self.multiplier)
    size = float(order["size"])
    sequence = int(order["sequence"])

    node = self.seqToOrderDict[sequence]

    if order['side'] == 'buy':
      bids = self.getBids(price)
      if not bids:
        return
      assert bids[0]['id'] == str(order['oid'])

      if bids[0]['size'] == size:
        self.setBids(price, bids[1:])

        del self.seqToOrderDict[sequence]
        del self.seqToPxDict[sequence]
      else:
        bids[0]['size'] -= size
        self.setBids(price, bids)
    else:
      asks = self.getAsks(price)
      if not asks:
        return
      assert asks[0]['id'] == str(order['oid'])

      if asks[0]['size'] == size:
        self.setAsks(price, asks[1:])

        del self.seqToOrderDict[sequence]
        del self.seqToPxDict[sequence]
      else:
        asks[0]['size'] -= size
        self.setAsks(price, asks)

    if len(self.bids) == 0 or len(self.asks) == 0:
      self.isReady = False

  # def change(self, order):
  #     try:
  #         new_size = Decimal(order['new_size'])
  #     except KeyError:
  #         return

  #     try:
  #         price = Decimal(order['price'])
  #     except KeyError:
  #         return

  #     if order['side'] == 'buy':
  #         bids = self.getBids(price)
  #         if bids is None or not any(o['id'] == order['order_id'] for o in bids):
  #             return
  #         index = [b['id'] for b in bids].index(order['order_id'])
  #         bids[index]['size'] = new_size
  #         self.setBids(price, bids)
  #     else:
  #         asks = self.getAsks(price)
  #         if asks is None or not any(o['id'] == order['order_id'] for o in asks):
  #             return
  #         index = [a['id'] for a in asks].index(order['order_id'])
  #         asks[index]['size'] = new_size
  #         self.setAsks(price, asks)

  #     tree = self.asks if order['side'] == 'sell' else self.bids
  #     node = tree.get(price)

  #     if node is None or not any(o['id'] == order['order_id'] for o in node):
  #         return

  # def get_current_ticker(self):
  #     return self._current_ticker

  # def getCurrentBook(self):
  #   result = {
  #       'sequence': self.sequence,
  #       'asks': [],
  #       'bids': [],
  #   }
  #   for ask in self.asks:
  #     try:
  #       # There can be a race condition here, where a price point is removed
  #       # between these two ops
  #       this_ask = self.asks[ask]
  #     except KeyError:
  #       continue
  #     for order in this_ask:
  #       result['asks'].append([order['price'], order['size'], order['id']])
  #   for bid in self.bids:
  #     try:
  #       # There can be a race condition here, where a price point is removed
  #       # between these two ops
  #       this_bid = self.bids[bid]
  #     except KeyError:
  #       continue

  #     for order in this_bid:
  #       result['bids'].append([order['price'], order['size'], order['id']])
  #   return result

  def printBook(self, numLevels=5):
    strs = ""
    for px, sizes in self.asks.items()[:numLevels]:
      size = sum([s['size'] for s in sizes])
      strs = "%.06f@%.2f\n" % (size, px) + strs

    strs += "---\n"
    for px, sizes in self.bids.items()[::-1][:numLevels]:
      size = sum([s['size'] for s in sizes])
      strs += "%.06f@%.2f\n" % (size, px)

    strs += "===\n"

    return strs

  def getAsk(self):
    return self.asks.peekitem(0)[0] * 1.0 / self.multiplier

  def getAsks(self, priceIn):
    price = int(float(priceIn) *  self.multiplier)
    return self.asks.get(price)

  def removeAsks(self, priceIn):
    price = int(float(priceIn) *  self.multiplier)
    del self.asks[price]

  def setAsks(self, priceIn, asks):
    price = int(float(priceIn) *  self.multiplier)
    self.asks[price] = asks

  def getBid(self):
    return self.bids.peekitem(-1)[0] * 1.0 / self.multiplier

  def getBids(self, priceIn):
    price = int(float(priceIn) *  self.multiplier)
    return self.bids.get(price)

  def removeBids(self, priceIn):
    price = int(float(priceIn) *  self.multiplier)
    del self.bids[price]

  def setBids(self, priceIn, bids):
    price = int(float(priceIn) *  self.multiplier)
    self.bids[price] = bids
