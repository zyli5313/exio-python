import pytest
import time
import json
from exio.websocketClient import WebsocketClient

SYMBOL = "btc-usdt"

@pytest.fixture(scope="module")
def client():
  return WebsocketClient(url="wss://feed.sandbox.ex.io", 
    symbols=[SYMBOL])

@pytest.mark.usefixtures('client')
class TestWebsocketClient:

  def test_connect(self, client):
    client.connect()

    data = client.ws.recv()
    msg = json.loads(data)
    assert msg["symbol"] == SYMBOL, msg

    client.disconnect()

    assert client.ws.connected == False, client.ws.__dict__
