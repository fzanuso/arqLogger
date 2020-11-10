from enum import Enum


class Side(Enum):
    BUY = 0
    SELL = 1


class Req(Enum):
    NEW = 0
    REPLACE = 1
    CANCEL = 2


class Statistics(Enum):
    Amount = 0
    AvgPx = 1
    CumQty = 2
