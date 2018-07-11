import pytest
import exio
import time
import datetime
from dateutil.relativedelta import relativedelta


@pytest.fixture(scope='module')
def client():
    return exio.PublicClient()


@pytest.mark.usefixtures('client')
class TestPublicClient(object):

    @staticmethod
    def teardown_method():
        time.sleep(.25)  # Avoid rate limit

    def test_getProducts(self, client):
        r = client.get_products()
        assert type(r) is list
        assert "btc-usd" in r[0]

    def test_getCurrencies(self, client):
        r = client.get_currencies()
        assert type(r) is list
        assert 'name' in r[0]
