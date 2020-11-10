import math


def my_compare_float(float1, float2, prec=6):
    """ Comparamos 2 float con un minimos de precision.
    True si son igual - else false
    """
    if float1 and float2:
        return abs(float1 - float2) <= (1 / 10 ** prec)
    else:
        return float1 == float2


def get_data_value(data, level):
    value = None
    if hasattr(data, level):
        value = getattr(data, level)[0]
        if math.isnan(value):
            value = None
        else:
            value = round(value, 6)
    return value


def is_better(new_px, px, side):
    if side == Order.Buy:
        return new_px > px
    elif side == Order.Sell:
        return new_px < px
    return None


def round_qty(qty, min_size):
    final = qty // min_size * min_size
    extra = qty - final
    if extra > (min_size / 2):
        return final + min_size
    else:
        return final
