from enum import Enum


class Side:
    Buy = 0
    Sell = 1


class Order:
    Created = 0
    Submitted = 1
    Accepted = 2
    Partial = 3
    Completed = 4
    Canceled = 5
    Expired = 6
    Margin = 7
    Rejected = 8


class LogTypes(Enum):
    Event = "EV"
    Response = "RE"
    Own = "PR"


class EventTypes(Enum):
    Initialize = "INI"
    MarketData = "MD"
    ExecReport = "OR"
    Pause = "PA"
    Error = "ER"
    Internal = "INT"


class ResponseTypes(Enum):
    NewOrder = "NO"
    CancelOrder = "CO"
    ReplaceOrder = "RO"

