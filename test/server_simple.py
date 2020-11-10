from src.arqLogger import start_websocket


# Callable function when message is received by the server
def on_new_log(log):
   print("Text message received: {0}".format(log))


# Simple start sever with port and callable function
start_websocket(8001, on_new_log)
# ws://177.231.134.94:8001/