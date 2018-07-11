#
# Live order book updated from the exio Websocket Feed

from sortedcontainers import SortedDict
from decimal import Decimal

class OrderBook(object):
    def __init__(self, symbol='btc-usdt', log_to=None):
        self._symbol = symbol
        self._asks = SortedDict()
        self._bids = SortedDict()
        self._client = PublicClient()
        self._sequence = -1
        self._log_to = log_to
        if self._log_to:
            assert hasattr(self._log_to, 'write')
        self._current_ticker = None

    @property
    def symbol(self):
        return self._symbol

    # def reset_book(self):
    #     self._asks = SortedDict()
    #     self._bids = SortedDict()
    #     res = self._client.get_product_order_book(symbol=self.symbol, level=3)
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
    #     self._sequence = res['sequence']

    def onUpdate(self, message):
        if self._log_to:
            pickle.dump(message, self._log_to)

        sequence = message['sequence']
        # if self._sequence == -1:
        #     self.reset_book()
        #     return
        if sequence <= self._sequence:
            # ignore older messages (e.g. before order book initialization from getProductOrderBook)
            return
        elif sequence > self._sequence + 1:
            self.onSequenceGap(self._sequence, sequence)
            # return

        msg_type = message['type']
        if msg_type == 'add':
            self.add(message)
        elif msg_type == 'remove':
            self.remove(message)
        elif msg_type == 'trade':
            self.trade(message)
            self._current_ticker = message
        # elif msg_type == 'change':
        #     self.change(message)

        self._sequence = sequence

    def onSequenceGap(self, gap_start, gap_end):
        # self.reset_book()
        print('Error: messages missing ({} - {}). Re-initializing  book at sequence.'.format(
            gap_start, gap_end, self._sequence))
        
        exit(-1)


    def add(self, order):
        order = {
            'oid': order['oid'],
            'side': order['side'],
            'price': Decimal(order['price']),
            'size': Decimal(order.get('size') or order['remaining_size'])
        }
        if order['side'] == 'buy':
            bids = self.get_bids(order['price'])
            if bids is None:
                bids = [order]
            else:
                bids.append(order)
            self.set_bids(order['price'], bids)
        else:
            asks = self.get_asks(order['price'])
            if asks is None:
                asks = [order]
            else:
                asks.append(order)
            self.set_asks(order['price'], asks)

    def remove(self, order):
        price = Decimal(order['price'])
        if order['side'] == 'buy':
            bids = self.get_bids(price)
            if bids is not None:
                bids = [o for o in bids if o['oid'] != order['oid']]
                if len(bids) > 0:
                    self.set_bids(price, bids)
                else:
                    self.remove_bids(price)
        else:
            asks = self.get_asks(price)
            if asks is not None:
                asks = [o for o in asks if o['oid'] != order['oid']]
                if len(asks) > 0:
                    self.set_asks(price, asks)
                else:
                    self.remove_asks(price)

    def trade(self, order):
        size = Decimal(order['size'])
        price = Decimal(order['price'])

        if order['side'] == 'buy':
            bids = self.get_bids(price)
            if not bids:
                return
            assert bids[0]['id'] == order['maker_order_id']
            if bids[0]['size'] == size:
                self.set_bids(price, bids[1:])
            else:
                bids[0]['size'] -= size
                self.set_bids(price, bids)
        else:
            asks = self.get_asks(price)
            if not asks:
                return
            assert asks[0]['id'] == order['maker_order_id']
            if asks[0]['size'] == size:
                self.set_asks(price, asks[1:])
            else:
                asks[0]['size'] -= size
                self.set_asks(price, asks)

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
    #         bids = self.get_bids(price)
    #         if bids is None or not any(o['id'] == order['order_id'] for o in bids):
    #             return
    #         index = [b['id'] for b in bids].index(order['order_id'])
    #         bids[index]['size'] = new_size
    #         self.set_bids(price, bids)
    #     else:
    #         asks = self.get_asks(price)
    #         if asks is None or not any(o['id'] == order['order_id'] for o in asks):
    #             return
    #         index = [a['id'] for a in asks].index(order['order_id'])
    #         asks[index]['size'] = new_size
    #         self.set_asks(price, asks)

    #     tree = self._asks if order['side'] == 'sell' else self._bids
    #     node = tree.get(price)

    #     if node is None or not any(o['id'] == order['order_id'] for o in node):
    #         return

    # def get_current_ticker(self):
    #     return self._current_ticker

    def getCurrentBook(self):
        result = {
            'sequence': self._sequence,
            'asks': [],
            'bids': [],
        }
        for ask in self._asks:
            try:
                # There can be a race condition here, where a price point is removed
                # between these two ops
                this_ask = self._asks[ask]
            except KeyError:
                continue
            for order in this_ask:
                result['asks'].append([order['price'], order['size'], order['id']])
        for bid in self._bids:
            try:
                # There can be a race condition here, where a price point is removed
                # between these two ops
                this_bid = self._bids[bid]
            except KeyError:
                continue

            for order in this_bid:
                result['bids'].append([order['price'], order['size'], order['id']])
        return result

    def getAsk(self):
        return self._asks.peekitem(0)[0]

    def getAsks(self, price):
        return self._asks.get(price)

    def removeAsks(self, price):
        del self._asks[price]

    def setAsks(self, price, asks):
        self._asks[price] = asks

    def getBid(self):
        return self._bids.peekitem(-1)[0]

    def getBids(self, price):
        return self._bids.get(price)

    def removeBids(self, price):
        del self._bids[price]

    def setBids(self, price, bids):
        self._bids[price] = bids


