r'''Parlance game server
    Copyright (C) 2004-2008  Eric Wald
    
    This module contains the main server, which serves any number of games
    over the network.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import re
from os         import path
from random     import randint, shuffle
from time       import time

from config     import GameOptions, VerboseObject, bots, variants
from functions  import defaultdict, expand_list, \
        instances, num2name, s, timestamp, version_string
from gameboard  import Turn
from language   import Message, Time, protocol
from player     import HoldBot
from tokens     import *
from validation import Validator

class Command(object):
    def __init__(self, pattern, callback, help):
        self.pattern = re.compile(pattern)
        self.command = callback
        self.description = help
class DelayedAction(object):
    def __init__(self, action, veto_action, veto_line, terms, delay, *args):
        self.callback = action
        self.veto_callback = veto_action
        self.veto_line = veto_line
        self.terms = terms
        self.args = args
        self.when = time() + delay
    def veto(self, client):
        ''' Cancels the action, calling the veto action if it was given.
            The veto callback may return a true value to block the cancellation,
            which should be a string explaining why it was blocked.
        '''#'''
        block = self.veto_callback and self.veto_callback(client, *self.args)
        if block:
            client.admin(block)
        else:
            if self.veto_line:
                client.game.admin('%s has vetoed %s',
                        client.full_name(), self.veto_line)
            client.game.actions.remove(self)
    def call(self):
        if self.callback: self.callback(*self.args)

