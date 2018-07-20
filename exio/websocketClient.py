#
#
# Template object to receive messages from the exio Websocket Feed

# from __future__ import print_function
import json
import base64
import hmac
import hashlib
import time
from threading import Thread
from websocket import create_connection, WebSocketConnectionClosedException
from exioAuth import getAuthHeaders

BOOK_MSG_TYPES = set(["bookOrders", "add", "remove", "trade"])
ORDER_MSG_TYPES = set(["openOrders", "accepted", "rejected", "canceled", "executed"])
MISC_MSG_TYPES = set(["heartbeat"])
ALL_MSG_TYPES = BOOK_MSG_TYPES | ORDER_MSG_TYPES | MISC_MSG_TYPES

class WebsocketClient(object):

  def __init__(self, url="wss://feed.sandbox.ex.io", symbols=None, messageType="subscribe",
               shouldPrint=True, key="", secret="", passphrase="", channels=None):
    self.url = url
    self.symbols = symbols
    self.channels = channels
    self.type = messageType
    self.stop = False
    self.error = None
    self.ws = None
    self.thread = None
    self.key = key
    self.secret = secret
    self.passphrase = passphrase
    self.shouldPrint = shouldPrint

  def start(self):
    def _go():
      self._connect()
      self._listen()
      self._disconnect()

    self.stop = False
    self.onOpen()
    # self.thread = Thread(target=_go)
    # self.thread.start()
    _go()

  def _connect(self):
    if self.symbols is None:
      self.symbols = ["btc-usdt"]
    elif not isinstance(self.symbols, list):
      self.symbols = [self.symbols]

    if self.url[-1] == "/":
      self.url = self.url[:-1]

    if self.channels is None:
      sub_params = {'type': 'subscribe', 'channels': [
          {"name": "books", "symbols": self.symbols}]}
    else:
      sub_params = {'type': 'subscribe', 'channels': self.channels}

    if self.key != "":
      timestamp = str(int(time.time()))
      message = timestamp + 'GET' + '/user/self/verify'
      headers = getAuthHeaders(timestamp, message, self.key, self.secret, self.passphrase)
      sub_params.update(headers)

    self.ws = create_connection(self.url)

    # TODO debug
    print json.dumps(sub_params, indent=2)

    self.ws.send(json.dumps(sub_params))

  def _listen(self):
    while not self.stop:
      try:
        start_t = 0
        if time.time() - start_t >= 30:
          # Set a 30 second ping to keep connection alive
          self.ws.ping("keepalive")
          start_t = time.time()
        data = self.ws.recv()
        msg = json.loads(data)
      except ValueError as e:
        self.onError(e)
      except Exception as e:
        self.onError(e)
      else:
        self.onUpdate(msg)

  def _disconnect(self):
    try:
      if self.ws:
        self.ws.close()
    except WebSocketConnectionClosedException as e:
      pass

    self.onClose()

  def close(self):
    self.stop = True
    # self.thread.join()

  def onOpen(self):
    if self.shouldPrint:
      print("-- Subscribed! --\n")

  def onClose(self):
    if self.shouldPrint:
      print("\n-- Socket Closed --")

  def onBookUpdate(self, msg):
    if self.shouldPrint:
      print json.dumps(msg, indent=2)

  def onOrderUpdate(self, msg):
    print json.dumps(msg, indent=2)

  def onHeartbeat(self, msg):
    print json.dumps(msg, indent=2)

  def onUpdate(self, msg):
    if msg["type"] in BOOK_MSG_TYPES:
      self.onBookUpdate(msg)

    elif msg["type"] in ORDER_MSG_TYPES:
      self.onOrderUpdate(msg)

    elif msg["type"] in MISC_MSG_TYPES:
      self.onHeartbeat(msg)

    else:
      raise Exception("Error! Unknown message type. %s" % (json.dumps(msg, indent=2)))      


  def onError(self, e, data=None):
    self.error = e
    self.stop = True
    print('{} - data: {}'.format(e, data))


if __name__ == "__main__":
  import sys
  # import exio
  import time

  class MyWebsocketClient(WebsocketClient):

    def onOpen(self):
      self.url = "wss://feed.sandbox.ex.io"
      self.symbols = ["btc-usdt", "eth-btc"]
      self.message_count = 0
      print("Let's count the messages!")

    def onUpdate(self, msg):
      print(json.dumps(msg, indent=4, sort_keys=True))
      self.message_count += 1

    def onClose(self):
      print("-- Goodbye! --")

  # wsClient = MyWebsocketClient()
  wsClient = MyWebsocketClient( 
          key="lz8pGP0YajvUUpPyDM/X6N9fCx6RP48N78HLaWJLMQs=", 
          secret="O+LMRRKXDcvX2KrmxCPnVVNoZj8rRiZc9MLSlebiOIjioM9heVTRQ5j79883rS7VvMxP/XlT0650koeJx1NCSJOp0Gc79+25OjBEcTviFc/EBbYlFqdXyw==", 
          passphrase="lizeyuan")
  wsClient.start()
  print(wsClient.url, wsClient.symbols)
  try:
    while True:
      print("\nMessageCount =", "%i \n" % wsClient.message_count)
      time.sleep(1)
  except KeyboardInterrupt:
    wsClient.close()

  if wsClient.error:
    sys.exit(1)
  else:
    sys.exit(0)
