from datetime import datetime
from .enums import EventTypes, LogTypes, ResponseTypes
from .exceptions import DataException


class Log:
    def __init__(self, id, strategy_id, execution_id, client_id, log_type, additional):
        self.id = id
        self.strategy_id = strategy_id
        self.execution_id = execution_id
        self.client_id = client_id
        self.type = log_type
        self.timestamp = datetime.now().timestamp()
        if additional:
            if isinstance(additional, dict):
                for k, v in additional.items():
                    self.__setattr__(k, v)
            else:
                raise DataException("invalid additional type: %s. Parameter 'additional' must be an instance of dict." % type(additional))


class EventLog(Log):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, event_type, additional):
        super().__init__(id, strategy_id, execution_id, client_id, LogTypes.Event.value, additional)
        self.event_id = event_id
        self.event_type = event_type


class ResponseLog(Log):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, response_type, additional):
        super().__init__(id, strategy_id, execution_id, client_id, LogTypes.Response.value, additional)
        self.event_id = event_id
        self.response_type = response_type


class StrategyLog(Log):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, data):
        super().__init__(id, strategy_id, execution_id, client_id, LogTypes.Own.value, None)
        self.event_id = event_id
        for k, v in data.items():
            self.__setattr__(k, v)


class NewOrderResponseLog(ResponseLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, order_id, side, px, qty, instrument, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, ResponseTypes.NewOrder.value, additional)
        self.order_id = order_id
        self.side = side
        self.px = px
        self.qty = qty
        self.instrument = instrument


class CancelOrderResponseLog(ResponseLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, order_id, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, ResponseTypes.CancelOrder.value, additional)
        self.order_id = order_id


class ReplaceOrderResponseLog(ResponseLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, order_id, side, new_px, new_qty, instrument, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, ResponseTypes.ReplaceOrder.value, additional)
        self.order_id = order_id
        self.side = side
        self.new_px = new_px
        self.new_qty = new_qty
        self.instrument = instrument


class MDEventLog(EventLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, md_received, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, EventTypes.MarketData.value, additional)
        self.md_received = md_received


class EREventLog(EventLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, order_id, state, last, rem_size, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, EventTypes.ExecReport.value, additional)
        self.order_id = order_id
        self.state = state
        self.last = last
        self.rem_size = rem_size


class PauseEventLog(EventLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, description, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, EventTypes.Pause.value, additional)
        self.description = description


class ErrorEventLog(EventLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, description, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, EventTypes.Error.value, additional)
        self.description = description


class InternalEventLog(EventLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, description, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, EventTypes.Internal.value, additional)
        self.description = description


class InitializeEventLog(EventLog):
    def __init__(self, id, strategy_id, execution_id, client_id, event_id, param_list, additional):
        super().__init__(id, strategy_id, execution_id, client_id, event_id, EventTypes.Initialize.value, additional)

        if param_list:
            if isinstance(param_list, dict):
                for k, v in param_list.items():
                    self.__setattr__(k, v)
            else:
                raise DataException(
                    "invalid param_list type: %s. Parameter 'param_list' must be an instance of dict." % type(
                        param_list))