class Server(VerboseObject):
    ''' Coordinates messages between clients and the games,
        administering socket connections and game creation.
    '''#'''
    __options__ = (
        ('games', int, 0, ('g', 'number of games'),
            'Minimum number of games to play before server stops.',
            'Use 0 to prevent the server from shutting down automatically.'),
        ('variant', str, 'standard', 'default variant',
            'The map to use for games not started with the "start <variant> game" command.',
            "This should be the variant's DAIDE name as specified in the variants file."),
        ('log_games', bool, False, 'record completed games',
            'Whether to save game logs to disk and delete them from memory.',
            'If this is on, games will be saved with a .dpp extension,',
            'in the directory indicated by log_path (below).',
            'However, the server will stop reporting them in game listings.'),
        ('log_path', file, path.join('log', 'games'), 'game log directory',
            'The directory in which to save game logs.'),
        
        # Admin messages
        ('snd_admin', bool, True, 'send admin messages',
            'Whether the server should broadcast admin messages.',
            'This includes server-generated and forwarded messages,',
            'but not individual responses to admin commands.'),
        ('fwd_admin', bool, True, 'forward admin messages',
            'Whether non-command admin messages from clients should be re-broadcast.'),
        ('admin_cmd', bool, True, 'accept admin commands',
            'Whether the server should accept admin commands.',
            'These allow players to do things outside the scope of DAIDE syntax,',
            'such as pausing the game, starting bots, or booting each other.'),
    )
    
    def __init__(self, thread_manager):
        ''' Initializes instance variables, including:
            - manager       The ThreadManager instance in charge of the program
            - clients       client_id -> Service for all connected clients
            - games         game_id -> Historian for currently hosted games
            - default       A list of Games that could be joined automatically
            - started_games The number of games that have been started
        '''#'''
        self.__super.__init__()
        self.manager   = thread_manager
        self.clients   = {}
        self.games     = {}
        self.default   = []
        self.closed    = False
        self.started_games = 0
        if not self.start_game():
            self.log_debug(1, 'Unable to start default variant')
            self.close()
    def filename(self, game_id):
        fname = game_id + path.extsep + 'dpp'
        return path.join(self.options.log_path, fname)
    
    def add_client(self, client):
        self.clients[client.client_id] = client
    def disconnect(self, client):
        del self.clients[client.client_id]
        if not self.clients: self.check_close()
    def check_close(self):
        ''' Closes the server if all requested games have been completed.
            Meant to be called when the last client disconnects.
        '''#'''
        open_games = False
        for game_id, game in self.games.items():
            if game.closed:
                if game.saved:
                    # Remove saved games from memory
                    del self.games[game_id]
            else: open_games = True
        if not open_games:
            # Check whether the server itself should close
            if 0 < self.options.games <= self.started_games:
                self.log_debug(11, 'Completed all requested games')
                self.close()
            else: self.start_game()
    def archive(self, game):
        if not self.options.log_games: return
        fname = self.filename(game.game_id)
        try:
            saved = open(fname, 'w')
            game.save(saved)
            saved.close()
        except IOError, err:
            self.log_debug(7, 'Unable to save %s: %s', fname, err)
        else:
            self.log_debug(7, '%s archived in %s', game.prefix, fname)
    
    def broadcast(self, message):
        self.log_debug(2, 'ALL << %s', message)
        for client in self.clients.values(): client.write(message)
    def broadcast_admin(self, text):
        if self.options.snd_admin: self.broadcast(ADM('Server')(text))
    
    def handle_message(self, client, message):
        'Processes a single message from any client.'
        reply = client.game.validator.validate_client_message(message)
        if reply: client.send(reply)
        else:
            method_name = 'handle_'+message[0].text
            # Special handling for common prefixes
            if message[0] in (YES, REJ, NOT):
                method_name += '_' + message[2].text
            
            handlers = [self, client.game, client.game.judge]
            for item in handlers:
                method = getattr(item, method_name, None)
                if method: method(client, message); break
            else:
                self.log_debug(7, 'Missing message handler: %s', method_name)
                client.send(HUH(ERR + message))
    def handle_HUH(self, client, message):
        self.log_debug(7, 'Client #%d complained about message: %s',
                client.client_id, message)
    def handle_ADM(self, client, message):
        line = message.fold()[2][0]
        text = line.lower()
        if text[0:7] == 'server:':
            if self.options.admin_cmd: self.seek_command(client, text[7:])
            else: client.admin('Admin commands have been disabled.')
        elif self.options.admin_cmd and not re.search('[a-z]', line):
            self.seek_command(client, text)
        elif self.options.fwd_admin:
            if text[0:4] == 'all:': self.broadcast(message)
            else: client.game.broadcast(message)
        else: client.reject(message)
    def seek_command(self, client, text):
        for pattern in self.commands:
            match = pattern.pattern.search(text)
            if match:
                pattern.command(self, client, match)
                break
        else:
            for pattern in client.game.commands:
                match = pattern.pattern.search(text)
                if match:
                    pattern.command(client.game, client, match)
                    break
            else:
                for pattern in self.local_commands:
                    match = pattern.pattern.search(text)
                    if match:
                        if client.address in ('localhost', '127.0.0.1'):
                            pattern.command(self, client, match)
                        else: client.admin('You are not authorized to do that.')
                        break
                else: client.admin('Unrecognized command: "%s"', text.strip())
    def handle_SEL(self, client, message):
        if len(message) > 3:
            reply = self.join_game(client, message.fold()[1][0]) and YES or REJ
            client.send(reply(message))
        else: client.send(SEL(client.game.game_id))
    def handle_PNG(self, client, message): client.accept(message)
    def handle_LST(self, client, message):
        if len(message) > 3:
            game = self.games.get(message.fold()[1][0])
            if game: client.send(game.listing())
            else: client.reject(message)
        else:
            for game in self.games.itervalues():
                client.send(game.listing())
            client.accept(message)
    
    def default_game(self):
        while self.default:
            game = self.default[-1]
            if game.closed: self.default.pop()
            else: return game
        else: return self.start_game()
    def join_game(self, client, game_id):
        new_game = None
        result = False
        
        if client.game.game_id == game_id: result = True
        elif self.games.has_key(game_id):
            new_game = self.games[game_id]
            result = True
        elif self.options.log_games:
            # Resuscitate an archived game as a Historian
            new_game = Historian(self, game_id)
            try:
                saved = open(self.filename(game_id), 'rU')
                result = new_game.load(saved)
                saved.close()
            except IOError: pass
            except Exception, e:
                self.log_debug(1,
                        'Exception while loading a saved game: %s %s',
                        e.__class__.__name__, e.args)
            if result: self.games[game_id] = new_game
        
        if result and new_game:
            client.change_game(new_game)
        return result
    def start_game(self, client=None, match=None):
        if match and match.lastindex:
            var_name = match.group(2)
        else: var_name = self.options.variant
        
        try:
            variant = variants[var_name]
        except KeyError:
            if client:
                client.admin('Unknown variant "%s"', var_name)
            else:
                raise ValueError('Unknown variant "%s"' % var_name)
        else:
            game_id = timestamp()
            self.started_games += 1
            if client: client.admin('New game started, with id %s.', game_id)
            game = Game(self, game_id, variant)
            self.games[game_id] = game
            self.default.append(game)
            self.manager.add_dynamic(game)
            self.manager.start_clients(game_id)
            return game
        return None
    def select_game(self, client, match):
        game_id = match.group(1)
        if self.join_game(client, game_id):
            client.admin('Joined game %s.', game_id)
        else: client.admin('Unknown game %s.', game_id)
    
    def list_variants(self, client, match):
        names = expand_list(sorted(variants))
        client.admin('Known map variants: %s', names)
    def list_help(self, client, match):
        for line in ([
            #'Begin an admin message with "All:" to send it to all players, not just the ones in the current game.',
            'Begin an admin message with "Server:" to use the following commands, all of which are case-insensitive:',
        ] + [pattern.description for pattern in self.commands]
        + [pattern.description for pattern in client.game.commands]):
            client.admin(line)
    def list_bots(self, client, match):
        client.admin('Available types of bots:')
        for name in bots:
            description = bots[name].__doc__.splitlines()[0].strip()
            client.admin('  %s - %s', name, description)
    def list_status(self, client, match):
        for game in self.games.itervalues():
            if game.closed: message = 'Closed'
            elif game.paused: message = 'Paused'
            elif game.started: message = 'In progress'
            else: message = 'Forming'
            client.admin('Game %s: %s; %s', game.game_id,
                    message, game.has_need())
    def list_powers(self, client, match):
        for player in client.game.players.values():
            if player.client:
                client.admin('%s (%d): %s, from %s', player.pname,
                        player.passcode, player.full_name(),
                        player.client.address)
            else: client.admin('%s (%d): None', player.pname, player.passcode)
    def close(self, client=None, match=None):
        ''' Tells clients to exit, and closes the server's sockets.'''
        if not self.closed:
            self.broadcast_admin('The server is shutting down.  Good-bye.')
            self.log_debug(10, 'Closing')
            self.closed = True
            for game in self.games.itervalues():
                if game.started and not game.saved:
                    self.archive(game)
                if not game.closed: game.close()
            self.broadcast(+OFF)
            if not self.manager.closed: self.manager.close()
            self.log_debug(11, 'Done closing')
        else: self.log_debug(11, 'Duplicate close() call')
    
    commands = [
        Command(r'help', list_help,
            '  help - Lists admin commands recognized by the server'),
        Command(r'new game', start_game,
            '  new game - Starts a new game of Standard Diplomacy'),
        Command(r'(new|start) (\w+) game', start_game,
            '  new <variant> game - Starts a new game, with the <variant> map'),
        #Command(r'select game (\w+)', select_game,
        #    '  select game <id> - Switches to game <id>, if it exists'),
        Command(r'list variants', list_variants,
            '  list variants - Lists known map variants'),
        Command(r'list bots', list_bots,
            '  list bots - Lists bots that can be started by the server'),
        Command(r'status', list_status,
            '  status - Displays the status of each game'),
    ]
    local_commands = [
        Command(r'shutdown', close,
            '  shutdown - Stops the server'),
        Command(r'powers', list_powers,
            '  powers - Displays the power assignments for this game'),
    ]

