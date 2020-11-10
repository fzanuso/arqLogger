
class SheetItem:
    def __init__(self, name, price_size, min_size, tick_px, settlement, bid_px=0, bid_qty=0, offer_px=0,
                 offer_qty=0):
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
