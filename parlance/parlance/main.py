r'''Parlance command-line interface
    Copyright (C) 2004-2008  Eric Wald
    
    This module includes functions to run players or the server based on
    command-line arguments.  It also includes the threading engine used by the
    back ends of each.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import select
from itertools import chain
from sys       import argv, exit, stdin
from time      import sleep, time

try: from threading import Thread, Lock
except ImportError:
    Thread = None
    from dummy_threading import Lock

from config    import Configuration, VerboseObject, variants
from network   import Client, ServerSocket

__all__ = [
    'ThreadManager',
    'run_player',
    'run_server',
]

class ThreadManager(VerboseObject):
    ''' Manages five types of clients: polled, timed, threaded, dynamic,
        and queued.
        
        Each type of client must have a close() method and corresponding
        closed property.  A client will be removed if it closes itself;
        otherwise, it will be closed when the ThreadManager closes.
        
        Each client must also have a prefix property, which should be a
        string, and a run() method, which is called as described below.
        
        Polled clients have a fileno(), which indicates a file descriptor.
        The client's run() method is called whenever that file descriptor
        has input to process.  In addition, the client is closed when its
        file descriptor runs out of input.  Each file descriptor can only
        support one polled client.
        
        The run() method of a timed client is called after the amount of
        time specified when it is registered.  The specified delay is a
        minimum, not an absolute; polled clients take precedence.
        
        Dynamic clients are like timed clients, but have a time_left() method
        to specify when to call the run() method.  The time_left() method is
        called each time through the polling loop, and should return either
        a number of seconds (floating point is permissible) or None.
        
        The run() method of a threaded client is called immediately in
        a separate thread.  The manager will wait for all threads started
        in this way, during its close() method.
    '''#'''
    flags = (getattr(select, 'POLLIN', 0) |
            getattr(select, 'POLLERR', 0) |
            getattr(select, 'POLLHUP', 0) |
            getattr(select, 'POLLNVAL', 0))
    
    __options__ = (
        ('wait_time', int, 600, 'idle timeout for server loop',
            'Default time (in seconds) to wait for select() or poll() system calls.',
            'Not used when any client or game has a time limit.',
            'Higher numbers waste less CPU time, up to a point,',
            'but may make the program less responsive to certain inputs.'),
        ('sleep_time', int, 1, 'idle timeout for busy loops',
            'Default time (in seconds) to sleep in potential busy loops.',
            'Higher numbers may waste less CPU time in certain situations,',
            'but will make the program less responsive to certain inputs.'),
        ('block_exceptions', bool, True, None,
            'Whether to block exceptions seen by the ThreadManager.',
            'When on, the program is more robust, but harder to debug.'),
        ('autostart', list, [], None,
            'A list of internal clients to start each game.'),
        #('external', list, [], None,
        #    'A list of external programs to start each game.'),
        #('countries', dict, {}, None,
        #    'A mapping of country -> passcode as which to start clients.'),
        #('fill', Player, HoldBot, None,
        #    'An internal client used to fill empty slots each game'),
    )
    
    def __init__(self):
        self.__super.__init__()
        self.log_debug(10, 'Attempting to create a poll object')
        if self.flags:
            try: self.polling = select.poll()
            except: self.polling = None
        else: self.polling = None
        
        self.polled = {}        # fd -> client
        self.timed = []         # (time, client)
        self.threaded = []      # (thread, client)
        self.dynamic = []       # client
        self.queue = []         # client
        self.queue_lock = Lock()
        self.queueing = False
        self.closed = False
    def clients(self):
        return [item[1] for item in chain(self.polled.iteritems(),
                self.timed, self.threaded)] + self.dynamic + self.queue
    
    def run(self):
        ''' The main loop; never returns until the manager closes.'''
        self.log_debug(10, 'Main loop started')
        try:
            while not self.closed:
                if self.clients():
                    self.process(self.options.wait_time)
                    if self.polled or self.timed or self.closed:
                        pass
                    else:
                        # Avoid turning this into a busy loop
                        self.log_debug(7, 'sleep()ing for %.3f seconds',
                                self.options.sleep_time)
                        sleep(self.options.sleep_time)
                else: self.close()
            self.log_debug(11, 'Main loop ended')
        except KeyboardInterrupt:
            self.log_debug(7, 'Interrupted by user')
        except:
            self.log_debug(1, 'Error in main loop; closing')
            self.close()
            raise
        self.close()
    def process(self, wait_time=1):
        ''' Runs as long as there is something productive to do.'''
        method = self.polling and self.poll or self.select
        while not self.closed:
            timeout = self.get_timeout()
            result = False
            if self.polled:
                poll_time = (timeout is None) and wait_time or timeout
                self.log_debug(7, '%s()ing for %.3f seconds',
                        method.__name__, poll_time)
                result = method(poll_time)
            elif timeout:
                self.log_debug(7, 'sleep()ing for %.3f seconds', timeout)
                sleep(timeout)
            if not result:
                if timeout is None: break
                if self.timed: self.check_timed()
                if self.dynamic: self.check_dynamic()
        if self.threaded: self.clean_threaded()
    def attempt(self, client):
        self.log_debug(12, 'Running %s', client.prefix)
        try: client.run()
        except KeyboardInterrupt:
            self.log_debug(7, 'Interrupted by user')
            self.close()
        except Exception, e:
            self.log_debug(1, 'Exception running %s: %s %s',
                    client.prefix, e.__class__.__name__, e.args)
            if not client.closed: client.close()
            if not self.options.block_exceptions: raise
    def close(self):
        self.closed = True
        if self.threaded: self.clean_threaded()
        for client in self.clients():
            if not client.closed: client.close()
        self.wait_threads()
        self.run_queue()
    
    # Polled client handling
    class InputWaiter(VerboseObject):
        ''' File descriptor for waiting on standard input.'''
        def __init__(self, input_handler, close_handler):
            self.__super.__init__()
            self.handle_input = input_handler
            self.handle_close = close_handler
            self.closed = False
        def fileno(self): return stdin.fileno()
        def run(self):
            line = ''
            try: line = raw_input()
            except EOFError: self.close()
            if line: self.handle_input(line)
        def close(self):
            self.closed = True
            self.handle_close()
    def add_polled(self, client):
        self.log_debug(11, 'New polled client: %s', client.prefix)
        assert not self.closed
        fd = client.fileno()
        self.polled[fd] = client
        if self.polling: self.polling.register(fd, self.flags)
    def remove_polled(self, fd):
        # Warning: Must be called in the same thread as the polling.
        # Outside of this class, call the client's close() method instead.
        self.log_debug(11, 'Removing polled client: %s',
                self.polled.pop(fd).prefix)
        if self.polling: self.polling.unregister(fd)
    def add_input(self, input_handler, close_handler):
        ''' Adds a polled client listening to standard input.
            On Windows, adds it as a threaded client instead;
            because select() can't handle non-socket file descriptors.
        '''#'''
        waiter = self.InputWaiter(input_handler, close_handler)
        if self.polling: self.add_polled(waiter)
        else: self.add_looped(waiter)
    def select(self, timeout):
        self.clean_polled()
        try: ready = select.select(self.polled.values(), [], [], timeout)[0]
        except select.error, e:
            self.log_debug(7, 'Select error received: %s', e.args)
            # Bad file descriptors should be caught in the next pass.
            if e.args[0] != 9:
                self.close()
                raise
        else:
            if ready:
                for client in ready:
                    self.attempt(client)
            else: return False
        return True
    def poll(self, timeout):
        self.clean_polled()
        try: ready = self.polling.poll(timeout * 1000)
        except select.error, e:
            self.log_debug(7, 'Polling error received: %s', e.args)
            # Ignore interrupted system calls
            if e.args[0] != 4:
                self.close()
                raise
        else:
            if ready:
                for fd, event in ready:
                    self.check_polled(fd, event)
            else: return False
        return True
    def check_polled(self, fd, event):
        client = self.polled[fd]
        self.log_debug(15, 'Event %s received for %s', event, client.prefix)
        if event & select.POLLIN:
            self.attempt(client)
        if client.closed:
            self.log_debug(7, '%s closed itself', client.prefix)
            self.remove_polled(fd)
        elif event & (select.POLLERR | select.POLLHUP):
            self.log_debug(7, 'Event %s received for %s', event, client.prefix)
            self.remove_polled(fd)
            if not client.closed: client.close()
        elif event & select.POLLNVAL:
            self.log_debug(7, 'Invalid fd for %s', client.prefix)
            self.remove_polled(fd)
            if not client.closed: client.close()
    def clean_polled(self):
        # Warning: This doesn't catch closed players until their Clients close.
        for fd, client in self.polled.items():
            if client.closed: self.remove_polled(fd)
    
    # Timed client handling
    def add_timed(self, client, delay):
        self.log_debug(11, 'New timed client: %s', client.prefix)
        assert not self.closed
        deadline = time() + delay
        self.timed.append((deadline, client))
        return deadline
    def add_dynamic(self, client):
        self.log_debug(11, 'New dynamic client: %s', client.prefix)
        assert not self.closed
        self.dynamic.append(client)
    def get_timeout(self):
        now = time()
        times = [t for t in (client.time_left(now)
                for client in self.dynamic if not client.closed)
                if t is not None]
        when = [t for t,c in self.timed if not c.closed]
        if when: times.append(max(0, 0.005 + min(when) - now))
        if times: result = min(times)
        else: result = None
        return result
    def check_timed(self):
        self.log_debug(14, 'Checking timed clients')
        now = time()
        timed = self.timed
        self.timed = []
        for deadline, client in timed:
            if client.closed:
                self.log_debug(11, 'Removing timed client: %s', client.prefix)
                continue
            if deadline < now: self.attempt(client)
            else: self.timed.append((deadline, client))
    def check_dynamic(self):
        self.log_debug(14, 'Checking dynamic clients')
        now = time()
        removals = []
        for client in self.dynamic:
            if client.closed:
                self.log_debug(11, 'Removing dynamic client: %s', client.prefix)
                removals.append(client)
            elif None is not client.time_left(now) <= 0: self.attempt(client)
        for client in removals: self.dynamic.remove(client)
    
    # Threaded client handling
    class LoopClient(object):
        def __init__(self, client):
            self.client = client
            self.closed = False
        def run(self):
            while not (self.closed or self.client.closed):
                self.client.run()
            self.close()
        def close(self):
            self.closed = True
            if not self.client.close: self.client.close()
        @property
        def prefix(self): return self.client.prefix
    class ThreadClient(object):
        def __init__(self, target, *args, **kwargs):
            self.target = target
            self.args = args
            self.kwargs = kwargs
            self.closed = False
            arguments = chain((repr(arg) for arg in args),
                    ("%s=%r" % (name, value)
                        for name, value in kwargs.iteritems()))
            self.prefix = (target.__name__ + '(' +
                    str.join(', ', arguments) + ')')
        def run(self):
            self.target(*self.args, **self.kwargs)
            self.close()
        def close(self):
            self.closed = True
    def add_threaded(self, client):
        if Thread:
            self.log_debug(11, 'New threaded client: %s', client.prefix)
            assert not self.closed
            thread = Thread(target=self.attempt, args=(client,))
            thread.start()
            self.threaded.append((thread, client))
        else:
            self.log_debug(11, 'Emulating threaded client: %s', client.prefix)
            self.attempt(client)
    def add_looped(self, client):
        self.add_threaded(self.LoopClient(client))
    def new_thread(self, target, *args, **kwargs):
        self.add_threaded(self.ThreadClient(target, *args, **kwargs))
    def add_client(self, player_class, **kwargs):
        name = player_class.__name__
        client = Client(player_class, manager=self, **kwargs)
        result = client.open()
        if result:
            self.add_polled(client)
            self.log_debug(10, 'Opened a Client for ' + name)
        else: self.log_debug(7, 'Failed to open a Client for ' + name)
        return result and client
    def start_clients(self, game_id):
        for klass in self.options.autostart:
            self.add_client(klass, game_id=game_id)
    def wait_threads(self):
        for thread, client in self.threaded:
            while thread.isAlive():
                try: thread.join(self.options.sleep_time)
                except KeyboardInterrupt:
                    if not client.closed: client.close()
                    print 'Still waiting for threads...'
    def clean_threaded(self):
        self.log_debug(14, 'Checking threaded clients')
        self.threaded = [item for item in self.threaded if item[0].isAlive()]
    
    # Queue management
    def enqueue(self, target, *args, **kwargs):
        self.add_queued(ThreadClient(target, args, kwargs))
    def add_queued(self, client):
        assert not self.closed
        self.queue_lock.acquire()
        self.queue.append(client)
        run_queue = not self.queueing
        if run_queue: self.queueing = True
        self.queue_lock.release()
        if run_queue: self.new_thread(self.check_queue)
    def check_queue(self):
        while True:
            try:
                self.queue_lock.acquire()
                if self.queue:
                    client = self.queue.pop(0)
                else:
                    self.queueing = False
                    break
            finally: self.queue_lock.release()
            if client.closed:
                self.log_debug(11, 'Removing queued client: %s', client.prefix)
            else: self.attempt(client)
    def run_queue(self):
        # Called after all threads are done,
        # so we shouldn't have to worry about the lock.
        if self.queue: self.log_debug(11, 'Checking all queued clients')
        for client in self.queue:
            if client.closed:
                self.log_debug(11, 'Removing queued client: %s', client.prefix)
            else: self.attempt(client)

