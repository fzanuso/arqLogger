# -*- coding: utf-8 -*-
"""

    Name: Strategy name
    Version: 1.0.0

"""
import math
import time
from datetime import datetime

from enum import Enum

from arquants import Strategy, Order


class Req(Enum):
    NEW = 0
    REPLACE = 1
    CANCEL = 2


class StrategyType(Enum):
    MM = 0


class MMStrategyState(Enum):
    WAITING_FOR_SIGNAL = 0
    SENDING_ORDERS = 1
    WAITING_TRADE = 2
    HOLD = 3


class MMStrategy(Strategy):

    def __init__(self, min_spread_ticks=5, order_size=100, debug=True):


        super(MMStrategy, self).__init__()
        #self.data2
        strategies = []
        states = []
        md = {
            StrategyType.MM.value: [[]]
        }
        self.initialize(strategies, states, md, debug)

        # Parameters

    def generate_index_mm(self):
        """
        return a dictionary by index with a list of instruments associated with the index.
        every index represent a unique set of instruments for the strategy
        :return: dict of list of list
        """
        index = 0
        data = 0
        sets = 1
        subsets = 1
        index_list = dict()
        while True:
            if hasattr(self, 'data' + str(data)):
                for i in range(subsets):
                    index_list[index] = ['data' + str(data + i)]
                    index += 1
            else:
                break
            data += sets
        return index_list

    def generate_signal_mm(self, index, data):
        self.log_md(StrategyType.MM, index)
        if self.trades_to_process[StrategyType.MM.value][index] > 0:
            self.trades_to_process[StrategyType.MM.value][index] -= 1
            self.logs_if("Strategy: %s - Index: %s - MD trade generados por la estrategia" % (StrategyType.MM.name, index))
        elif self.strategy_state[StrategyType.MM.value][index] is MMStrategyState.WAITING_FOR_SIGNAL.value:
            if self.get_data_value(data[0], "bid_px") and self.get_data_value(data[0], "offer_px"):
                bid_px = data[0].bid_px[0] + data[0].get_tick()
                offer_px = data[0].offer_px[0] - data[0].get_tick()
                if offer_px - bid_px >= (self.min_spread_ticks * data[0].get_tick()):
                    bid_qty, offer_qty = self.get_size()
                    self.signals[StrategyType.MM.value][index] = []
                    signal = dict()
                    signal['type'] = 0
                    signal['px'] = bid_px
                    signal['qty'] = bid_qty
                    signal['side'] = Order.Buy
                    self.signals[StrategyType.MM.value][index].append(signal)
                    signal = dict()
                    signal['type'] = 0
                    signal['px'] = offer_px
                    signal['qty'] = offer_qty
                    signal['side'] = Order.Sell
                    self.signals[StrategyType.MM.value][index].append(signal)
                else:
                    self.logs_if("Strategy: %s - Index: %s - Min tick no se cumple" % (StrategyType.MM.name, index))
            else:
                self.logs_if("Strategy: %s - Index: %s - No hay md en el book" % (StrategyType.MM.name, index))
        elif self.strategy_state[StrategyType.MM.value][index] is MMStrategyState.WAITING_TRADE.value:
            offer_px = data[0].offer_px[0]
            bid_px = data[0].bid_px[0]
            offer_signal = None
            bid_signal = None
            for ord in self.my_orders[StrategyType.MM.value][index].values():
                if ord.ordtype == Order.Buy:
                    if not self.my_compare_float(bid_px, ord.price):
                        bid_px = bid_px + data[0].get_tick()
                        bid_signal = dict()
                        bid_signal['type'] = 1
                        bid_signal['replace'] = ord.m_orderId
                        bid_signal['px'] = bid_px
                        bid_signal['qty'] = ord.size
                if ord.ordtype == Order.Sell:
                    if not self.my_compare_float(offer_px, ord.price):
                        offer_px = offer_px - data[0].get_tick()
                        offer_signal = dict()
                        offer_signal['type'] = 1
                        offer_signal['replace'] = ord.m_orderId
                        offer_signal['px'] = offer_px
                        offer_signal['qty'] = ord.size
            if bid_signal or offer_signal:
                if len(self.my_orders[StrategyType.MM.value][index]) == 2:
                    if offer_px - bid_px >= (self.min_spread_ticks * data[0].get_tick()):
                        self.signals[StrategyType.MM.value][index] = []
                        if bid_signal:
                            self.signals[StrategyType.MM.value][index].append(bid_signal)
                        if offer_signal:
                            self.signals[StrategyType.MM.value][index].append(offer_signal)
                    else:
                        self.logs_if("Strategy: %s - Index: %s - Min tick no se cumple, cancelamos." %
                                     (StrategyType.MM.name, index))
                        self.signals[StrategyType.MM.value][index] = []
                        for ord in self.my_orders[StrategyType.MM.value][index].values():
                            cancel_signal = dict()
                            cancel_signal['type'] = 2
                            cancel_signal['cancel'] = ord.m_orderId
                            self.signals[StrategyType.MM.value][index].append(cancel_signal)
                else:
                    self.signals[StrategyType.MM.value][index] = []
                    if offer_signal:
                        self.signals[StrategyType.MM.value][index].append(offer_signal)
                    if bid_signal:
                        self.signals[StrategyType.MM.value][index].append(bid_signal)
            else:
                self.logs_if("Strategy: %s - Index: %s - No podemos mejorar." % (StrategyType.MM.name, index))

    def process_signal_mm(self, index, signals):
        self.change_state(index, StrategyType.MM.value, MMStrategyState.SENDING_ORDERS.value)
        for signal in signals:
            if signal['type'] == 0:
                self.new_order(StrategyType.MM, index, signal['side'], 0, signal['px'], signal['qty'])
            elif signal['type'] == 1:
                ord_to_replace = self.my_orders[StrategyType.MM.value][index][signal['replace']]
                self.replace_order(StrategyType.MM, index, ord_to_replace, signal['px'], signal['qty'])
            elif signal['type'] == 2:
                ord_to_cancel = self.my_orders[StrategyType.MM.value][index][signal['cancel']]
                self.cancel_order(StrategyType.MM, index, ord_to_cancel)

    def notify_order_mm(self, index, order):
        if self.strategy_state[StrategyType.MM.value][index] in (MMStrategyState.SENDING_ORDERS.value,
                                                                 MMStrategyState.WAITING_TRADE.value):
            if order.status in (Order.Completed, Order.Partial):
                self.acum[order.ordtype] += abs(list(order.executed.exbits)[-1].size)
            # Order.Completed, Order.Partial, Order.Accepted, Order.Rejected, Order.Cancelled, Order.Canceled
            if not self.my_orders[StrategyType.MM.value][index]:
                self.change_state(index, StrategyType.MM.value, MMStrategyState.WAITING_FOR_SIGNAL.value)
            elif not self.ack[StrategyType.MM.value][index][0] and \
                    not self.ack[StrategyType.MM.value][index][1] and \
                    not self.ack[StrategyType.MM.value][index][2]:
                self.change_state(index, StrategyType.MM.value, MMStrategyState.WAITING_TRADE.value)

    def get_size(self):
        diff = self.acum[Order.Buy] - self.acum[Order.Sell]
        if self.my_compare_float(diff, 0.0):
            return self.order_size, self.order_size
        elif diff > 0:
            return self.order_size - diff, self.order_size
        elif diff < 0:
            return self.order_size, self.order_size + diff

    def initialize(self, strategies, states, md, debug=True):

        # Parameters
        self.strategies = strategies  # enum with sub-strategies
        self.states = states  # list order by sub-strategy id with enum of sub-strategies states
        self.md_info = md  # Dictionary by sub-strategy with a list of list of market data to check
        self.debug = debug  # used for logging
        self.log_string = "" # used to store logs during event

        self.idx_to_process = dict()  # Dictionary by strategy with a set of index to process when md arrives.
        self.idx_data = dict()  # Dictionary by index with a list of instrument associated to the index
        self.idx_by_inst = dict() # Dictionary by instrument's data with list of index associated to the instrument
        self.symbol_data = dict() # Dictionary by strategy and index with list of data associated
        self.signals = dict()  # Dictionary by strategy and index with signals generated by the strategy
        self.strategy_state = dict()  # Dictionary by strategy and index with the state of the strategy
        self.last_md = dict()  # Dictionary by strategy and index with last market data received
        self.trades_to_process = dict()  # Dictionary by strategy and index of number of trades to process
        self.my_orders = dict()  # Dictionary by strategy and index of orders by order_id
        self.index_of_orders = dict()  # Dictionary by strategy and order_id with index of the order
        # List of dictionaries by strategy, index and order_id
        # where we store information about new request sent to the market (0=new, 1=replace, 2=cancel)
        self.ack = [dict(), dict(), dict()]

        self.log_string = ""    # log string

        self.init_data()
        self.log_index_info()

    def next(self):
        self.generate_signals()

        # process signals
        for strategy in self.strategies:
            for index, signals in self.signals[strategy.value].items():
                getattr(self, 'process_signal_%s' % strategy.name.lower())(index, signals)

        # clear processed signals
        for strategy in self.strategies:
            self.signals[strategy.value].clear()

        self.flush_logs()

    def new_order(self, strategy, index, side, symbol_id, px, qty):
        if side == Order.Buy:
            order = self.buy(data=self.symbol_data[strategy.value][index][symbol_id],
                             price=px, size=qty, exectype=Order.Limit)
        elif side == Order.Sell:
            order = self.sell(data=self.symbol_data[strategy.value][index][symbol_id],
                              price=px, size=qty, exectype=Order.Limit)

        self.index_of_orders[strategy.value][order.m_orderId] = index
        self.my_orders[strategy.value][index][order.m_orderId] = order
        self.ack[strategy.value][index][Req.NEW.value][order.m_orderId] = order

    def replace_order(self, strategy, index, order_to_replace, new_px, new_qty):
        replaced_order = self.replace(size=new_qty, price=new_px, order=order_to_replace)

        self.index_of_orders[strategy.value][replaced_order.m_orderId] = index
        self.my_orders[strategy.value][index][replaced_order.m_orderId] = replaced_order
        self.ack[strategy.value][index][Req.REPLACE.value][replaced_order.m_orderId] = order_to_replace

    def cancel_order(self, strategy, index, order_to_cancel):
        self.cancel(order_to_cancel)
        self.ack[strategy.value][index][Req.CANCEL.value][order_to_cancel.m_orderId] = order_to_cancel

    def notify_order(self, order):
        # check strategy that send the order
        for strategy in self.strategies:
            if order.m_orderId in self.index_of_orders[strategy.value].keys():
                if order.status not in (Order.Created, Order.Submitted):
                    index = self.index_of_orders[strategy.value][order.m_orderId]
                    self.log_order_info(strategy.name, index, order)
                    if order.m_orderId in self.ack[strategy.value][index][Req.NEW.value].keys():
                        del self.ack[strategy.value][index][Req.NEW.value][order.m_orderId]
                    elif order.m_orderId in self.ack[strategy.value][index][Req.REPLACE.value].keys():
                        if order.status is not Order.Rejected:
                            replaced = self.ack[strategy.value][index][Req.REPLACE.value][order.m_orderId]
                            del self.my_orders[strategy.value][index][replaced.m_orderId]
                            del self.index_of_orders[strategy.value][replaced.m_orderId]
                        del self.ack[strategy.value][index][Req.REPLACE.value][order.m_orderId]
                    elif order.m_orderId in self.ack[strategy.value][index][Req.CANCEL.value].keys():
                        del self.ack[strategy.value][index][Req.CANCEL.value][order.m_orderId]
                    if order.status in (Order.Completed, Order.Rejected, Order.Canceled):
                        del self.my_orders[strategy.value][index][order.m_orderId]
                        del self.index_of_orders[strategy.value][order.m_orderId]
                    getattr(self, 'notify_order_%s' % strategy.name.lower())(index, order)
                break
            else:
                self.log_order_not_expected(strategy, None, order)
        self.flush_logs()

    def generate_signals(self):
        self.update_market_data()
        for strategy in self.strategies:
            for idx in self.idx_to_process[strategy.value]:
                # for every sub-strategy we call generate signals for every index in which market data changed
                getattr(self, 'generate_signal_%s' % strategy.name.lower())(idx, self.symbol_data[strategy.value][idx])
            self.idx_to_process[strategy.value].clear()

    def update_market_data(self):
        """
        Update market data of every instrument and identify index of every strategy that need to be process.
        """
        for instr in self.last_md.keys():
            data = getattr(self, instr)
            for md in self.last_md[instr].keys():
                self.last_md[instr][md][0] = self.last_md[instr][md][1]
                self.last_md[instr][md][1] = self.get_data_value(data, md)
                if self.last_md[instr][md][0] != self.last_md[instr][md][1]:
                    for strategy in self.strategies:
                        if instr in self.idx_by_inst[strategy.value].keys() and \
                                md in self.idx_by_inst[strategy.value][instr].keys():
                            for idx in self.idx_by_inst[strategy.value][instr][md]:
                                self.idx_to_process[strategy.value].add(idx)

    def on_pause(self):
        self.logs("Se apreto pausa, cancelando órdenes")
        self.cancel_all()
        self.flush_logs()

    def on_error(self):
        self.logs("Ocurrio un error, cancelando órdenes")
        self.cancel_all()
        self.flush_logs()

    def cancel_all(self):
        # Esperamos 1seg para evitar limite de logueo
        time.sleep(1)
        for strategy in self.strategies:
            for index in self.my_orders[strategy.value].keys():
                for order in self.my_orders[strategy.value][index].values():
                    self.logs("Cancelling order: strategy: %s - index: %s - id: %s" %
                              (strategy.name, index, order.m_orderId))
                    self.cancel(order)
            # volvemos a setaer estados iniciales
            for index in self.strategy_state[strategy.value].keys():
                self.change_state(index, strategy.value, 0)

    def init_data(self):
        for strategy in self.strategies:
            i = 0
            while True:
                if hasattr(self, 'data' + str(i)):
                    self.last_md['data' + str(i)] = dict()
                else:
                    break
                i += 1
            self.idx_by_inst[strategy.value] = dict()
            self.idx_to_process[strategy.value] = set()
            self.signals[strategy.value] = dict()
            self.strategy_state[strategy.value] = dict()
            self.trades_to_process[strategy.value] = dict()
            self.my_orders[strategy.value] = dict()
            self.index_of_orders[strategy.value] = dict()
            self.ack[strategy.value] = dict()
            self.idx_data[strategy.value] = dict()
            self.symbol_data[strategy.value] = dict()
        for strategy in self.strategies:
            result = getattr(self, 'generate_index_%s' % strategy.name.lower())()
            for idx in result.keys():
                self.symbol_data[strategy.value][idx] = []
                self.idx_data[strategy.value][idx] = []
                i = 0
                for inst in result[idx]:
                    self.symbol_data[strategy.value][idx].append(getattr(self, inst))
                    self.idx_data[strategy.value][idx].append(inst)
                    if inst not in self.idx_by_inst[strategy.value].keys():
                        self.idx_by_inst[strategy.value][inst] = dict()
                        #self.idx_by_inst[strategy.value][inst] = set()
                    for md in self.md_info[strategy.value][i]:
                        self.last_md[inst][md] = [None, None]
                        if md not in self.idx_by_inst[strategy.value][inst].keys():
                            self.idx_by_inst[strategy.value][inst][md] = set()
                        self.idx_by_inst[strategy.value][inst][md].add(idx)
                    i += 1
                self.ack[strategy.value][idx] = [None, None, None]
                self.ack[strategy.value][idx][Req.NEW.value] = dict()
                self.ack[strategy.value][idx][Req.REPLACE.value] = dict()
                self.ack[strategy.value][idx][Req.CANCEL.value] = dict()
                self.trades_to_process[strategy.value][idx] = 0
                self.strategy_state[strategy.value][idx] = 0
                self.my_orders[strategy.value][idx] = dict()

    ####################
    # HELPER FUNCTIONS #
    ####################

    def change_state(self, index, strategy_id, new_state_id):
        if self.debug:
            self.logs("Strategy: %s - Index: %s - Changing State from '%s' to '%s'" %
                  (strategy_id, index, self.strategy_state[strategy_id][index], new_state_id))
        self.strategy_state[strategy_id][index] = new_state_id

    @staticmethod
    def my_compare_float(float1, float2, prec=6):
        """ Comparamos 2 float con un minimos de precision.
        True si son igual - else false
        """
        if float1 and float2:
            return abs(float1 - float2) <= (1 / 10 ** prec)
        else:
            return float1 == float2

    @staticmethod
    def get_data_value(data, level):
        value = None
        if hasattr(data, level):
            value = getattr(data, level)[0]
            if not value or math.isnan(value):
                value = None
            else:
                value = round(value, 6)
        return value

    def get_strategy_state(self, strategy_id, index):
        return self.states[strategy_id](self.strategy_state[strategy_id][index])

    def log_md(self, strategy, index):
        if self.debug:
            line = "Strategy: %s - Index: %s - State: %s. Market Data: " % \
                   (strategy.name, index, self.get_strategy_state(strategy.value, index).name)
            i = 0
            for data_name in self.idx_data[strategy.value][index]:
                data = getattr(self, data_name)
                line = line + "%s: " % data.tradecontract
                for md in self.md_info[strategy.value][i]:
                    line = line + " %s@%s " % (md, self.last_md[data_name][md][1])
                i += 1
            self.logs(line)

    def log_order_not_expected(self, strategy, index, order):
        """
        Logging unexpected order.
        """
        state = None if not index else self.strategy_state[strategy.value][index].name
        self.logs("Strategy: %s - Index: %s - State: %s. Unexpected order: id: %s - status: %s" %
                  (strategy.name, index, state, order.m_orderId, order.status))

    def log_order_info(self, strategy_name, index, order):
        if order.status is Order.Created:
            self.logs_if("Strategy: %s - Index: %s - order Created: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Submitted:
            self.logs_if("Strategy: %s - Index: %s  order Submitted: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Accepted:
            self.logs_if("Strategy: %s - Index: %s  order Accepted: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Partial:
            self.logs_if("Strategy: %s - Index: %s  order Partial: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Completed:
            self.logs_if("Strategy: %s - Index: %s - order Completed: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Canceled:
            self.logs_if("Strategy: %s - Index: %s  order Canceled: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Expired:
            self.logs_if("Strategy: %s - Index: %s  order Expired: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Margin:
            self.logs_if("Strategy: %s - Index: %s  order Margin: %s" % (strategy_name, index, order.m_orderId))
        elif order.status is Order.Rejected:
            self.logs_if("Strategy: %s - Index: %s  order Rejected: %s" % (strategy_name, index, order.m_orderId))
        else:
            self.logs_if("Strategy: %s - Index: %s  order with not knowing status: %s" % (strategy_name, index,
                                                                                          order.m_orderId))

    def log_index_info(self):
        for strategy in self.strategies:
            for idx in self.idx_data[strategy.value].keys():
                i = 0
                line = "Strategy: %s - Index: %s - \n" % (strategy.name, idx)
                for data in self.symbol_data[strategy.value][idx]:
                    line = line + "%s: %s\n" % (i, data.tradecontract)
                    i += 1
                self.logs_if(line)

    def logs_if(self, msg):
        if self.debug:
            self.log_string += str(datetime.now()) + " {" + msg + "}|"

    def flush_logs(self):
        self.logs(self.log_string)
        self.log_string = ""

    def get_best_bids(self, index_for_ci, data_ci):
        """
        Devuelve una lista con el 1er y 2do mejor precio BID,
        sin tener en cuenta nuestra orden.
        None, si no hay otro precio.
        """
        level = 2
        bids_d = dict()
        data = self.get_data_value(data_ci, 'bid_px')
        if data:
            bids_d[data] = data_ci.bid_qty[0]
            data = self.get_data_value(data_ci, 'bid_px_' + str(level))
        while data:
            data = round(data, 6)
            bids_d[data] = self.get_data_value(data_ci, 'bid_qty_' + str(level))
            level += 1
            data = self.get_data_value(data_ci, 'bid_px_' + str(level))
        if self.orders_ci[0][index_for_ci]:
            for my_order in self.orders_ci[0][index_for_ci].values():
                px = round(my_order.price, 6)
                if bids_d[px]:
                    if bids_d[px] >= my_order.executed.remsize:
                        bids_d[px] -= my_order.executed.remsize
        bids = [None, None]
        i = 0
        for k, v in bids_d.items():
            if bids_d[k] > 0:
                bids[i] = bids_d[k]
                i += 1
            if i == 2:
                break
        print(bids)
        return bids