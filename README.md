<p align="center">
  <img src="https://s3.amazonaws.com/sandbox-exio-static/email/email-header.png" alt="ex.io">
</p>
<p align="center">
  <h1 align="center">exio-node</h1>
</p>
<p align="center">
  <b>A minimal client library &amp; CLI demonstrating API usage</b>
</p>

[![Build Status](https://travis-ci.org/zyli5313/exio-python.svg?branch=master)](https://travis-ci.org/zyli5313/exio-python)
[![Coverage Status](https://coveralls.io/repos/github/zyli5313/exio-python/badge.svg?branch=master)](https://coveralls.io/github/zyli5313/exio-python?branch=master)

This project contains a minimal client library that wraps ex.io's API. In addition, it contains a command-line utility that you can use to drive the client library. This is intended to demonstrate basic API usage.

### Library Usage

#### Install

```
$ python setup.py install
```

You can now import and instantiate a client object in your app.

#### Example

```python
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
```

### CLI Usage

This repository comes bundled with a simple CLI app that you can use to run various operations. The CLI app is built on top of the library. 

> Note: To get an API credentials, you must login to ex.io and create one from with your user settings.

The command-line utility defaults to using endpoints that are in the _sandbox_ environment, not production. Therefore, you should use API key, secret, and passphrases that were created from sandbox environment. If you want to use production endpoints, you can specificy them through the command-line:

```
$ python exio-cli.py -c subscribe -s btc-usdt --restApi=https://api.ex.io --websocketApi=wss://feed.ex.io
```

### Subscribe

The subscribe command will subscribe to the public `books` channel. If an API credentials are available, it will also subscribe to the private `orders` channel.

```
$ python exio-cli.py -c subscribe -s btc-usdt
$ python exio-cli.py -c subscribe -s btc-usdt --apiKey xxx --apiSecret xxx --apiPassphrase xxx
```

### Insert

The insert command will insert an order into the exchange. This command requires API credentials.

```
$ python exio-cli.py -c insert -s btc-usdt --apiKey xxx --apiSecret xxx --apiPassphrase xxx buy 4000 1
```

### Cancel

This cancel command will cancel all open orders for a particular symbol, or a particular order if given an order-id to cancel. This command requires you to provide an API credentials.

```
$ python exio-cli.py -c cancel -s btc-usdt --apiKey xxx --apiSecret xxx --apiPassphrase xxx
```

### Open

The open command will return all open orders you might have for a given symbol. This command requires API credentials.

```
$ python exio-cli.py -c open -s btc-usdt --apiKey xxx --apiSecret xxx --apiPassphrase xxx
```

### Funds

The funds command will return your balance information for all currencies. This command requiers API credentials.

```
$ python exio-cli.py -c funds -s btc-usdt --apiKey xxx --apiSecret xxx --apiPassphrase xxx
```