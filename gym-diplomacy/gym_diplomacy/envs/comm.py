# load additional Python module
import socket
import errno
import sys
import os
import typing
from threading import Thread

import logging

FORMAT = "%(levelname)-8s -- [%(filename)s:%(lineno)s - %(funcName)10s()] %(message)s"
logging.basicConfig(format=FORMAT)

logging_level = 'DEBUG'
level = getattr(logging, logging_level)
logger = logging.getLogger(__name__)
logger.setLevel(level)


class LocalSocketServer:
    sock = None
    handle: typing.Callable = None
    threads: typing.List[Thread] = []

    terminate: bool = False


    def __init__(self, port, handle):
        self.handle = handle

        # create TCP (SOCK_STREAM) /IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # reuse the socket, meaning there should not be any errno98 address already in use
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # retrieve local hostname
        local_hostname = socket.gethostname()

        # get fully qualified hostname
        local_fqdn = socket.getfqdn()

        # get the according IP address
        ip_address = socket.gethostbyname(local_hostname)

        # output hostname, domain name and IP address
        logger.debug("Socket working on %s (%s) with %s" % (local_hostname, local_fqdn, ip_address))

        # bind the socket to the port given
        server_address = (ip_address, port)

        logger.debug('Socket starting up on %s port %s' % server_address)
        self.sock.bind(server_address)

        # listen for incoming connections (server mode) with one connection at a time
        self.sock.listen(1)


    def threaded_listen(self):
        thread = Thread(target=self._listen)
        self.threads.append(thread)
        thread.start()


    def _listen(self):
        while not self.terminate:
            # wait for a connection
            logger.debug('Waiting for a connection...')
            connection, client_address = self.sock.accept()
            with connection:
                # show who connected to us
                logger.debug('Connection from {}'.format(client_address))

                data = connection.recv(1024 * 20)

                logger.debug("Calling handler...")
                connection.send(self.handle(data))
            
            logger.debug("Connection closed")


    def close(self) -> None:
        logger.info("Closing LocalSocketServer...")

        self.terminate = True
        #self.sock.shutdown(socket.SHUT_RDWR)  # further sends and receives are disallowed
        self.sock.close()

        for thread in self.threads:
            thread.join()

        logger.info("LocalSocketServer terminated.")


def handle_f(request: bytearray):
    return request


def main_f():
    sock = LocalSocketServer(5000, handle_f)
    sock.listen()


if __name__ == "__main__":
    main_f()

