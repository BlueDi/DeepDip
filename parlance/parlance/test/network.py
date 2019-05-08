r'''Test cases for Parlance network activity
    Copyright (C) 2004-2008  Eric Wald
    
    This module includes functional (end-to-end) test cases to verify that the
    whole system works together; unfortunately, many of them can take quite
    a while to run, and a few need bots that can actually finish a game.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import socket
import unittest
from itertools       import count
from struct          import pack
from time            import sleep

from parlance.config    import VerboseObject
from parlance.functions import any
from parlance.language  import Representation, Token, protocol
from parlance.main      import ThreadManager
from parlance.network   import Client, Connection, ServerSocket
from parlance.player    import Clock, HoldBot
from parlance.server    import Server
from parlance.tokens    import ADM, BRA, HLO, IAM, KET, NME, REJ, YES

from parlance.test.server import ServerTestCase

class NetworkTestCase(ServerTestCase):
    class Disconnector(ServerTestCase.Fake_Player):
        sleep_time = 14
        name = 'Loose connection'
        def handle_message(self, message):
            self.__super.handle_message(message)
            if message[0] is HLO:
                self.manager.add_timed(self, self.sleep_time)
            elif message[0] is REJ:
                raise UserWarning("Rejected command: " + str(message))
        def run(self):
            self.send(ADM(str(self.power))('Passcode: %d' % self.pcode))
            self.close()
    class FakeClient(Client):
        ''' A fake Client to test the server timeout.'''
        is_server = False
        prefix = 'Fake Client'
        error_code = None
        
        def open(self):
            # Open the socket
            self.sock = sock = socket.socket()
            sock.connect((self.options.host or 'localhost', self.options.port))
            sock.settimeout(None)
            
            if self.pclass:
                # Send initial message
                self.log_debug(9, 'Sending Initial Message')
                self.send_dcsp(self.IM, pack('!HH',
                    self.proto.version, self.proto.magic))
            
            return True
        def run(self):
            if self.pclass: self.__super.run()
            else: self.read()
        def send_error(self, code, from_them=False):
            if from_them: self.error_code = code
            self.__super.send_error(code, from_them)
    
    port = count(16714)
    
    def setUp(self):
        ServerTestCase.setUp(self)
        self.set_verbosity(0)
        self.manager = ThreadManager()
        self.manager.wait_time = 10
        self.manager.pass_exceptions = True
    def connect_server(self, clients, games=1, poll=True, **kwargs):
        self.set_option('games', games)
        self.set_option('port', self.port.next())
        
        manager = self.manager
        sock = ServerSocket(Server, manager)
        if not poll: sock.polling = None
        if sock.open():
            self.server = server = sock.server
        else: raise UserWarning('ServerSocket failed to open')
        if not server: raise UserWarning('ServerSocket lacks a server')
        manager.add_polled(sock)
        for dummy in range(games):
            if server.closed: raise UserWarning('Server closed early')
            players = []
            for player_class in clients:
                player = manager.add_client(player_class, **kwargs)
                if not player:
                    raise UserWarning('Manager failed to start a client')
                players.append(player)
                manager.process()
            while any(not p.closed for p in players):
                manager.process(23)
    def fake_client(self, player_class):
        name = player_class and player_class.__name__ or str(player_class)
        client = self.FakeClient(player_class)
        result = client.open()
        if result: self.manager.add_polled(client)
        else: raise UserWarning('Failed to open a Client for ' + name)
        return result and client

class Network_Errors(NetworkTestCase):
    def test_timeout(self):
        ''' Thirty-second timeout for the Initial Message'''
        self.failUnlessEqual(protocol.Timeout, 0x01)
        self.connect_server([])
        client = self.fake_client(None)
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.Timeout)
    def test_initial(self):
        ''' Client's first message must be Initial Message.'''
        self.failUnlessEqual(protocol.NotIMError, 0x02)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.DM, '')
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.NotIMError)
    def test_endian(self):
        ''' Integers must be sent in network byte order.'''
        self.failUnlessEqual(protocol.EndianError, 0x03)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM,
                pack('<HH', protocol.version, protocol.magic))
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.EndianError)
    def test_endian_short(self):
        ''' Length must be sent in network byte order.'''
        self.failUnlessEqual(protocol.EndianError, 0x03)
        self.connect_server([])
        client = self.fake_client(None)
        client.sock.sendall(pack('<BxHHH', client.IM, 4,
            protocol.version, protocol.magic))
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.EndianError)
    def test_magic(self):
        ''' The magic number must match.'''
        self.failUnlessEqual(protocol.MagicError, 0x04)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM, 'None')
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.MagicError)
    def test_version(self):
        ''' The server must recognize the protocol version.'''
        self.failUnlessEqual(protocol.VersionError, 0x05)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM,
                pack('!HH', protocol.version + 1, protocol.magic))
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.VersionError)
    def test_duplicate(self):
        ''' The client must not send more than one Initial Message.'''
        self.failUnlessEqual(protocol.DuplicateIMError, 0x06)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM,
                pack('!HH', protocol.version, protocol.magic))
        client.send_dcsp(client.IM,
                pack('!HH', protocol.version, protocol.magic))
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.DuplicateIMError)
    def test_server_initial(self):
        ''' The server must not send an Initial Message.'''
        self.failUnlessEqual(protocol.ServerIMError, 0x07)
        # Todo
    def test_type(self):
        ''' Stick to the defined set of message types.'''
        self.failUnlessEqual(protocol.MessageTypeError, 0x08)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM,
                pack('!HH', protocol.version, protocol.magic))
        client.send_dcsp(10, '')
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.MessageTypeError)
    def test_short(self):
        ''' Detect messages chopped in transit.'''
        self.failUnlessEqual(protocol.LengthError, 0x09)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM,
                pack('!HH', protocol.version, protocol.magic))
        client.sock.sendall(pack('!BxH', client.DM, 20) + HLO(0).pack())
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.LengthError)
    def test_quick(self):
        ''' The client should not send a DM before receiving the RM.'''
        self.failUnlessEqual(protocol.EarlyDMError, 0x0A)
        # I don't see a way to trigger this with the current system.
    def test_representation(self):
        ''' The server's first message must be RM.'''
        self.failUnlessEqual(protocol.NotRMError, 0x0B)
        # Todo
    def test_unexpected(self):
        ''' The server must not send an unrequested RM.'''
        self.failUnlessEqual(protocol.UnexpectedRM, 0x0C)
        # Todo
    def test_client_representation(self):
        ''' The client must not send Representation Messages.'''
        self.failUnlessEqual(protocol.ClientRMError, 0x0D)
        self.connect_server([])
        client = self.fake_client(None)
        client.send_dcsp(client.IM,
                pack('!HH', protocol.version, protocol.magic))
        self.manager.process()
        client.send_RM()
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.ClientRMError)
    def test_reserved_tokens(self):
        ''' "Reserved for AI use" tokens must never be sent over the wire.'''
        class ReservedSender(object):
            def __init__(self, send_method, **kwargs):
                self.send = send_method
                self.closed = False
            def register(self):
                self.send(Token('HMM', 0x585F)())
            def close(self): self.closed = True
        self.failUnlessEqual(protocol.IllegalToken, 0x0E)
        self.connect_server([])
        client = self.fake_client(ReservedSender)
        self.manager.process()
        self.failUnlessEqual(client.error_code, protocol.IllegalToken)

