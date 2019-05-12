# load additional Python module
import errno
import logging
import os
import socket
import socketserver
import sys
import typing
from threading import Thread


logger = logging.getLogger(__name__)


class DiplomacyThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self, port, host='localhost'):
        self.port = port
        self.host = host
        self.address = (self.host, self.port)

        # bind_and_activate means that the constructor will bind and activate the server right away
        # Because we want to set up the reuse address flag, this should not be the case, and we bind and activate
        # manually
        super(DiplomacyThreadedTCPServer, self).__init__(self.address, DiplomacyTCPHandler, bind_and_activate=False)
        self.allow_reuse_address = True
        self.server_bind()
        self.server_activate()
        logger.info("Server bound and activated at address: {}".format(self.server_address))


    def shutdown(self):
        super().shutdown()
        logger.info("Shutting down server.")


class DiplomacyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def recv_all(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = self.request.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data


    def handle(self):
        while True:
            data_length_bytes: bytes = self.recv_all(4)

            # If recv read an empty request b'', then client has closed the connection
            if not data_length_bytes:
                break

            # DON'T DO strip() ON THE DATA_LENGTH PACKET. It might delete what Python thinks is whitespace but
            # it actually is a byte that makes part of the integer.
            data_length: int = int.from_bytes(data_length_bytes, byteorder='big')

            # Don't do strip() on data either (be sure to check if there is some error if you do use)
            data: bytes = self.recv_all(data_length)

            if self.server.handler is not None:
                response: bytes = self.server.handler(bytearray(data))
            else:
                logger.warning("The handler for the message received is None in DiplomacyTCPHandler. Assuming it's for debug reasons. "
                               "Otherwise, fix.")
                response: bytes = data.upper()

            self.request.sendall(len(response).to_bytes(4, byteorder='big'))
            self.request.sendall(response)

