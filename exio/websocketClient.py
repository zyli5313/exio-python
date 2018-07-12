#
#
# Template object to receive messages from the exio Websocket Feed

from __future__ import print_function
import json
import base64
import hmac
import hashlib
import time
from threading import Thread
from websocket import create_connection, WebSocketConnectionClosedException
# from exioAuth import getAuthHeaders

class WebsocketClient(object):
    def __init__(self, url="wss://feed.sandbox.ex.io", symbols=None, messageType="subscribe",
                 shouldPrint=True, auth=False, key="", secret="", channels=None):
        self.url = url
        self.symbols = symbols
        self.channels = channels
        self.type = messageType
        self.stop = False
        self.error = None
        self.ws = None
        self.thread = None
        self.auth = auth
        self.key = key
        self.secret = secret
        self.shouldPrint = shouldPrint

    def start(self):
        def _go():
            self._connect()
            self._listen()
            self._disconnect()

        self.stop = False
        self.onOpen()
        self.thread = Thread(target=_go)
        self.thread.start()

    def _connect(self):
        if self.symbols is None:
            self.symbols = ["btc-usdt"]
        elif not isinstance(self.symbols, list):
            self.symbols = [self.symbols]

        if self.url[-1] == "/":
            self.url = self.url[:-1]

        if self.channels is None:
            sub_params = {'type': 'subscribe', 'channels': [{"name": "books", "symbols": self.symbols}]}
        else:
            sub_params = {'type': 'subscribe', 'channels': self.channels}

        if self.auth:
            timestamp = str(time.time())
            message = timestamp + 'GET' + '/user/self/verify'
            message = message.encode('ascii')
            hmac_key = base64.b64decode(self.secret)
            signature = hmac.new(hmac_key, message, hashlib.sha256)
            signature_b64 = base64.b64encode(signature.digest()).decode('utf-8').rstrip('\n')
            sub_params['signature'] = signature_b64
            sub_params['key'] = self.key
            sub_params['passphrase'] = self.api_passphrase
            sub_params['timestamp'] = timestamp

        self.ws = create_connection(self.url)

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
        self.thread.join()

    def onOpen(self):
        if self.shouldPrint:
            print("-- Subscribed! --\n")

    def onClose(self):
        if self.shouldPrint:
            print("\n-- Socket Closed --")

    def onUpdate(self, msg):
        if self.shouldPrint:
            print(msg)

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


    wsClient = MyWebsocketClient()
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
