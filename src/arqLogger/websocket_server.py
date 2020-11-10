from datetime import datetime

from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from twisted.internet import reactor


def log(msg):
    print("{}: {}".format(str(datetime.now()), msg))


class LoggerServer(WebSocketServerProtocol):
    """Dummy websocket protocol"""
    def __init__(self, on_message):
        super(LoggerServer, self).__init__()
        self.on_message = on_message

    def onConnect(self, request):
        log("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        log("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            log("Binary message received: {0} bytes".format(len(payload)))
        else:
            message = payload.decode('utf8')
            self.on_message(message)

    def onClose(self, wasClean, code, reason):
        log("WebSocket connection closed: {}".format(reason))

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)


class WsProtocolFactory(WebSocketServerFactory):

    def __init__(self, on_message):
        super(WsProtocolFactory, self).__init__()
        self.on_message = on_message

    def buildProtocol(self, *args, **kwargs):
        protocol = LoggerServer(self.on_message)
        protocol.factory = self
        return protocol


def start_websocket(port, on_message):
    factory = WsProtocolFactory(on_message)
    # factory.setProtocolOptions(maxConnections=2)
    reactor.listenTCP(port, factory)
    reactor.run()


