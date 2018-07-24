import requests


class PublicClient(object):
  """
  exio public api
  """

  def __init__(self, apiUrl='https://api.sandbox.ex.io/v1', timeout=30):
    """Create EXIO API public client.

    Args:
        apiUrl (Optional[str]): API URL. Defaults to EXIO API.

    """
    self.url = apiUrl.rstrip('/')
    self.timeout = timeout

  def _get(self, path, params=None):
    """Perform get request"""

    r = requests.get(self.url + path, params=params, timeout=self.timeout)
    # r.raise_for_status()
    return r.json()

  def getProducts(self):
    """Get a list of available currency pairs for trading.

    Returns:
        list: Info about all currency pairs. Example::
            {
            "msg": "ok",
            "symbols": [
            {
              "name": "eth-btc",
              "description": "Ethereum / Bitcoin",
              "base": "eth",
              "base_min_tick": "0.01",
              "base_min_size": "0.1",
              "base_max_size": "100000",
              "quote": "btc",
              "quote_min_tick": "0.00001",
              "fees": "btc"
            },
            {
              "name": "eth-usdt",
              "description": "Ethereum / U.S Dollar Tether",
              "base": "eth",
              "base_min_tick": "0.01",
              "base_min_size": "0.1",
              "base_max_size": "100000",
              "quote": "usdt",
              "quote_min_tick": "0.1",
              "fees": "usdt"
            },
            {
              "name": "btc-usdt",
              "description": "Bitcoin / U.S Dollar Tether",
              "base": "btc",
              "base_min_tick": "0.0001",
              "base_min_size": "0.01",
              "base_max_size": "100000",
              "quote": "usdt",
              "quote_min_tick": "1",
              "fees": "usdt"
            }
            ]
            }

    """
    return self._get('/symbols')

  def getTickSize(self, symbol):
    symbols = self.getProducts()["symbols"]

    tickSize = float([sym["quote_min_tick"]
                      for sym in symbols if str(sym["name"]) == symbol][0])
    minSize = float([sym["base_min_size"]
                     for sym in symbols if str(sym["name"]) == symbol][0])

    return tickSize, minSize

  def getCurrencies(self):
    """List known currencies.

    Returns:
        list: List of currencies. Example::
            [{
                "id": "BTC",
                "name": "Bitcoin",
                "min_size": "0.00000001"
            }, {
                "id": "USD",
                "name": "United States Dollar",
                "min_size": "0.01000000"
            }]

    """
    return self._get('/currencies')


if __name__ == '__main__':
  import json

  client = PublicClient()

  print json.dumps(client.getProducts(), indent=2)

  print "\n\n" + json.dumps(client.getCurrencies(), indent=2)
