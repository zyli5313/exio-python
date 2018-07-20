#
# Live order book updated from the exio Websocket Feed

import json
from sortedcontainers import SortedDict
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
    self.oidToOrderDict = {}
    self.oidToPxDict = {} # internal px, not real px

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
    print 'Error: messages missing ({} - {}). Re-initializing  book at sequence.'.format(
        gap_start, gap_end, self.sequence)

    exit(-1)

  def add(self, order):
    order = {
        'oid': str(order['oid']),
        'side': str(order['side']),
        "price": int(float(order["price"]) * self.multiplier),
        "size": float(order["size"])
    }

    node = dllistnode(order)
    self.oidToPxDict[order["oid"]] = order["price"]

    if order['side'] == 'buy':
      bids = self.getBids(order['price'])
      
      if bids is None:
        bids = dllist([order])
      else:
        bids.append(node)

      node = bids.last
      self.oidToOrderDict[order["oid"]] = node

      self.setBids(order['price'], bids)

      assert node == bids.nodeat(len(bids)-1), "bids={} node={}".format(bids, node)
    else:
      asks = self.getAsks(order['price'])
      
      if asks is None:
        asks = dllist([order])
      else:
        asks.append(node)

      node = asks.last
      self.oidToOrderDict[order["oid"]] = node

      self.setAsks(order['price'], asks)

      assert node == asks.nodeat(len(asks)-1), "asks={} node={}".format(asks, node)

    if len(self.bids) > 0 and len(self.asks) > 0:
      self.isReady = True

  def remove(self, order):
    oid = str(order["oid"])

    if oid in self.oidToOrderDict:
      node = self.oidToOrderDict[oid]
      price = self.oidToPxDict[oid]

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
    
      del self.oidToOrderDict[oid]
      del self.oidToPxDict[oid]
    

  def trade(self, order):
    price = int(float(order["price"]) * self.multiplier)
    size = float(order["size"])
    oid = str(order["oid"])

    node = self.oidToOrderDict[oid]

    if order['side'] == 'buy':
      bids = self.getBids(price)
      if not bids:
        return
      assert bids[0]['id'] == str(order['oid'])

      if bids[0]['size'] == size:
        self.setBids(price, bids[1:])

        del self.oidToOrderDict[oid]
        del self.oidToPxDict[oid]
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

        del self.oidToOrderDict[oid]
        del self.oidToPxDict[oid]
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
    for px, orders in self.asks.items()[:numLevels]:
      # print "type(nodes)={} type(nodes[0])={} nodes[0].value={}".format(type(nodes), type(nodes[0]), nodes[0].value)
      size = sum([order['size'] for order in orders])
      strs = "%.06f@%.2f\n" % (size, px) + strs

    strs += "---\n"
    for px, orders in self.bids.items()[::-1][:numLevels]:
      # print "type(nodes)={} type(nodes[0])={} nodes[0].value={}".format(type(nodes), type(nodes[0]), nodes[0].value)
      size = sum([order['size'] for order in orders])
      strs += "%.06f@%.2f\n" % (size, px)

    strs += "===\n"

    return strs

  def getBBO(self):
    ask = self.asks.peekitem(0)[0]
    asks = self.asks.get(ask)
    askSize = sum([float(order['size']) for order in asks])

    bid = self.bids.peekitem(-1)[0]
    bids = self.bids.get(bid)
    bidSize = sum([float(order['size']) for order in bids])

    return bid * 1.0 / self.multiplier, ask * 1.0 / self.multiplier, bidSize, askSize

  def getAsk(self):
    if len(self.asks) == 0:
      return None
    else:
      return self.asks.peekitem(0)[0] * 1.0 / self.multiplier

  def getAsks(self, price):
    return self.asks.get(price)

  def removeAsks(self, price):
    del self.asks[price]

  def setAsks(self, price, asks):
    self.asks[price] = asks

  def getBid(self):
    if len(self.bids) == 0:
      return None
    else:
      return self.bids.peekitem(-1)[0] * 1.0 / self.multiplier

  def getBids(self, price):
    return self.bids.get(price)

  def removeBids(self, price):
    del self.bids[price]

  def setBids(self, price, bids):
    self.bids[price] = bids
