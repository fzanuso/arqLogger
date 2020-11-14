from datetime import datetime
import queue
import math
import threading
import json
import time

from apscheduler.schedulers.background import BackgroundScheduler
import websocket

from .enums import Order, Side
from .logs import StrategyLog, InitializeEventLog, EREventLog, MDEventLog
from .logs import PauseEventLog, ErrorEventLog, InternalEventLog
from .logs import NewOrderResponseLog, CancelOrderResponseLog, ReplaceOrderResponseLog


class ArquantLogger():

    def __init__(self, url, strategy, strategy_id, client_id, param_list):
        # Connection related variables
        self.url = url
        # Initializing a queue
        self.queue = queue.Queue()
        self.ws_connection = None
        self.ws_thread = None
        self.schedTask = None
        self.connected = False
        self.strategy = strategy
        self.strategy_id = strategy_id
        self.client_id = client_id
        self.param_list = param_list
        self.execution_id = round(datetime.now().timestamp() * 100)
        self.msg_id = 0
        self.event_id = 0
        self.retry = 0
        self.retry_time = 5
        self.task_id = "logging_task"
        self._log_initialize_event()

    def connect(self):
        self.strategy.logs("Starting websocket connection...")
        self.ws_connection = websocket.WebSocketApp(self.url,
                                                    on_message=self._on_message,
                                                    on_error=self._on_error,
                                                    on_close=self._on_close,
                                                    on_open=self._on_open)

        # Create a thread and target it to the run_forever function, then start it.
        self.ws_thread = threading.Thread(target=self.ws_connection.run_forever,
                                          kwargs={"ping_interval": 270})
        self.ws_thread.start()

    def _start_logging(self):
        self.schedTask = BackgroundScheduler()
        self.schedTask.add_job(self._check_logs, 'interval', seconds=1, id=self.task_id)
        self.schedTask.start()
        self.strategy.logs("Start Scheduling Logs")

    def _check_logs(self):
        if self.ws_connection.sock and self.ws_connection.sock.connected:
            while not self.queue.empty():
                msg = self.queue.get()
                self._send_log(msg)
        else:
            self.schedTask.remove_job(self.task_id)
            self.schedTask = None

    def _send_log(self, log):
        self.msg_id += 1
        log.id = self.msg_id
        self.ws_connection.send(json.dumps(log.__dict__, cls=Encoder))

    def _on_message(self, message):
        self.strategy.logs("message arrived: %s" % message)

    def _on_error(self, exception):
        self.strategy.logs("error during websocket connection: %s. "
                           "waiting %s sec until next retrying connecting." % (exception, self.retry_time))
        time.sleep(self.retry_time)
        if not self.ws_connection.sock.connected:
            self.strategy.logs("retrying connecting nro: %s." % self.retry)
            self.retry += 1
            self.connect()

    def _on_close(self):
        self.connected = False

    def _on_open(self):
        self.connected = True
        self._start_logging()

    def close_connection(self):
        if self.ws_connection.sock and self.ws_connection.sock.connected:
            self.ws_connection.close()

    def _append_log(self, log):
        self.queue.put(log)

    # Logging methods
    def _log_initialize_event(self, additional=None):
        self.event_id += 1
        self._append_log(InitializeEventLog(-1,
                                            self.strategy_id,
                                            self.execution_id,
                                            self.client_id,
                                            self.event_id,
                                            self.param_list,
                                            additional))

    def log_er_event(self, order, additional=None):
        self.event_id += 1
        try:
            last = []
            if order.executed.exbits:
                for l in list(order.executed.exbits):
                    last.append({"px": l.price, "qty": l.size})
            self._append_log(EREventLog(-1,
                                        self.strategy_id,
                                        self.execution_id,
                                        self.client_id,
                                        self.event_id,
                                        order.m_orderId,
                                        self.get_order_status(order.status),
                                        last,
                                        order.executed.remsize,
                                        additional))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_er_event. exception: %s" % e)

    def log_md_event(self, data_list=None, entry_list=None, additional=None):
        self.event_id += 1
        try:
            md_map = dict()
            idx = 0
            for data in data_list:
                md_map[data.tradecontract] = dict()
                for entry in entry_list[idx]:
                    md_map[data.tradecontract][entry] = self.get_data_entry(data, entry)
                idx += 1
            self._append_log(MDEventLog(-1,
                                        self.strategy_id,
                                        self.execution_id,
                                        self.client_id,
                                        self.event_id,
                                        md_map,
                                        additional))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_md_event. exception: %s" % e)

    def log_pause_event(self, description=None, additional=None):
        self.event_id += 1
        try:
            self._append_log(PauseEventLog(-1,
                                           self.strategy_id,
                                           self.execution_id,
                                           self.client_id,
                                           self.event_id,
                                           description,
                                           additional))
            time.sleep(1)
            self.close_connection()
        except Exception as e:
            self.strategy.logs("Could not generate log in log_pause_event. exception: %s" % e)

    def log_error_event(self, description=None, additional=None):
        self.event_id += 1
        try:
            self._append_log(ErrorEventLog(-1,
                                           self.strategy_id,
                                           self.execution_id,
                                           self.client_id,
                                           self.event_id,
                                           description,
                                           additional))
            self.close_connection()
        except Exception as e:
            self.strategy.logs("Could not generate log in log_error_event. exception: %s" % e)

    def log_internal_event(self, description=None, additional=None):
        self.event_id += 1
        try:
            self._append_log(InternalEventLog(-1,
                                              self.strategy_id,
                                              self.execution_id,
                                              self.client_id,
                                              self.event_id,
                                              description,
                                              additional))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_internal_event. exception: %s" % e)

    def log_new_order_response(self, order, additional=None):
        try:
            self._append_log(NewOrderResponseLog(-1,
                                                 self.strategy_id,
                                                 self.execution_id,
                                                 self.client_id,
                                                 self.event_id,
                                                 order.m_orderId,
                                                 order.m_action,
                                                 order.price,
                                                 order.size,
                                                 order.data.tradecontract,
                                                 additional))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_new_order_response. exception: %s" % e)

    def log_cancel_order_response(self, order, additional=None):
        try:
            self._append_log(CancelOrderResponseLog(-1,
                                                    self.strategy_id,
                                                    self.execution_id,
                                                    self.client_id,
                                                    self.event_id,
                                                    order.m_orderId,
                                                    additional))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_cancel_order_response. exception: %s" % e)

    def log_replace_order_response(self, order, additional=None):
        try:
            self._append_log(ReplaceOrderResponseLog(-1,
                                                     self.strategy_id,
                                                     self.execution_id,
                                                     self.client_id,
                                                     self.event_id,
                                                     order.m_orderId,
                                                     order.m_action,
                                                     order.price,
                                                     order.size,
                                                     order.data.tradecontract,
                                                     additional))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_replace_order_response. exception: %s" % e)

    def log_strategy(self, data):
        try:
            self._append_log(StrategyLog(-1,
                                         self.strategy_id,
                                         self.execution_id,
                                         self.client_id,
                                         self.event_id,
                                         data))
        except Exception as e:
            self.strategy.logs("Could not generate log in log_strategy. exception: %s" % e)

    def new_limit_order(self, data, side, px, qty, additional=None):
        if side is Side.Buy:
            order = self.strategy.buy(data=data, price=px, size=qty, exectype=2)
        elif side is Side.Sell:
            order = self.strategy.sell(data=data, price=px, size=qty, exectype=2)
        else:
            raise Exception("Invalid side: %s" % side)
        self.log_new_order_response(order, additional)
        return order

    def replace_order(self, order, new_px, new_qty, additional=None):
        replaced_order = self.strategy.replace(size=new_qty, price=new_px, order=order)
        self.log_replace_order_response(order, additional)
        return replaced_order

    def cancel_order(self, order, additional=None):
        self.strategy.cancel(order)
        self.log_cancel_order_response(order, additional)

    @staticmethod
    def get_data_entry(data, entry):
        value = None
        if hasattr(data, entry):
            value = getattr(data, entry)
            if not isinstance(value, float):
                value = value[0]
            if not value or math.isnan(value):
                value = None
            else:
                value = round(value, 6)
        return value

    @staticmethod
    def get_order_status(status):
        if status is Order.Created:
            return "Created"
        elif status is Order.Submitted:
            return "Submitted"
        elif status is Order.Accepted:
            return "Accepted"
        elif status is Order.Partial:
            return "Partial"
        elif status is Order.Completed:
            return "Completed"
        elif status is Order.Canceled:
            return "Cancelled"
        elif status is Order.Rejected:
            return "Rejected"
        elif status is Order.Expired:
            return "Expired"
        else:
            return "Unknown status: %s" % status


class Encoder(json.JSONEncoder):
    def default(self, obj):
        attr = ""
        try:
            attr = json.JSONEncoder.default(self, obj)
        except Exception:
            print("could not serialize: %s" % obj)
            attr = "--error-serializing--"
        finally:
            return attr