def run_player(player_class, allow_multiple=True, allow_country=True):
    name = player_class.__name__
    num = None
    countries = {}
    
    def usage(problem=None, *args):
        if allow_multiple:
            print 'Usage: %s [host][:port] [number]%s [-v<level>]' % (argv[0],
                    allow_country and ' [power=passcode] ...' or '')
            print 'Connects <number> copies of %s to <host>:<port>' % name
        else:
            print 'Usage: %s [host][:port]%s -v<level>' % (argv[0],
                    allow_country and ' [power=passcode]' or '')
            print 'Connects a copy of %s to <host>:<port>' % name
        if problem: print str(problem) % args
        exit(1)
    
    remainder = Configuration.arguments
    #try: remainder = Configuration.parse_argument_list(argv[1:])
    #except Exception, err: usage(err)
    host = Configuration._args.get('host')
    for arg in remainder:
        if arg.isdigit():
            if not allow_multiple:
                usage('%s does not support multiple copies.', name)
            elif num is None: num = int(arg)
            else: usage()       # Only one number specification allowed
        elif len(arg) > 3 and arg[3] == '=':
            if allow_country: countries[arg[:3].upper()] = int(arg[4:])
            else: usage('%s does not accept country codes.', name)
        elif host is None: Configuration.set_globally('host', arg)
        else: usage()           # Only one host specification allowed
    if num is None: num = 1
    
    manager = ThreadManager()
    while num > 0 or countries:
        num -= 1
        if countries:
            nation, pcode = countries.popitem()
            result = manager.add_client(player_class,
                    power=nation, passcode=pcode)
        else: result = manager.add_client(player_class)
        if not result: manager.log_debug(1, 'Failed to start %s.  Sorry.', name)
    manager.run()

