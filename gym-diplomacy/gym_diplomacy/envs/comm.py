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
        logger.info("Shutting down server.")
        super().shutdown()


class DiplomacyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def recv_all(self, n):
        """Helper function to recv n bytes or return None if EOF is hit"""
        data = b''

        while len(data) < n:
            try:
                packet = self.request.recv(n - len(data))
            except:
                packet = None
            if not packet:
                return None
            data += packet

        return data


    def handle(self):
        """Handles the received data.
        If receives an empty request, then the client closed the connection.
        """
        while True:
            data_length_bytes = self.recv_all(4)

            if not data_length_bytes:
                break

            data_length = int.from_bytes(data_length_bytes, byteorder='big')

            data = self.recv_all(data_length)

            if self.server.handler is not None:
                response = self.server.handler(bytearray(data))
            else:
                logger.warning("The handler for the message received is None in DiplomacyTCPHandler. "
                               "Assuming it's for debug reasons. Otherwise, fix.")
                response = data.upper()

            try:
                self.request.sendall(len(response).to_bytes(4, byteorder='big'))
                self.request.sendall(response)
            except BrokenPipeError:
                break

