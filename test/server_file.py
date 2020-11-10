import logging
from src.arqLogger import start_websocket
from datetime import datetime
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("Rotating Log")
logger.setLevel(logging.INFO)

# add a rotating handler
handler = RotatingFileHandler("arquants.log", maxBytes=1000000, backupCount=5)
logger.addHandler(handler)


def on_new_log(log):
    logger.info("%s - %s" % (datetime.now(), log))


start_websocket(8001, on_new_log)