class Network_Basics(NetworkTestCase):
    def test_full_connection(self):
        ''' Seven fake players, polling if possible'''
        self.connect_server([self.Disconnector] * 7)
    def test_without_poll(self):
        ''' Seven fake players, selecting'''
        self.connect_server([self.Disconnector] * 7, poll=False)
    def test_with_timer(self):
        ''' Seven fake players and an observer'''
        self.connect_server([Clock] + ([self.Disconnector] * 7))
    def test_takeover(self):
        ''' Takeover ability after game start'''
        class Fake_Takeover(VerboseObject):
            ''' A false player, who takes over a position and then quits.'''
            sleep_time = 7
            name = 'Impolite Finisher'
            def __init__(self, send_method, representation,
                    power, passcode, manager=None):
                self.__super.__init__()
                self.log_debug(9, 'Fake player started')
                self.restarted = False
                self.closed = False
                self.send = send_method
                self.rep = representation
                self.power = power
                self.passcode = passcode
            def register(self):
                self.send(NME(self.power.text)(str(self.passcode)))
            def close(self):
                self.log_debug(9, 'Closed')
                self.closed = True
            def handle_message(self, message):
                self.log_debug(5, '<< %s', message)
                if message[0] is YES and message[2] is IAM:
                    self.send(ADM(self.power.text)('Takeover successful'))
                    sleep(self.sleep_time)
                    self.close()
                elif message[0] is REJ and message[2] is NME:
                    self.send(IAM(self.power)(self.passcode))
                elif message[0] is ADM: pass
                else: raise AssertionError, 'Unexpected message: ' + str(message)
        class Fake_Restarter(self.Disconnector):
            ''' A false player, who starts Fake_Takeover after receiving HLO.'''
            sleep_time = 3
            def close(self):
                self.manager.add_client(Fake_Takeover, power=self.power,
                    passcode=self.pcode)
                self.log_debug(9, 'Closed')
                self.closed = True
        self.set_option('takeovers', True)
        self.connect_server([Fake_Restarter] + [self.Disconnector] * 6)
    def test_start_bot_blocking(self):
        ''' Bot-starting cares about the IP address someone connects from.'''
        manager = self.manager
        def lazy_admin(self, line, *args):
            self.queue = []
            self.send(ADM(self.name)(str(line) % args))
            manager.process()
            return [msg.fold()[2][0] for msg in self.queue if msg[0] is ADM]
        self.connect_server([])
        self.Fake_Master.admin = lazy_admin
        master = self.connect_player(self.Fake_Master)
        self.connect_player(self.Fake_Player)
        master.admin('Server: become master')
        self.assertContains('Recruit more players first, or use your own bots.',
                master.admin('Server: start holdbot'))
    def test_unpack_message(self):
        ''' Former docstring tests from Connection.unpack_message().'''
        c = Connection()
        c.rep = Representation({0x4101: 'Sth'}, c.proto.base_rep)
        msg = [HLO.number, BRA.number, 0x4101, KET.number]
        unpacked = c.unpack_message(pack('!HHHH', *msg))
        self.failUnlessEqual(repr(unpacked),
            "Message([HLO, [Token('Sth', 0x4101)]])")

class Network_Full_Games(NetworkTestCase):
    def test_holdbots(self):
        ''' Seven drawing holdbots'''
        self.connect_server([HoldBot] * 7)
    def test_two_games(self):
        ''' seven holdbots; two games'''
        self.connect_server([HoldBot] * 7, 2)
        self.failUnlessEqual(len(self.server.games), 2)

if __name__ == '__main__': unittest.main()