def run_server(server_class, default_verbosity):
    def usage(problem=None, *args):
        print 'Usage: %s [-gGAMES] [-vLEVEL] [VARIANT]' % (argv[0],)
        print 'Serves GAMES games of VARIANT, with output verbosity LEVEL'
        if problem: print str(problem) % args
        exit(1)
    Configuration._args.setdefault('verbosity', default_verbosity)
    opts = {}
    remainder = Configuration.arguments
    #try: remainder = Configuration.parse_argument_list(argv[1:])
    #except: usage()
    if remainder:
        if remainder[0] in variants:
            Configuration.set_globally('variant', remainder[0])
        else: usage('Unknown variant %r', remainder[0])
    manager = ThreadManager()
    server = ServerSocket(server_class, manager)
    if server.open():
        manager.add_polled(server)
        manager.run()
    else: server.log_debug(1, 'Failed to open the server.')

class RawClient(object):
    ''' Simple client to translate DM to and from text.'''
    prefix = 'RawClient'
    def __init__(self, send_method, representation, manager):
        self.send_out  = send_method      # A function that accepts messages
        self.rep       = representation   # The representation message
        self.closed    = False # Whether the connection has ended, or should end
        self.manager   = manager
    def register(self):
        print 'Connected.'
        self.manager.add_input(self.handle_input, self.close)
    def handle_message(self, message):
        ''' Process a new message from the server.'''
        print '>>', message
    def close(self):
        ''' Informs the player that the connection has closed.'''
        print 'Closed.'
        self.closed = True
        if not self.manager.closed: self.manager.close()
    def handle_input(self, line):
        try: message = self.rep.translate(line)
        except Exception, err: print str(err) or '??'
        else: self.send(message)
    def send(self, message):
        if not self.closed: self.send_out(message)

def run():
    r'''Run a raw token client.
        The client will take messages in token syntax from standard input and
        send them to the server, printing any received messages to standard
        output in the same syntax.
    '''#'''
    run_player(RawClient, False, False)
