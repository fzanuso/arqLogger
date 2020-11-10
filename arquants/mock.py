from enum import Enum
import queue
import uuid
from threading import Thread
import time


class Position(object):

    def __init__(self):
        self.size = 0


class Broker(object):

    def __init__(self):
        self.position = dict()

    def getposition(self, data, clone=False):
        return self.position[data.tradecontract]

    def update_position(self, contract, size):
        if contract not in self.position.keys():
            self.position[contract] = Position()
        self.position[contract].size += size

class Strategy(object):

    instruments = {}

    def __init__(self):
        self.set_instruments(Strategy.instruments)
        self.orders_new = queue.Queue()
        self.orders_replace = queue.Queue()
        self.orders_cancel = queue.Queue()
        self.orders_by_id = dict()
        self.broker = Broker()

    def get_order(self, index):
        idx = 0
        for order in self.orders_by_id.values():
            if idx == index:
                return order
            idx += 1

    def notify_submitted(self, order):
        time.sleep(0.5)
        order.status = Order.Submitted
        self.notify_order(order)
        
    def logs(self, msg):
        print("stratey log: "+msg)

    def set_instruments(self, instr):
        self.__instr__ = dict()
        for k, v in instr.items():
            self.__instr__[v.tradecontract] = k
            self.__setattr__(k, v)

    def buy(self, data, price, size, exectype):
        print("se envia una orden BUY para %s de %s@%s tipo %s." % (data.tradecontract,
                                                                    size, price,
                                                                    exectype))
        return self.create_order(data, price, size, exectype, Order.Buy)

    def sell(self, data, price, size, exectype):
        print("se envia una orden SELL para %s de %s@%s tipo %s." % (data.tradecontract,
                                                                     size, price,
                                                                     exectype))
        return self.create_order(data, price, size, exectype, Order.Sell)

    def replace(self, size, price, order):
        print("se envia a reemplazar orden %s id: %s - Pasamos de %s@%s a %s@%s." % (
            order.ordtype, order.m_orderId,
            order.size, order.price, size, price))
        order = OrderLimit(price, size, order.ordtype, data=order.data, ordType=order.type, replace_id=order.m_orderId)
        self.orders_by_id[order.m_orderId] = order
        self.orders_replace.put(order)
        return order

    def cancel(self, order):
        print("se envia a cancelar orden %s id: %s." % (order.ordtype, order.m_orderId))
        self.orders_cancel.put(self.orders_by_id[order.m_orderId])

    def create_order(self, data1, price, size, type, side):
        order = OrderLimit(price, size, side, data=data1, ordType=type)
        self.orders_new.put(order)
        self.orders_by_id[order.m_orderId] = order
        #Thread(target=self.notify_submitted, args=(order,)).start()
        return order

    def next(self):
        raise NotImplementedError("Must override next")

    def update_order(self, ord_id, state, size=0):
        time.sleep(0.1)
        order = self.orders_by_id[ord_id]
        order.status = state

        if order.status is not Order.Rejected and order.replace_id:
            del self.orders_by_id[order.replace_id]

        m = 1
        if order.ordtype == Order.Sell:
            m = -1
        if order.status is Order.Partial:
            self.broker.update_position(order.data.tradecontract, m*size)
            order.executed.exbits.append(Trade(order.price, size))
            order.remaining -= size
        elif order.status is Order.Completed:
            self.broker.update_position(order.data.tradecontract, m*size)
            order.executed.exbits.append(Trade(order.price, order.remaining))
            order.remaining -= 0.0

        if order.status in (Order.Canceled, Order.Completed, Order.Expired, Order.Rejected):
            del self.orders_by_id[order.m_orderId]

        self.notify_order(order)

    def update_md(self, instrument, bid_qty=0, bid_px=0, offer_px=0, offer_qty=0):
        time.sleep(0.1)
        if instrument in self.__instr__.keys():
            data = getattr(self, self.__instr__[instrument])
            data.update_bid_px(bid_px)
            data.update_bid_qty(bid_qty)
            data.update_offer_px(offer_px)
            data.update_offer_qty(offer_qty)
            self.next()
        else:
            raise Exception("Instrument not in the List of the Strategy")


class Settle(Enum):
    S_CI = 1
    S_24 = 2
    S_48 = 3
    S_72 = 4


