import pytest
import numpy as np
from exio.publicClient import PublicClient

@pytest.fixture(scope="module")
def client():
  return PublicClient()

@pytest.mark.usefixtures('client')
class TestPublicClient:

  def test_getProduct(self, client):
    products = client.getProducts()

    assert products["msg"] == "ok", products

  def test_getTickSize(self, client):
    tickSize, minSize = client.getTickSize("btc-usdt")

    assert np.isclose(tickSize, 1.0) and np.isclose(minSize, 0.01), \
      "tickSize=%s minSize=%s" % (tickSize, minSize)

  def test_getCurrencies(self, client):
    currencies = client.getCurrencies()

    assert currencies["msg"] == "ok", currencies