class Historian(VerboseObject):
    ''' A game-like object that simply handles clients and history.'''
    class HistoricalJudge(object):
        def __init__(self, historian, last_turn, result):
            self.history = historian
            self.turn = last_turn
            self.game_result = result
        
        def handle_MAP(self, client, message):
            client.send(self.history.messages[MAP])
        def handle_VAR(self, client, message):
            client.send(self.history.messages[VAR])
        def handle_MDF(self, client, message):
            client.send(self.history.messages[MDF])
        def handle_NOW(self, client, message):
            client.send(self.history.history[self.turn][NOW])
        def handle_SCO(self, client, message):
            client.send(self.history.history[self.turn][SCO])
        def handle_ORD(self, client, message):
            client.send_list(self.history.history[self.turn][ORD])
        
        def handle_SUB(self, client, message): client.reject(message)
        def handle_DRW(self, client, message): client.reject(message)
        def handle_MIS(self, client, message): client.reject(message)
        def handle_NOT_SUB(self, client, message): client.reject(message)
        def handle_NOT_DRW(self, client, message): client.reject(message)
    
    def __init__(self, server, game_id):
        ''' Initializes certain instance variables:
            - server           The overarching server for the program
            - game_id          The unique identification for this game
            - game_options     The GameOptions instance for this game
            - started          Whether the game has started yet
            - closed           Whether the server is trying to shut down
            - clients          List of Clients that have accepted the map
        '''#'''
        self.__super.__init__()
        self.server = server
        self.game_id = game_id
        self.game_options = GameOptions()
        self.prefix = 'Historian %s' % game_id
        self.judge = None
        self.saved = False
        self.closed = True
        self.started = True
        self.variant = None
        self.clients = []
        self.messages = {}
        self.history = {}
        self.validator = Validator()
    
    def save(self, stream):
        if not self.started:
            raise UserWarning('Trying to save an unstarted game')
        def write_message(msg): stream.write(str(msg) + '\n')
        def write(token): write_message(self.messages[token])
        write(LST)
        write(MAP)
        write(VAR)
        write(MDF)
        write(HLO)
        write(SCO)
        write(NOW)
        for turn in sorted(self.history.keys()):
            for message in self.get_history(turn, False):
                write_message(message)
        if self.judge.game_result: write_message(self.judge.game_result)
        if self.started:
            if self.closed: write(SMR)
            else:
                for country, player in self.players:
                    write_message(IAM (country) (player.pcode))
        self.saved = True
        self.broadcast(SVE(str(self.game_id)))
    def load(self, stream):
        sco = None
        turn = None
        result = None
        rep = protocol.base_rep
        history = {}
        messages = {}
        for line in stream:
            message = rep.translate(line)
            self.log_debug(13, 'Loading "%s" from game log.', message)
            first = message[0]
            if first in (ORD, SET):
                offset = first is ORD and 2 or 5
                turn = Turn(message[offset], message[offset + 1]).key
                history.setdefault(turn, {
                        SET: [],
                        ORD: [],
                        SCO: sco,
                        'new_SCO': False,
                        NOW: None
                })[first].append(message)
            elif first is NOW:
                history.get(turn, messages)[NOW] = message
            elif first is SCO:
                when = history.get(turn, messages)
                when[SCO] = sco = message
                when['new_SCO'] = True
            elif first in (LST, MAP, VAR, MDF, HLO, SMR):
                messages[first] = message
                if first is MAP:
                    variant_name = message.fold()[1][0]
                    try:
                        self.variant = variants[variant_name]
                    except KeyError:
                        self.log_debug(7, 'Variant %r not found among %r',
                                variant_name, variants.keys())
                        return False
                    else:
                        rep = self.variant.rep
                elif first is HLO:
                    self.game_options.parse_message(message)
            elif first in (DRW, SLO):
                result = message
        self.judge = self.HistoricalJudge(self, turn, result)
        self.history = history
        self.messages = messages
        self.saved = True
        return True
    
    # Stub routines, used by Service and Server
    def disconnect(self, client):
        self.log_debug(6, 'Client #%d has disconnected', client.client_id)
        if client in self.clients:
            self.clients.remove(client)
            self.admin('%s has disconnected.', client.full_name())
    def listing(self): return self.messages[LST]
    
    # Sending messages
    def broadcast(self, message):
        ''' Sends a message to each ready client, and notes it in the log.'''
        self.log_debug(2, 'ALL << %s', message)
        for client in self.clients: client.write(message)
    def admin(self, line, *args):
        if self.server.options.snd_admin:
            self.broadcast(ADM('Server')(str(line) % args))
    
    # Degenerate message handlers
    def handle_GOF(self, client, message): client.reject(message)
    def handle_SND(self, client, message): client.reject(message)
    def handle_TME(self, client, message): client.reject(message)
    def handle_NOT_TME(self, client, message): client.reject(message)
    def handle_NOT_GOF(self, client, message): client.reject(message)
    def handle_REJ_MAP(self, client, message): self.disconnect(client)
    def handle_YES_SVE(self, client, message): pass
    def handle_REJ_SVE(self, client, message): pass
    def handle_YES_LOD(self, client, message): pass
    def handle_REJ_LOD(self, client, message): self.disconnect(client)
    
    # Identity messages
    def handle_NME(self, client, message): client.reject(message)
    def handle_IAM(self, client, message): client.reject(message)
    def handle_OBS(self, client, message):
        if client in self.clients: client.reject(message)
        else:
            if len(message) > 1:
                msg = message.fold()
                client.name, client.version = (msg[1][0], msg[2][0])
            client.accept(message)
            client.send(self.messages[MAP])
    def handle_YES_MAP(self, client, message):
        if client in self.clients: return # Ignore duplicate messages
        self.clients.append(client)
        name = client.full_name()
        obs = client.name and ' as an observer' or ''
        self.admin('%s has connected%s.', name, obs)
        client.send(self.messages[HLO])
        client.send(self.messages[SCO])
        if self.judge.game_result: client.send(self.judge.game_result)
        if self.started and self.closed: client.send(self.messages[SMR])
        client.send(self.messages[NOW])
    
    # History
    def handle_HST(self, client, message):
        if len(message) > 1:
            turn = Turn(message[2], message[3]).key
            result = self.get_history(turn, True)
            if result: client.send_list(result)
            else: client.reject(message)
        elif self.history:
            for turn in sorted(self.history.keys()):
                client.send_list(self.get_history(turn, False))
        else: client.reject(message)
    def get_history(self, key, always_sco):
        result = []
        turn = self.history.get(key)
        if turn:
            for message in sorted(turn[SET]): result.append(message)
            for message in sorted(turn[ORD]): result.append(message)
            if always_sco or turn['new_SCO']:
                result.append(turn[SCO])
            result.append(turn[NOW])
        return result
    def handle_SMR(self, client, message):
        if self.started and self.closed:
            if self.judge.game_result: client.send(self.judge.game_result)
            client.send(self.messages[SMR])
        else: client.reject(message)
    
    commands = []