class Order(Enum):
    Created = 0
    Submitted = 1
    Completed = 2
    Canceled = 3
    Rejected = 4
    Expired = 5
    Partial = 6
    Accepted = 7
    Replace = 8
    Limit = 9
    Market = 10
    Buy = 11
    Sell = 12


class OrderLimit(object):
    def __init__(self, px, qty, side, data=None, ordType=Order.Limit, id=None, replace_id=None):
        self.data = data
        self.m_orderId = id if id else uuid.uuid1().__str__()
        self.price = px
        self.size = qty
        self.ordtype = side
        self.m_action = "BUY" if side == 0 else "SELL"
        self.type = ordType
        self.status = Order.Submitted
        self.executed = Executed()
        self.remaining = qty
        self.replace_id = replace_id


class Executed:
    def __init__(self):
        self.exbits = []
        self.remsize = 0


class Trade:
    def __init__(self, px, qty):
        self.price = px
        self.size = qty


class MarketData(object):
    def __init__(self, name, price_size, min_size, tick_px, settlement, bid_px=0, bid_qty=0, offer_px=0, offer_qty=0):
        self.price_size = float(price_size)
        self.tradecontract = name
        self.tick_px = tick_px
        self.contractsize = min_size
        self.settlement = settlement.value
        self.offer_px = [0]
        self.bid_px = [0]
        self.offer_qty = [0]
        self.bid_qty = [0]
        self.offer_px[0] = float(offer_px)
        self.offer_qty[0] = float(offer_qty)
        self.bid_px[0] = float(bid_px)
        self.bid_qty[0] = float(bid_qty)

    def update_bid_px(self, bid_px):
        self.bid_px[0] = float(bid_px) if bid_px else None

    def update_bid_qty(self, bid_qty):
        self.bid_qty[0] = float(bid_qty) if bid_qty else None

    def update_offer_px(self, offer_px):
        self.offer_px[0] = float(offer_px) if offer_px else None

    def update_offer_qty(self, offer_qty):
        self.offer_qty[0] = float(offer_qty) if offer_qty else None

    def update_md(self, bid_px, bid_qty, offer_px, offer_qty):
        self.offer_px[0] = float(offer_px)
        self.offer_qty[0] = float(offer_qty)
        self.bid_px[0] = float(bid_px)
        self.bid_qty[0] = float(bid_qty)

    def get_tick(self):
        return self.tick_px


Instruments = {
    "AY24 - CI": MarketData("AY24 - CI", 100, 1, 0.5, Settle.S_CI),
    "AY24D - CI": MarketData("AY24D - CI", 100, 1, 0.01, Settle.S_CI),
    "AY24 - 24hs": MarketData("AY24 - 24hs", 100, 1, 0.5, Settle.S_24),
    "AY24D - 24hs": MarketData("AY24D - 24hs", 100, 1, 0.01, Settle.S_24),
    "AY24 - 48hs": MarketData("AY24 - 48hs", 100, 1, 0.5, Settle.S_48),
    "AY24D - 48hs": MarketData("AY24D - 48hs", 100, 1, 0.01, Settle.S_48),
    "PARY - CI": MarketData("PARY - CI", 100, 1000, 0.5, Settle.S_CI),
    "PARYD - CI": MarketData("PARYD - CI", 100, 1000, 0.01, Settle.S_CI),
    "PARY - 24hs": MarketData("PARY - 24hs", 100, 1000, 0.5, Settle.S_24),
    "PARYD - 24hs": MarketData("PARYD - 24hs", 100, 1000, 0.01, Settle.S_24),
    "PARY - 48hs": MarketData("PARY - 48hs", 100, 1000, 0.5, Settle.S_48),
    "PARYD - 48hs": MarketData("PARYD - 48hs", 100, 1000, 0.01, Settle.S_48),
    "PESOS - T+1": MarketData("PESOS - T+1", 1, 1, 0.01, Settle.S_24),
    "PESOS - T+2": MarketData("PESOS - T+2", 1, 1, 0.01, Settle.S_48),
    "GGAL - CI": MarketData("GGAL - CI", 1, 1, 0.05, Settle.S_CI),
    "GGAL - 48hs": MarketData("GGAL - 48hs", 1, 1, 0.05, Settle.S_48),
}
