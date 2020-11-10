import time
from src.arqLogger import ArquantLogger
from arquants import Strategy, OrderLimit, Settle, MarketData, Trade

data1 = MarketData("GGAL - 48hs", 1, 1, 0.05, Settle.S_48)
data2 = MarketData("AY24 - CI", 100, 1, 0.5, Settle.S_CI)
order = OrderLimit(100.2, 50, 0, data1)
order.executed.exbits.append(Trade(order.price, 50))


def start_client(param1=10, param2=20, param3="valor3"):
   params_list = locals()
   stgy = Strategy()
   client = ArquantLogger("ws://localhost:8001/", stgy, "Testing", "bono usd vs ars", params_list)
   client.connect()

   # MSG 1
   client.log_strategy({"description": "Testing logging"})
   time.sleep(2)
   # MSG 2
   client.log_new_order_response(order, {"additional1": "strategy tasa 1", "additional2": 0})
   time.sleep(1)
   client.log_cancel_order_response(order, {"additional1": "strategy tasa 1", "additional2": 0})
   client.log_replace_order_response(order, {"additional1": "strategy tasa 1", "additional2": 0})

   time.sleep(3)
   # MSG 3
   client.log_md_event([data1, data2], [["bid_px", "bid_qty"], ["offer_px", "offer_qty"]], {"additional1": "strategy tasa 1", "additional2": 0})
   client.log_er_event(order, {"additional1": "strategy tasa 1", "additional2": 0})
   time.sleep(2)
   client.log_internal_event("description of internal", {"additional1": "strategy tasa 1", "additional2": 0})
   client.log_pause_event("description of pause", {"additional1": "strategy tasa 1", "additional2": 0})
   client.log_error_event("description of error", {"additional1": "strategy tasa 1", "additional2": 0})

   time.sleep(1000)
   client.close_connection()


if __name__ == '__main__':
   start_client()
   print("finalizing")