class Game(Historian):
    ''' Coordinates messages between Players and the Judge,
        administering time limits and power assignments.
        
        Note: This implementation accepts press and other messages after
        the deadlines, until network traffic stops.  That prevents mass
        amounts of last-second traffic from preventing someone's orders
        from going through, but can be abused.
    '''#'''
    __options__ = (
        ('shuffle', bool, True, 'randomize power assignments',
            'Whether to assign players to powers randomly.',
            'If not true, powers are assigned in token order',
            '(usually alphabetical), to each player as it connects.'),
        ('quit', bool, False, 'close on disconnect',
            'Whether a game should end when a player disconnects.',
            'Useful for testing, but should *not* be on for human games.'),
        ('veto_time', int, 20, 'time allowed for vetos',
            'Time (in seconds) to wait for vetos before processing certain admin commands.',
            'Use 0 to disable vetos entirely.'),
        ('takeovers', bool, False, 'allow takeovers',
            'Whether IAM messages can take over non-abandoned powers.',
            'This can be disturbing to the original player, so use with care.',
            'However, it allows new players to take over bot positions,',
            'and prevents problems with an undetected nonresponsive client.'),
        ('replaced', bool, False, 'show replaced powers in summary',
            'Whether SMR messages should list players that have been replaced.',
            'If true, the original player will be listed first,',
            'with the year of replacement and their center count at that time,',
            'but only if the new player reports a different name and/or version.'),
        ('bot_min', int, 0, 'minimum player count for bots',
            'Blocks the bot-starting admin commands, in favor of more individual players.',
            'Specifically, starting bots requires that at least this many players',
            'be connected from different IP addresses.',
            'Use 0 to always allow starting bots.'),
    )
    
    class Player_Struct(object):
        def __init__(self, power_name):
            self.client   = None
            self.name     = ''
            self.version  = ''
            self.ready    = False
            self.pname    = power_name
            self.robotic  = False
            self.assigned = False
            self.passcode = randint(100, protocol.max_pos_int - 1)
        def new_client(self, client, assigned=False):
            self.client   = client
            self.ready    = False
            if assigned:
                name, version = self.assigned
                self.robotic  = True
                self.assigned = False
            else:
                name = client.name or self.name
                version = client.version or self.version
                self.robotic  = 'Human' not in name + version
            self.name    = client.name = name
            self.version = client.version = version
        def client_ready(self): return self.client and self.ready
        def copy_client(self, struct):
            self.name    = struct.name
            self.ready   = struct.ready
            self.client  = struct.client
            self.version = struct.version
            self.robotic = struct.robotic
        def full_name(self): return '%s (%s)' % (self.name, self.version)
    
    def __init__(self, server, game_id, variant):
        ''' Initializes yet more instance variables:
            - judge            The judge, handling orders and adjudication
            - press_allowed    Whether press is allowed right now
            - timers           Time notification requests
            - deadline         When the current turn will end
            - press_deadline   When press must stop for the current turn
            - time_checked     When time notifications were last sent
            - time_stopped     Time remaining when the clock stopped
            - press_in         Whether press is allowed during a given phase
            - limits           The time limits for the phases, as well as max and press
            - players          Power token -> player mappings
            - p_order          The order in which to assign powers
        '''#'''
        self.__super.__init__(server, game_id)
        
        # Override certain Historian variables
        self.prefix         = 'Game %s' % game_id
        self.started        = False
        self.closed         = False
        self.variant        = variant
        self.judge          = variant.new_judge(self.game_options)
        self.messages[MAP]  = MAP(variant.mapname)
        self.messages[VAR]  = VAR(variant.name)
        self.messages[MDF]  = self.judge.mdf
        
        # Press- and time-related variables
        self.press_allowed  = False
        self.paused         = False
        self.timers         = {}
        self.deadline       = None
        self.press_deadline = 0
        self.time_checked   = None
        self.time_stopped   = None
        self.actions        = []
        
        self.set_limits()
        
        # Player-related variables
        self.players        = {}
        self.limbo          = {}
        self.summary        = []
        powers = self.judge.players()
        if self.options.shuffle: shuffle(powers)
        else: powers.sort()
        self.p_order        = powers
        for country in powers:
            self.players[country] = self.Player_Struct(
                    self.judge.player_name(country))
    
    def set_limits(self):
        game = self.game_options
        
        move_limit = int(game.MTL)
        press_limit = int(game.PTL)
        build_limit = int(game.BTL)
        retreat_limit = int(game.RTL)
        self.press_in = {
            Turn.move_phase    : press_limit < move_limit or not move_limit,
            Turn.retreat_phase : not game.NPR,
            Turn.build_phase   : not game.NPB,
        }
        
        self.limits = {
            None               : 0,
            Turn.move_phase    : move_limit,
            Turn.retreat_phase : retreat_limit,
            Turn.build_phase   : build_limit,
            'press'            : press_limit,
        }
    
    # Connecting and disconnecting players
    def open_position(self, country):
        ''' Frees the player slot to be taken over,
            and either broadcasts the CCD message (during a game),
            or tries to give it to the oldest client in limbo.
        '''#'''
        player = self.players[country]
        player.client = None
        player.ready = True
        if self.closed: pass
        elif self.judge.phase:
            self.broadcast(CCD(country))
            pcode = 'Passcode for %s: %d' % (player.pname, player.passcode)
            self.log_debug(6, pcode)
            if not self.judge.eliminated(country):
                #self.admin(pcode)
                if self.game_options.DSD: self.pause()
        elif self.limbo: self.offer_power(country, *self.limbo.popitem())
    def offer_power(self, country, client, message):
        ''' Sets the client as the player for the power,
            pending acceptance of the map.
        '''#'''
        self.log_debug(6, 'Offering %s to client #%d', country, client.client_id)
        msg = message.fold()
        client.country = country
        client.name = msg[1][0]
        client.version = msg[2][0]
        self.players[country].new_client(client)
        client.send_list([YES(message), MAP(self.judge.map_name)])
    def players_unready(self):
        ''' A list of disconnected or unready players.'''
        return [country
            for country, struct in self.players.iteritems()
            if not (struct.client_ready() or self.judge.eliminated(country))
        ]
    def disconnect(self, client):
        self.log_debug(6, 'Client #%d has disconnected', client.client_id)
        self.cancel_time_requests(client)
        opening = None
        if client in self.clients:
            self.clients.remove(client)
            need = self.closed and ' ' or self.has_need()
            name = client.full_name()
            if client.booted:
                player = self.players[client.booted]
                if player.client is client:
                    reason = 'booted'
                    opening = client.booted
                else: reason = 'replaced'
                self.admin('%s has been %s. %s', name, reason, need)
            elif client.country:
                player = self.players[client.country]
                if self.closed or not self.started:
                    self.admin('%s has disconnected. %s', name, need)
                opening = client.country
                client.country = None
            else: self.admin('%s has disconnected. %s', name, need)
        elif client.country:
            # Rejected the map
            opening = client.country
            client.country = None
        elif self.limbo.has_key(client): del self.limbo[client]
        
        # For testing purposes: stop the game if a player quits
        if opening and not self.closed:
            quitting = self.options.quit
            self.log_debug(11, 'Deciding whether to quit (%s)', quitting)
            if quitting: self.close()
            else: self.open_position(opening)
    def close(self):
        self.log_debug(10, 'Closing')
        self.pause()
        self.judge.phase = None
        self.press_allowed = False
        if not self.closed:
            self.closed = True
            if self.started:
                summary = self.summarize()
                if not self.saved: self.broadcast(summary)
                self.messages[SMR] = summary
                self.messages[LST] = self.listing()
                self.server.archive(self)
    def reveal_passcodes(self, client):
        disconnected = {}
        robotic = {}
        for country, player in self.players.iteritems():
            if not self.judge.eliminated(country):
                if not player.client: disconnected[country] = player.passcode
                elif player.robotic: robotic[country] = player.passcode
        msg = None
        slate = None
        if disconnected:
            if len(disconnected) > 1: msg = 'have been disconnected'
            else: msg = 'has been disconnected'
            slate = disconnected
        elif robotic and self.options.takeovers:
            if len(robotic) > 1: msg = 'seem to be bots'
            else: msg = 'seems to be a bot'
            slate = robotic
        if msg:
            client.admin('%s %s.',
                expand_list(['%s (%s)' % kv for kv in slate.iteritems()]), msg)
            return True
        return False
    def players_needed(self):
        ''' Calculates the number of empty powers in the game.'''
        return len([p for p in self.players.itervalues() if not p.client])
    def has_need(self):
        ''' Creates the line announcing connected and needed players.'''
        observing = len([True for client in self.clients if not client.country])
        have      = len(self.clients) - observing
        needed    = len(self.players) - have
        need = ''
        if not self.started:
            if needed: need = 'Need %d to start.' % needed
            else: need = 'Game on!'
        elif needed and not self.closed:
            need = '%d player%s disconnected.' % (needed, s(needed))
        return 'Have %d player%s and %d observer%s. %s' % (
                have, s(have), observing, s(observing), need)
    def check_start(self):
        needed = len(self.players_unready())
        if needed:
            self.log_debug(9, 'Waiting for %d more player%s', needed, s(needed))
        else:
            # Send starting messages, and start the timers.
            self.started = True
            self.log_debug(9, 'Starting the game')
            self.validator.syntax_level = self.game_options.LVL
            self.messages[LST] = self.listing(OFF)
            self.messages[HLO] = HLO(OBS)(0)(self.game_options)
            for user in self.clients: self.send_hello(user)
            for user, message in self.limbo.iteritems():
                user.reject(message)
                self.reveal_passcodes(user)
            self.limbo.clear()
            
            result = self.judge.start()
            for message in result:
                self.broadcast(message)
                self.messages[message[0]] = message
            
            self.set_limits()
            self.set_deadlines()
    
    # Time Limits
    def pause(self):
        if self.deadline and not self.paused:
            self.time_stopped = self.deadline - time()
            self.broadcast(NOT(TME(Time(self.time_stopped))))
        self.paused = True
    def unpause(self):
        self.paused = False
        if self.time_stopped: self.set_deadlines(self.time_stopped)
    def set_deadlines(self, seconds=None):
        ''' Sets the press_allowed flag and starts turn timers.
            Use seconds when the clock starts again after DSD.
        '''#'''
        phase = self.judge.phase
        if not seconds:
            seconds = self.limits[phase]
            self.press_allowed = (phase and self.press_in[phase])
            self.time_checked = seconds
        self.deadline = self.time_stopped = None
        self.press_deadline = 0
        if seconds and not self.closed:
            message = TME(Time(seconds))
            if self.paused:
                self.time_stopped = seconds
                self.broadcast(NOT(message))
            else:
                self.deadline = time() + seconds
                if self.press_allowed and phase == Turn.move_phase:
                    self.press_deadline = self.limits['press']
                self.broadcast(message)
    def time_left(self, now):
        ''' Returns the number of seconds before the next event.
            May return None if there is no next event scheduled.
        '''#'''
        if self.ready(): return 0
        result = None
        if self.deadline and not self.paused:
            timers = [sec for sec in self.timers if sec < self.time_checked]
            timers.append(self.limits['press'] and self.press_deadline)
            result = self.deadline - max(timers)
        if self.actions:
            next_action = min([a.when for a in self.actions])
            if result: result = min(next_action, result)
            else: result = next_action
        return result and result - now
    def cancel_time_requests(self, client):
        ''' Removes the client from the list of time requests.'''
        for client_list in self.timers.itervalues():
            while client in client_list: client_list.remove(client)
    def run(self):
        ''' Checks deadlines, time requests, wait flags, and delayed actions,
            running the judge and sending notifications when appropriate.
        '''#'''
        now = time()
        for act in list(self.actions):
            if act.when <= now: act.call(); self.actions.remove(act)
        if self.ready(): self.run_judge()
        elif self.deadline and not self.paused:
            remain = self.deadline - now
            times = reversed(sorted(sec for sec in self.timers
                        if remain < sec < self.time_checked))
            for second in times:
                self.time_checked = second
                for client in self.timers[second]:
                    client.send(TME(Time(second)))
            if now > self.deadline: self.run_judge()
            elif remain < self.press_deadline:
                self.press_allowed  = False
    def ready(self): return not (self.paused or self.judge.unready or self.players_unready())
    def run_judge(self):
        ''' Runs the judge and handles turn transitions.'''
        if self.deadline: self.log_debug(10, 'Running the judge with %f seconds left', self.deadline - time())
        else: self.log_debug(10, 'Running the judge')
        
        key = self.judge.turn().key
        self.history[key] = turn = {
            SET: [], ORD: [], SCO: None, NOW: None, 'new_SCO': False
        }
        for message in self.judge.run():
            self.broadcast(message)
            if message[0] in (ORD, SET): turn[message[0]].append(message)
            elif message[0] in (SCO, NOW): turn[message[0]] = message
        if not turn[SCO]: turn[SCO] = self.judge.map.create_SCO()
        else: turn['new_SCO'] = True
        
        if self.judge.phase:
            self.set_deadlines()
            for player in self.players.itervalues():
                if player.client: player.ready = True
        else: self.close()
    def queue_action(self, client, action_callback, action_line,
            veto_callback, veto_line, veto_terms, *args):
        delay = self.options.veto_time
        self.admin('%s is %s', client.full_name(), action_line)
        if delay > 0:
            self.actions.append(DelayedAction(action_callback, veto_callback,
                veto_line, veto_terms, delay, *args))
            self.admin('(You may veto within %s seconds.)', num2name(delay))
        else: action_callback(*args)
    def full_name(self): return 'The server'
    
    # Sending messages
    def send_hello(self, client):
        country = client.country
        if country: passcode = self.players[country].passcode
        else: country = UNO; passcode = 0
        client.send(HLO(country)(passcode)(self.game_options))
    def summarize(self):
        ''' Creates the end-of-game SMR message.'''
        result = self.messages.get(SMR)
        if not result:
            players = self.summary
            for country, player in self.players.iteritems():
                stats = [
                    country,
                    [player.name or '""'],
                    [player.version or ' '],
                    self.judge.score(country)
                ]
                elim = self.judge.eliminated(country)
                if elim: stats.append(elim)
                players.append(stats)
            self.messages[SMR] = result = SMR(self.judge.turn()) % players
        return result
    
    # Press and administration
    def listing(self, result=None):
        need = (not self.closed) and self.players_needed() or 0
        return (LST(self.game_id)(need, result or self.status())
                (self.variant.name)(self.game_options))
    def status(self):
        disconnected = False
        robotic = False
        for country, player in self.players.iteritems():
            if not self.judge.eliminated(country):
                if not player.client: disconnected = True
                elif player.robotic: robotic = True
        
        if self.closed:
            if self.judge.game_result:
                result = self.judge.game_result[0]
            else: result = OFF
        elif self.paused:
            if disconnected and self.game_options.DSD:
                result = DSD
            else: result = TME
        elif self.started:
            if disconnected or (robotic and self.options.takeovers):
                result = IAM
            else: result = OBS
        else: result = NME
        return result
    def handle_GOF(self, client, message):
        country = client.country
        if country and self.judge.phase:
            self.players[country].ready = True
            client.accept(message)
            missing = self.judge.missing_orders(country)
            if missing: client.send(missing)
        else: client.reject(message)
    def handle_SND(self, client, message):
        ''' Sends the press message to the recipients,
            subject to various caveats listed in the syntax document.
        '''#'''
        country = client.country
        eliminated = self.judge.eliminated()
        if country and self.press_allowed and country not in eliminated:
            folded = message.fold()
            offset = len(folded) > 3
            recips = folded[1 + offset]
            for nation in recips:
                if not self.players[nation].client:
                    client.send(CCD(nation)(message))
                    break
                elif nation in eliminated:
                    client.send(OUT(nation)(message))
                    break
                elif nation is country:
                    # The syntax document specifies that this should not be.
                    self.log_debug(7, 'Client #%d is sending press to itself.',
                            client.client_id)
                    pass
            else:
                press = Message(folded[2 + offset])
                # Send OUT if any power in press is eliminated
                for nation in eliminated:
                    if nation in press:
                        client.send(OUT(nation)(message))
                        return
                self.validator.trim(press)
                outgoing = FRM(country)(recips)(press)
                for nation in recips:
                    # Hope that nobody disappears here...
                    self.players[nation].client.send(outgoing)
                client.accept(message)
        else: client.reject(message)
    def handle_HLO(self, client, message):
        if self.started: self.send_hello(client)
        else: client.reject(message)
    def handle_TME(self, client, message):
        if self.deadline and not self.paused: remain = self.deadline - time()
        else: remain = 0
        
        if len(message) == 1:
            # Request for amount of time left in the turn
            if remain: client.send(TME(Time(remain)))
            else:      client.reject(message)
        elif len(message) >= 4:
            try: request = int(Time(*message.fold()[1]))
            except (ValueError, KeyError): client.reject(message)
            if request > max(self.limits.values()):
                # Ignore requests greater than the longest time limit
                client.reject(message)
            else:
                # Add it to the list
                self.timers.setdefault(request, []).append(client)
                client.accept(message)
        else: client.reject(message)
    
    # Messages with standard prefixes
    def handle_NOT_TME(self, client, message):
        ''' Cancels client timer requests.
            NOT (TME) cancels all requests, NOT (TME (seconds)) just one.
        '''#'''
        reply = YES
        if len(message) == 4: self.cancel_time_requests(client)
        elif len(message) >= 4:
            # Remove the request from the list, if it's there.
            try:
                request = int(Time(*message.fold()[1]))
                self.timers[request].remove(client)
            except (ValueError, KeyError): reply = REJ
        else: reply = REJ
        client.send(reply(message))
    def handle_NOT_GOF(self, client, message):
        country = client.country
        if country and self.judge.phase and not self.judge.eliminated(country):
            self.players[country].ready = False
            client.accept(message)
        else: client.reject(message)
    def handle_YES_MAP(self, client, message):
        if message.fold()[1][1][0].lower() == self.judge.map_name:
            if client in self.clients: return # Ignore duplicate messages
            self.clients.append(client)
            if self.server.options.admin_cmd:
                client.admin('Welcome.  This server accepts admin commands; '
                        'send "Server: help" for details.')
            name = client.full_name()
            obs = ''
            if client.country:
                self.players[client.country].ready = True
            else:
                if client.name: obs = ' as an observer'
                if self.started and not self.closed:
                    self.reveal_passcodes(client)
            self.admin('%s has connected%s. %s', name, obs, self.has_need())
            
            if self.started:
                self.send_hello(client)
                # This should probably be farmed out to the judge,
                # but it works for now.
                client.send(self.judge.map.create_SCO())
                if self.closed:
                    msg = self.judge.game_result
                    if msg: client.send(msg)
                    if self.started: client.send(self.summarize())
                client.send(self.judge.map.create_NOW())
            else: self.check_start()
        else: client.reject(message); self.disconnect(client)
    
    # Identity messages
    def handle_NME(self, client, message):
        if self.started or client.country:
            # Prohibit playing multiple positions,
            # and block signups after starting a game
            client.reject(message)
            self.reveal_passcodes(client)
            if not client.name:
                msg = message.fold()
                client.name = msg[1][0]
                client.version = msg[2][0]
        else:
            for country in self.p_order:
                # Take the first open slot
                if not self.players[country].client:
                    self.offer_power(country, client, message)
                    break
            else:
                # Wait for an opening
                self.log_debug(6, 'Leaving client #%d in limbo', client.client_id)
                self.limbo[client] = message
    def handle_IAM(self, client, message):
        country = message[2]
        passcode = message[5].value()
        self.log_debug(9, 'Considering IAM (%s) (%d)', country, passcode)
        slot = self.players[country]
        
        # Block attacks by the unscrupulous.
        if not self.started:
            # Check whether we have actually given out this passcode
            if slot.assigned and slot.passcode == passcode:
                self.log_debug(6, 'Client #%d takes over %s', client.client_id, country)
                old_client = slot.client
                if old_client:
                    for new_country in self.p_order:
                        # Take the first open slot
                        new_slot = self.players[new_country]
                        if not new_slot.client:
                            self.log_debug(6, 'Reassigning client #%d to %s',
                                    old_client.client_id, new_country)
                            old_client.country = new_country
                            new_slot.copy_client(slot)
                            break
                    else:
                        self.log_debug(1, 'No place to put old client #%d!',
                                old_client.client_id)
                        old_client.country = None
                
                slot.new_client(client, True)
                client.country = country
                client.accept(message)
            else:
                client.reject(message)
                if client.country: self.open_position(country)
                client.boot()
        elif client.guesses < 3 and slot.passcode == passcode:
            # Be very careful here.
            old_client = slot.client
            self.log_debug(9, 'Passcode check succeeded; switching from %r', client.country)
            
            if old_client is client and country == client.country:
                # It's already okay.
                good = False
            elif not old_client:
                # Allow taking over empty slots, but not by existing players
                good = not client.country
                if good: self.broadcast(NOT(CCD(country)))
            elif self.options.takeovers:
                # The current client might be dead, but we haven't noticed yet.
                # Or this could be a legitimate GM decision,
                # to replace a bot with a human player
                good = True
            else: good = False
            
            if good:
                self.log_debug(6, 'Client #%d takes control of %s', client.client_id, country)
                if client not in self.clients: self.clients.append(client)
                if client.country: self.open_position(client.country)
                client.country = country
                if (client.name and self.options.replaced and
                        (slot.name, slot.version) !=
                        (client.name, client.version)):
                    # Slight abuse of the syntax:
                    # Replaced players are reported, with the year of
                    # replacement and their center count at that time.
                    # This means the country will be reported multiple times.
                    self.summary.append([
                        country,
                        [slot.name or '""'],
                        [slot.version or ' '],
                        self.judge.score(country),
                        self.judge.turn().year
                    ])
                slot.new_client(client)
                slot.ready = True
                client.accept(message)
                if old_client: old_client.boot()
                
                # Restart timers if everybody's here
                unready = self.players_unready()
                if unready: self.log_debug(9, 'Still waiting for %s', expand_list(unready))
                elif self.paused: self.resume()
            else: client.reject(message)
        else:
            self.log_debug(7, 'Passcode check failed')
            client.guesses += 1
            client.reject(message)
    
    # Game-specific admin commands
    def find_players(self, name):
        result = []
        low_result = []
        for key, struct in self.players.iteritems():
            names = (struct.name, struct.version)
            if self.started: names += (struct.pname, key.text)
            for item in names:
                if name == item:
                    result.append((struct.client, item))
                elif name == item.lower():
                    low_result.append((struct.client, item))
        return result or low_result
    def eject(self, client, match):
        verb, name = match.groups()
        players = self.find_players(name)
        if (len(players) == 1) or (players and not self.started):
            if verb == 'boot':
                veto_action = self.block_boot
                veto_verb = 'booting'
                terms = ('boot', 'booting')
            else:
                veto_action = None
                veto_verb = 'ejection'
                terms = ('eject', 'ejection')
            
            names = defaultdict(int)
            for c,n in players: names[n] += 1
            itemlist = [(num,nam) for nam,num in names.items()]
            itemlist.sort()
            self.queue_action(client, self.boot_players,
                    '%sing %s from the game.' %
                    (verb, expand_list([instances(num, nam, False)
                        for num,nam in itemlist])),
                    veto_action, 'the player %s.' % veto_verb, terms,
                    [c for c,n in players])
        else:
            status = players and 'Ambiguous' or 'Unknown'
            client.admin('%s player "%s"', status, name.capitalize())
    def block_boot(self, client, players):
        if client in players: return "You can't veto your own booting."
    def boot_players(self, players):
        for client in players: client.boot()
    def list_players(self, client, match):
        players = []
        observers = []
        observing = 0
        for person in self.clients:
            if person.name:
                name = '  ' + person.full_name()
                if person.country: players.append(name)
                else: observers.append(name)
            else: observing += 1
        if players:
            client.admin('Players:')
            players.sort()
            for line in players: client.admin(line)
        if observers:
            client.admin('Observers:')
            observers.sort()
            for line in observers: client.admin(line)
        if observing:
            client.admin('%s anonymous observer%s',
                    num2name(observing).capitalize(), s(observing))
    def set_time_limit(self, client, match):
        phase, seconds = match.groups()
        if phase[0] in "mrbp":
            attribute = phase[0].upper() + 'TL'
            if seconds and not self.started:
                value = int(seconds.strip())
                setattr(self.game_options, attribute, value)
                self.admin('%s has set the %s time limit to %d seconds.',
                        client.full_name(), phase, value)
            else:
                value = getattr(self.game_options, attribute)
                client.admin('The %s time limit is %d seconds.', phase, value)
        else:
            client.admin('Unknown phase %r; '
                'try move, build, retreat, or press.', phase)
    def stop_time(self, client, match):
        if self.paused: client.admin('The game is already paused.')
        else:
            self.pause()
            self.admin('%s has paused the game.', client.full_name())
    def resume(self, client=None, match=None):
        if self.paused:
            self.queue_action(client or self, self.unpause,
                    'resuming the game.', None, 'resuming the game.',
                    ('resume', 'unpause'))
        elif client: client.admin('The game is not currently paused.')
    def start_bot(self, client, match):
        ''' Starts the specified number of the specified kind of bot.
            If number is less than one, it will be added to
            the number of empty power slots in the client's game.
        '''#'''
        if self.num_players() < self.options.bot_min:
            #client.admin('This server is not designed for solo games;')
            client.admin('Recruit more players first, or use your own bots.')
            return
        bot_name = match.group(2)
        if bot_name[-1] == 's' and bot_name not in bots:
            bot_name = bot_name[:-1]
            default_num = 0
        else: default_num = 1
        if bot_name in bots:
            bot_class = bots[bot_name]
            country = match.group(3)
            if country:
                for token, struct in self.players.items():
                    if country in (token.text.lower(), struct.pname.lower()):
                        num = 1
                        power = token
                        pcode = struct.passcode
                        pname = struct.pname
                        if self.started and struct.client and not struct.client.closed:
                            client.admin('%s is still in the game.', pname)
                            return
                        else:
                            struct.assigned = (bot_class.__name__,
                                    version_string())
                        break
                else:
                    client.admin('Unknown player: %s', country)
                    return
            else:
                power = pcode = None
                try: num = int(match.group(1))
                except (TypeError, ValueError): num = default_num
                if num < 1: num += self.players_needed()
            
            name = bot_class.__name__
            self.queue_action(client, self.start_bot_class, 'starting %s%s.' %
                    (instances(num, name), power and ' as %s' % pname or ''),
                    None, 'the %s%s.' % (name, s(num)),
                    ('start', 'bot', 'bots', name, name + 's'),
                    bot_class, num, power, pcode)
        else: client.admin('Unknown bot: %s', bot_name)
    def start_bot_class(self, bot_class, number, power, pcode):
        self.log_debug(11, 'Attempting to start %s %s%s',
                num2name(number), bot_class.__name__, s(number))
        failure = 0
        for dummy in range(number):
            client = self.server.manager.add_client(bot_class,
                    game_id=self.game_id, power=power, passcode=pcode)
            if not client: failure += 1
        if failure:
            self.admin('%s bot%s failed to start',
                num2name(failure).capitalize(), s(failure))
    def num_players(self):
        return len(set([p.client.address
            for p in self.players.values() if p.client]))
    def set_press_level(self, client, match):
        cmd, specific, level = match.groups()
        if specific:
            try: new_level = self.validator.press_levels[level]
            except KeyError:
                client.admin('Invalid press level %r', level.capitalize())
                return
        elif cmd == 'en': new_level = 8000
        elif cmd == 'dis': new_level = 0
        old_level = self.game_options.LVL
        if new_level == old_level:
            client.admin('The press level is already %d', old_level)
        elif self.started:
            client.admin('The press level can only be changed before the game starts.')
        else:
            self.game_options.LVL = new_level
            self.admin('%s has set the press level to %d (%s).',
                    client.full_name(), new_level,
                    self.validator.press_levels[new_level])
    def end_game(self, client, match):
        if self.closed: client.admin('The game is already over.')
        else:
            self.queue_action(client, self.close, 'ending the game.',
                    None, 'ending the game.', ('end', 'close'))
    def veto_admin(self, client, match):
        word = match.group(2)
        if word: actions = [a for a in self.actions if word in a.terms]
        else: actions = list(self.actions)
        if actions:
            for vetoed in actions: vetoed.veto(client)
        else:
            client.admin('%s to %s.',
                word and ('No %s commands' % word) or 'Nothing',
                match.group(1))
    
    commands = [
        Command(r'who|list players', list_players,
            '  list players - Lists the player names (but not power assignments)'),
        Command(r'(veto|cancel|reject) *(\w*)', veto_admin,
            '  veto [<command>] - Cancels recent admin commands'),
        Command(r'(en|dis)able +press *(level +(\d+|[a-z ]+))?', set_press_level,
            '  enable/disable press - Allows or blocks press between powers'),
        Command(r'pause', stop_time,
            '  pause - Stops deadline timers and phase transitions'),
        Command(r'resume|unpause', resume,
            '  resume - Resumes deadline timers and phase transitions'),
        Command(r'\b(\w+) time limit( \d+|)', set_time_limit,
            '  <phase> time limit [<seconds>] - Set or display the time limit for <phase>'),
        Command(r'(eject|boot) +(.+)', eject,
            '  eject <player> - Disconnect <player> (either name or country) from the game'),
        Command(r'end game', end_game,
            '  end game - Ends the game (without a winner)'),
        Command(r'start (an? )?(\w+) as (\w+)', start_bot,
            '  start <bot> as <country> - Start a copy of <bot> to play <country>'),
        Command(r'start (an? |\d+ )?(\w+)()', start_bot,
            '  start <number> <bot> - Invites <number> copies of <bot> into the game'),
    ]


def run():
    r'''Run a game server.
        Takes options from the command line, including number of games and the
        default map.
    '''#'''
    from main import run_server
    run_server(Server, 7)
