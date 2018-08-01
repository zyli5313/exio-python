import pytest
import time
import json
import datetime as dt
from exio.authClient import AuthenticatedClient

KEY = "lz8pGP0YajvUUpPyDM/X6N9fCx6RP48N78HLaWJLMQs="
SECRET = "O+LMRRKXDcvX2KrmxCPnVVNoZj8rRiZc9MLSlebiOIjioM9heVTRQ5j79883rS7VvMxP/XlT0650koeJx1NCSJOp0Gc79+25OjBEcTviFc/EBbYlFqdXyw=="
PASSPHRASE = "lizeyuan"

SYMBOL = "btc-usdt"
CURRENCY = "btc"

@pytest.fixture(scope="module")
def client():
  return AuthenticatedClient(KEY, SECRET, PASSPHRASE, 
    apiUrl="https://api.sandbox.ex.io/v1")

@pytest.mark.usefixtures('client')
class TestAuthenticatedClient:

  def test_sendIOC(self, client):
    order = client.buyIOC(SYMBOL, 1, 0.01)
    assert order["msg"] == "ok", order

    order = client.sellIOC(SYMBOL, 100000, 0.01)
    assert order["msg"] == "ok", order
    
  def test_sendGTC(self, client):
    order = client.buyGTC(SYMBOL, 1, 0.01)
    assert order["msg"] == "ok", order

    order = client.sellGTC(SYMBOL, 100000, 0.01)
    assert order["msg"] == "ok", order

    cancelMsg = client.cancelAll(SYMBOL)
    assert cancelMsg["msg"] == "ok", cancelMsg

    openOrders = client.getOpenOrders(SYMBOL)
    assert len(openOrders["orders"]) == 0, openOrders

    start = dt.datetime.today().strftime("%Y-%m-%d")
    end = start
    trades = client.getTradeHistory(SYMBOL, start, end)
    assert "trades" in trades, trades

  def test_funding(self, client):
    depositAdd = client.createDepositAddress(CURRENCY)
    assert "address" in depositAdd, depositAdd

    add = client.getDepositAddress(CURRENCY)
    assert add["msg"] == "ok", add

    funds = client.getFunds()
    assert funds["msg"] == "ok", funds

    pos = client.getPosition(CURRENCY)
    assert type(pos) == float, pos

    # destination = {}
    # withdraw = client.createWithdrawalRequest(CURRENCY, 0.01, destination)
    # assert False, withdraw

    withdrawHistory = client.getWithdrawalHistory(CURRENCY, 0.01, {})
    assert withdrawHistory["msg"] == "ok", withdrawHistory




