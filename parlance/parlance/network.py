r'''Parlance client/server communications
    Copyright (C) 2004-2008  Eric Wald
    
    This module includes classes to send and receive network messages, using
    the Pythonic messages for the interface to other parts of the program.
    This should be the only module that cares about details of the
    client-server protocol.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import socket
from struct    import pack, unpack
from time      import sleep

from config    import VerboseObject
from functions import any
from language  import Message, Representation, protocol
from tokens    import ADM, MDF, OFF, REJ, YES


class SocketWrapper(VerboseObject):
    __options__ = (
        ('host', str, '', None,
            'The name or IP address of the server.',
            'If blank, the server will listen on all possible addresses,',
            'and clients will connect to localhost.'),
        ('port', int, 16713, None,
            'The port that the server listens on.'),
    )
    
    def __init__(self):
        self.__super.__init__()
        self.broken = False  # Whether the write pipe has been broken
        self.closed = False
        self.sock = None
    def close(self):
        if self.sock: self.sock.close()
        self.closed = True
        self.sock = None
    def open(self): raise NotImplementedError
    def run(self):
        ''' Called when we have data to read.'''
        raise NotImplementedError
    def fileno(self): return self.sock.fileno()

class Connection(SocketWrapper):
    ''' Base methods for the DAIDE Client-Server Protocol.'''
    is_server = NotImplemented
    __options__ = (
        ('echo_final', bool, False, 'send unnecessary final messages',
            'Whether to send FM after receiving EM or FM.',
            'The extra FM may be useful to terminate input loops,',
            'particularly when using threads, but the protocol prohibits it.'),
        ('null_rm', bool, False, 'send empty representation messages',
            'Whether to send an empty RM for the standard map.',
            'The standard says yes, but that may be changed soon.'),
    )
    
    def __init__(self):
        self.__super.__init__()
        self.send_final = True
        self.proto = protocol
        self.timer = None
        self.rep = None
        
        # IM, DM, FM, etc.
        for name, value in self.proto.message_types.iteritems():
            setattr(Connection, name[0] + 'M', value)
        
        if self.is_server:
            self.first = self.IM
        else: self.first = self.RM
    def close(self):
        if self.timer: self.timer.close()
        if self.send_final: self.send_dcsp(self.FM, '')
        self.send_final = False
        self.__super.close()
    
    # Incoming messages
    def read(self):
        if self.closed or not self.sock:
            self.log_debug(7, 'Reading while closed')
            return None
        try:
            header = self.sock.recv(4)
            if header and self.sock:
                msg_type, msg_len = unpack('!BxH', header)
                if msg_len: message = self.sock.recv(msg_len)
                else:       message = ''
                if len(message) < msg_len:
                    if len(message) == unpack('<H', pack('>H', msg_len))[0]:
                        self.send_error(self.proto.EndianError)
                    else: self.send_error(self.proto.LengthError)
                else: return self.process_message(msg_type, message)
            else:
                self.log_debug(7, 'Received empty packet')
                self.close()
        except socket.error, e:
            # Ignore 'Resource temporarily unavailable' errors
            # Anything else is probably a bad connection
            if e.args[0] == 11:
                self.log_debug(13, 'Ignoring socket error %s', e.args)
            else:
                self.log_debug(1, 'Socket error %s', e.args)
                # Should I disable the final message in this case?
                self.close()
        return None
    def process_message(self, type_code, data):
        ''' Processes a single DCSP message from the server.'''
        self.log_debug(13, 'Message type %d received', type_code)
        message = None
        first = self.first
        self.first = None
        if self.timer: self.timer.close()
        if first is not None and type_code not in (first, self.FM, self.EM):
            if self.is_server:     self.send_error(self.proto.NotIMError)
            else:                  self.send_error(self.proto.NotRMError)
        elif type_code == self.IM:
            if not self.is_server: self.send_error(self.proto.ServerIMError)
            elif first is None:    self.send_error(self.proto.DuplicateIMError)
            else:                  self.process_IM(data)
        elif type_code == self.RM:
            if self.is_server:     self.send_error(self.proto.ClientRMError)
            elif len(data) % 6:    self.send_error(self.proto.LengthError)
            #elif self.rep:         self.send_error(self.proto.UnexpectedRM)
            else:                  self.read_representation(data)
        elif type_code == self.DM:
            if not data:           self.send_error(self.proto.LengthError)
            elif len(data) % 2:    self.send_error(self.proto.LengthError)
            elif self.rep:         message = self.unpack_message(data)
            else:                  self.send_error(self.proto.EarlyDMError)
        elif type_code == self.FM:
            self.send_final = self.options.echo_final
            self.close()
        elif type_code == self.EM:
            if len(data) == 2:     self.send_error(unpack('!H', data)[0], True)
            else:                  self.send_error(self.proto.LengthError)
        else:
            self.log_debug(7, 'Unknown message type %s received', type_code)
            self.send_error(self.proto.MessageTypeError)
        return message
    def process_IM(self, data):
        ''' Verifies the Initial Message from the client.'''
        if len(data) == 4:
            (version, magic) = unpack('!HH', data)
            if magic == self.proto.magic:
                if version == self.proto.version: self.send_RM()
                else: self.send_error(self.proto.VersionError)
            elif unpack('<HH', data)[1] == self.proto.magic:
                self.send_error(self.proto.EndianError)
            else: self.send_error(self.proto.MagicError)
        else: self.send_error(self.proto.LengthError)
    def read_representation(self, data):
        ''' Creates a representation dictionary from the RM.
            This dictionary maps names to numbers and vice-versa.
        '''#'''
        if data:
            rep = {}
            while len(data) >= 6:
                num, name = unpack('!H3sx', data[:6])
                rep[num] = name
                data = data[6:]
            self.rep = Representation(rep, self.proto.base_rep)
        else: self.rep = self.proto.default_rep
    def unpack_message(self, data):
        ''' Produces a Message from a string of token numbers.
            Uses values in the representation, if available.
        '''#'''
        try:
            result = Message([self.rep[x]
                for x in unpack('!' + 'H'*(len(data)//2), data)])
        except ValueError:
            # Someone foolishly chose to disconnect over an unknown token.
            self.send_error(self.proto.IllegalToken)
            result = None
        else:
            # Tokens in the "Reserved for AI use" category
            # must never be sent over the wire.
            if any('Reserved' in token.category_name() for token in result):
                self.send_error(self.proto.IllegalToken)
                result = None
        return result
    
    # Outgoing messages
    def write(self, message): self.send_dcsp(self.DM, message.pack())
    def send_error(self, code, from_them=False):
        if self.is_server: them = 'Client'; us = 'Server'
        else:              them = 'Server'; us = 'Client'
        
        text = self.proto.error_strings.get(code)
        if text:
            if from_them: faulty = us
            else: faulty = them; self.send_dcsp(self.EM, pack('!H', code))
            self.log_debug(8, '%s error (%s)', faulty, text)
        else:
            if from_them: sender = them + ' sent'
            else:         sender = us + ' trying to send'
            self.log_debug(7, '%s unknown error "%s"', sender, code)
        
        # Terminate the connection
        self.send_final = self.options.echo_final
        self.close()
    def send_RM(self):
        ''' Sends the representation message to the client.
            This implementation can be configured to always sends a full RM,
            or to rely on the default for the Standard map.
        '''#'''
        if self.options.null_rm and self.rep == self.proto.default_rep:
            data = ''
        else:
            data = str.join('', (pack('!H3sx', token.number, name)
                        for name, token in self.rep.items()))
        self.send_dcsp(self.RM, data)
    def send_dcsp(self, msg_type, data):
        ''' Sends a DCSP message to the client.
            msg_type must be an integer, one of the defined message types.
            data must be a packed binary string.
        '''#'''
        if self.sock and not self.broken:
            self.log_debug(13, 'Sending message type %d', msg_type)
            try: self.sock.sendall(pack('!BxH', msg_type, len(data)) + data)
            except socket.error, e:
                # Don't close here, because there may be more to receive
                self.log_debug(7, 'Socket error while sending %s', e.args)
                self.send_final = False
                self.broken = True
        else: self.log_debug(7, 'Trying to send on a closed connection')

class Client(Connection):
    ''' Connects an internal Player to a server on the network.'''
    is_server = False
    def __init__(self, player_class, **kwargs):
        'Initializes instance variables'
        self.__super.__init__()
        self.pclass = player_class
        self.kwargs = kwargs
        self.player = None
    def prefix(self):
        return (self.player and self.player.prefix
                or self.pclass.__name__) + ' Client'
    prefix = property(fget=prefix)
    
    def send(self, msg):
        self.log_debug(5, '>> %s', msg)
        self.write(msg)
    
    def open(self):
        # Open the socket
        self.sock = sock = socket.socket()
        
        # Todo: Check for error 111 (Connection refused)
        port = (self.options.host or 'localhost', self.options.port)
        self.log_debug(17, 'Connecting to %s:%d...', *port)
        sock.connect(port)
        sock.settimeout(None)
        
        # Required by the DCSP document
        try: sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except: self.log_debug(7, 'Could not set SO_KEEPALIVE')
        
        # Send initial message
        self.log_debug(9, 'Sending Initial Message')
        self.send_dcsp(self.IM, pack('!HH',
            self.proto.version, self.proto.magic))
        
        return True
    def run(self):
        ''' Reads a message from the socket.
            Meant to be called by a ThreadManager.
            Checks first to see if it has a representation yet.
        '''#'''
        msg = self.read()
        
        # Wait for representation message
        if msg and not self.rep:
            self.log_debug(7, 'DM while waiting for RM: ' + str(msg))
        elif self.rep and not self.player:
            self.log_debug(9, 'Representation received')
            self.player = self.pclass(send_method=self.send,
                    representation=self.rep, **self.kwargs)
            self.player.register()
        if self.player:
            if msg: self.player.handle_message(msg)
            if self.player.closed: self.close()
    def close(self):
        if self.player and not self.player.closed: self.player.close()
        self.__super.close()

class Service(Connection):
    ''' Connects a network player to the internal Server.'''
    is_server = True
    class TimeoutMonitor(object):
        def __init__(self, service):
            self.service = service
            self.closed = False
            self.prefix = 'IM Check for ' + service.prefix
        def run(self):
            if not self.service.closed:
                self.service.send_error(self.service.proto.Timeout)
        def close(self):
            self.closed = True
    
    def __init__(self, client_id, connection, address, server):
        self.__super.__init__()
        self.sock      = connection
        self.client_id = client_id
        self.address   = address
        self.country   = None
        self.name      = None
        self.version   = None
        self.guesses   = 0
        self.mastery   = False
        self.booted    = False
        self.server    = server
        self.errors    = 0
        self.game      = server.default_game()
        self.rep       = self.game.variant.rep
        self.prefix    = 'Service #%d (%s)' % (client_id, self.game.game_id)
        
        server.add_client(self)
    def power_name(self):
        return self.country and str(self.country) or ('#' + str(self.client_id))
    def full_name(self):
        return (self.name and ('%s (%s)' % (self.name, self.version))
                or 'An observer')
    def run(self):
        msg = self.read()
        if msg:
            self.log_debug(4, '%3s >> %s', self.power_name(), msg)
            try: self.server.handle_message(self, msg)
            except Exception, e:
                self.log_debug(1, '%s handling "%s": %s',
                        e.__class__.__name__, msg, e)
                self.server.broadcast_admin('An error has occurred.  '
                        'The server may be unreliable until it is restarted.')
                self.errors += 1
                if self.errors > 3:
                    self.admin("You have caused too much trouble.  Good-bye.")
                    self.boot()
                else: self.admin("Please don't do that again, whatever it was.")
    def close(self):
        if not self.closed:
            self.closed = True
            self.game.disconnect(self)
            self.server.disconnect(self)
            self.__super.close()
    def boot(self):
        ''' Forcibly disconnect a client, for misbehaving or being replaced.'''
        self.log_debug(6, 'Booting client #%d', self.client_id)
        self.send(+OFF)
        self.booted = self.country
        self.country = None
        self.close()
    def change_game(self, new_game):
        self.game.disconnect(self)
        self.game = new_game
        representation = new_game.variant.rep
        if representation != self.rep:
            self.rep = representation
            self.send_RM()
        self.prefix = 'Service #%d (%s)' % (self.client_id, new_game.game_id)
    def start_timer(self, manager):
        self.timer = self.TimeoutMonitor(self)
        manager.add_timed(self.timer, 30)
    
    def send(self, message):
        if message[0] is MDF: text = 'MDF [...]'
        else: text = str(message)
        self.log_debug(3, '%3s << %s', self.power_name(), text)
        self.write(message)
    def send_list(self, message_list):
        for msg in message_list: self.send(msg)
    def accept(self, message): self.send(YES(message))
    def reject(self, message): self.send(REJ(message))
    def admin(self, line, *args): self.send(ADM('Server')(str(line) % args))

class ServerSocket(SocketWrapper):
    def __init__(self, server_class, thread_manager):
        self.__super.__init__()
        self.server = None
        self.server_class = server_class
        self.manager = thread_manager
        self.next_id = 0
    def open(self):
        ''' Start listening for clients on the specified address.
            May throw exceptions for bad host/port combinations.
        '''#'''
        # Initialize a new socket
        wait_time = .125
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (self.options.host, self.options.port)
        while True:
            try: sock.bind(addr)
            except socket.error, e:
                if e.args[0] == 98:
                    self.log_debug(1, 'Waiting for port %s:%d' % addr)
                    sleep(wait_time)
                    wait_time *= 2
                else: raise e
            else: break
        self.log_debug(6, 'Listening on port %s:%d' % addr)
        sock.setblocking(False)
        sock.listen(7)
        self.sock = sock
        self.server = self.server_class(self.manager)
        return bool(sock and self.server)
    def close(self):
        self.closed = True
        if self.server and not self.server.closed: self.server.close()
        if not self.manager.closed: self.manager.close()
        self.__super.close()
    def run(self):
        ''' Attempts to connect one new network player'''
        try: conn, addr = self.sock.accept()
        except socket.error: pass
        else:
            self.log_debug(6, 'Connection from %s as client #%d',
                    addr, self.next_id)
            
            # Required by the DCSP document
            try: conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            except: self.log_debug(7, 'Could not set SO_KEEPALIVE')
            conn.setblocking(False)
            service = Service(self.next_id, conn, addr[0], self.server)
            service.start_timer(self.manager)
            self.manager.add_polled(service)
            self.next_id += 1

class RawServer(object):
    ''' Simple server to translate DM to and from text.'''
    class FakeGame(object):
        def __init__(self, server):
            self.variant = server
            self.game_id = 'ID'
        def disconnect(self, client):
            print 'Client #%d has disconnected.' % client.client_id
    def __init__(self, thread_manager):
        self.closed = False
        self.manager = thread_manager
        self.clients = {}
        self.rep = protocol.default_rep
        self.game = self.FakeGame(self)
        thread_manager.add_input(self.handle_input, self.close)
        print 'Waiting for connections...'
    def handle_message(self, client, message):
        ''' Process a new message from the client.'''
        print '#%d >> %s' % (client.client_id, message)
    def close(self):
        ''' Informs the user that the connection has closed.'''
        self.closed = True
        if not self.manager.closed: self.manager.close()
    def add_client(self, client):
        self.clients[client.client_id] = client
    def disconnect(self, client):
        del self.clients[client.client_id]
        if not self.clients: self.close()
    def handle_input(self, line):
        try: message = self.rep.translate(line)
        except Exception, err: print str(err) or '??'
        else:
            for client in self.clients.values(): client.write(message)
    def broadcast_admin(self, text): pass
    def default_game(self): return self.game

def run():
    r'''Run a raw token server.
        The server will take messages in token syntax from standard input and
        send them to each connected client, printing any received messages to
        standard output in the same syntax.  The server will close when the
        last client disconnects.
    '''#'''
    from main import run_server
    run_server(RawServer, 0)
