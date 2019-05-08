r'''Test cases for the Parlance server
    Copyright (C) 2004-2008  Eric Wald
    
    This module tests the server's response to client activity, and other
    functionality not specifically related to adjudication or the judge.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import unittest
from time       import sleep, time

from parlance.config     import Configuration, GameOptions, VerboseObject
from parlance.functions  import num2name, fails, failing
from parlance.gameboard  import Turn
from parlance.language   import Time
from parlance.main       import ThreadManager
from parlance.network    import Service
from parlance.player     import Clock, HoldBot
from parlance.server     import Server
from parlance.tokens     import *
from parlance.xtended    import ITA, LON, PAR

class Fake_Manager(ThreadManager):
    def __init__(self):
        self.__super.__init__()
        self.pass_exceptions = True
        self.autostart = ()
        self.next_id = 0
        self.server = Server(self)
        self.start_clients(self.server.default_game().game_id)
    def add_client(self, player_class, **kwargs):
        service = Fake_Service(self.next_id,
                self.server, player_class, manager=self, **kwargs)
        self.next_id += 1
        return service
    def add_threaded(self, client):
        self.attempt(client)
    def add_dynamic(self, client):
        self.log_debug(1, 'Blocking dynamic client: %s', client.prefix)

class Fake_Service(Service):
    ''' Connects the Server straight to a player.
        It would probably be a bad idea to mix this with network Services.
    '''#'''
    def __init__(self, client_id, server, player_class, **kwargs):
        self.queue = []
        self.player = None
        self.__super.__init__(client_id, None, client_id, server)
        self.player = player_class(send_method=self.handle_message,
                representation=self.rep, **kwargs)
        self.player.register()
        for msg in self.queue: self.handle_message(msg)
    def write(self, message):
        self.player.handle_message(message)
        if self.player.closed: self.close()
    def close(self):
        if not self.closed:
            self.closed = True
            self.game.disconnect(self)
            self.server.disconnect(self)
    def handle_message(self, message):
        if self.player:
            self.log_debug(4, '%3s >> %s', self.power_name(), message)
            self.server.handle_message(self, message)
        else: self.queue.append(message)
    def send_RM(self): self.player.rep = self.rep

class ServerTestCase(unittest.TestCase):
    ''' Base class for Server unit tests'''
    class Fake_Player(VerboseObject):
        ''' A false player, to test the network classes.
            Also useful to learn country passcodes.
        '''#'''
        name = 'Fake Player'
        def __init__(self, send_method, representation, manager,
                power=None, passcode=None, game_id=None, observe=False):
            self.__super.__init__()
            self.log_debug(9, 'Fake player started')
            self.closed = False
            self.power = power
            self.pcode = passcode
            self.queue = []
            self.send = send_method
            self.rep = representation
            self.manager = manager
            self.game_id = game_id
            if observe: self.player_type = OBS
            else: self.player_type = NME
        def register(self):
            if self.game_id is not None: self.send(SEL(self.game_id))
            if self.power and self.pcode:
                self.send(IAM (self.power) (self.pcode))
            else:
                self.send(self.player_type (self.name)
                        (self.__class__.__name__))
        def close(self):
            self.log_debug(9, 'Closed')
            self.closed = True
        def handle_message(self, message):
            self.log_debug(5, '<< %s', message)
            self.queue.append(message)
            if message[0] is HLO:
                self.power = message[2]
                self.pcode = message[5].value()
                self.game_opts = GameOptions()
                self.game_opts.parse_message(message)
            elif message[0] in (MAP, SVE, LOD): self.send(YES(message))
            elif message[0] is OFF: self.close()
        def admin(self, line, *args):
            self.queue = []
            self.send(ADM(self.name)(str(line) % args))
            return [msg.fold()[2][0] for msg in self.queue if msg[0] is ADM]
        def get_time(self):
            self.queue = []
            self.send(+TME)
            times = [Time(*msg.fold()[1])
                    for msg in self.queue if msg[0] is TME]
            return times and int(times[0]) or None
        def hold_all(self):
            self.send(+MIS)
            units = [msg.fold()[1:] for msg in self.queue if msg[0] is MIS][-1]
            self.send(SUB % [[unit, HLD] for unit in units])
    class Fake_Master(Fake_Player):
        name = 'Fake Human Player'
    
    def setUp(self):
        ''' Initializes class variables for test cases.'''
        self.game_options = {
            'DSD': False,
            'LVL': 20,
            'RTL': 0,
            'BTL': 0,
            'PDA': False,
            'variant' : 'standard',
            'quit' : True,
            'snd_admin' : True,
            'admin_cmd' : True,
            'fwd_admin' : True,
            'host' : '',
            'port' : 16720,
            'wait_time' : 5,
            'send_SET': False,
            'send_ORD': False,
            'draw': 3,
            'response': 'croak',
            'bot_min': 2,
            'veto_time': 3,
            'MTL': 60,
            'confirm': False,
            'log_games': False,
            'block_exceptions': False,
        }
        
        self.set_verbosity(0)
        Configuration._cache.update(self.game_options)
        self.manager = None
        self.server = None
    def tearDown(self):
        if self.server and not self.server.closed: self.server.close()
        if self.manager and not self.manager.closed: self.manager.close()
    def set_verbosity(self, verbosity):
        self.set_option('verbosity', verbosity)
    def set_option(self, option, value):
        self.game_options[option] = value
        Configuration.set_globally(option, value)
    def connect_server(self):
        self.set_option('games', 1)
        self.manager = manager = Fake_Manager()
        self.server = manager.server
        self.game = self.server.default_game()
    def connect_player(self, player_class, **kwargs):
        client = self.manager.add_client(player_class, **kwargs)
        self.manager.process()
        return client.player
    def start_game(self):
        game = self.server.default_game()
        while not game.started: self.connect_player(self.Fake_Player)
        return game
    def wait_for_actions(self, game=None):
        if not game: game = self.server.default_game()
        while game.actions:
            remain = game.time_left(time())
            if remain > 0: sleep(remain + 0.001)
            game.run()
    
    def assertPressSent(self, press, sender, recipient):
        sender.queue = []
        recipient.queue = []
        msg = SND(recipient.power)(press)
        sender.send(msg)
        self.assertContains(YES(msg), sender.queue)
        msg = FRM(sender.power)(recipient.power)(press)
        self.assertContains(msg, recipient.queue)
    def assertPressRejected(self, press, sender, recipient):
        sender.queue = []
        msg = SND(recipient.power)(press)
        sender.send(msg)
        self.assertContains(REJ(msg), sender.queue)
    def assertPressHuhd(self, press, sender, recipient, error_loc):
        sender.queue = []
        msg = SND(recipient.power)(press)
        sender.send(msg)
        msg.insert(error_loc, ERR)
        self.assertContains(HUH(msg), sender.queue)
    def assertContains(self, item, series):
        self.failUnless(item in series,
                'Expected %r among %r' % (item, series))

class Server_Basics(ServerTestCase):
    ''' Basic Server Functionality'''
    def test_GOF_each_turn(self):
        ''' GOF should be assumed for each player each turn.'''
        self.set_option('MTL', 15)
        self.connect_server()
        players = []
        while not self.game.started:
            players.append(self.connect_player(self.Fake_Player))
        flagger = players[0]
        turn = self.game.judge.turn
        start_phase = turn().key
        flagger.send(NOT(GOF))
        for player in players: player.hold_all()
        self.game.run()
        self.failUnlessEqual(start_phase, turn().key)
        sleep(flagger.get_time() + 1)
        self.game.run()
        next_phase = turn().key
        self.failIfEqual(start_phase, next_phase)
        for player in players: player.hold_all()
        self.game.run()
        self.failIfEqual(next_phase, turn().key)
    def test_empty_MIS(self):
        ''' Server replies to MIS with MIS when no orders are outstanding.'''
        self.connect_server()
        sender = self.connect_player(self.Fake_Player)
        self.start_game()
        sender.hold_all()
        sender.queue = []
        sender.send(+MIS)
        self.assertContains(+MIS, sender.queue)
    def test_missing_orders_CCD(self):
        ''' Failing to submit orders on time results in a CCD message.'''
        self.set_option('MTL', 5)
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        self.start_game()
        sleep(player.get_time() + 1)
        self.game.run()
        self.assertContains(CCD(player.power) (SPR, 1901), player.queue)
    def test_submitted_orders_CCD(self):
        ''' Submitting orders on time avoids a CCD message.'''
        self.set_option('MTL', 5)
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        self.start_game()
        player.hold_all()
        sleep(player.get_time() + 1)
        self.game.run()
        self.failIf(player.power in sum([msg
            for msg in player.queue if msg[0] is CCD], []),
            '%s reported in civil disorder' % (player.power,))
    def test_historian(self):
        self.set_option('MTL', 5)
        self.set_option('send_ORD', True)
        self.connect_server()
        self.server.options.log_games = True
        game = self.start_game()
        game.run_judge()
        game.close()
        self.server.check_close()
        self.failIf(self.server.games.has_key(game.game_id))
        
        player = self.connect_player(self.Fake_Player,
                game_id=game.game_id, observe=True)
        self.assertContains(YES (SEL (game.game_id)), player.queue)
        player.queue = []
        player.send(HST(SPR, 1901))
        power = self.game.judge.map.powers.values()[0]
        self.assertContains(ORD (SPR, 1901) ([power.units[0]], HLD) (SUC),
                player.queue)
    def test_history_full(self):
        self.set_option('MTL', 5)
        self.set_option('send_ORD', True)
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        self.start_game()
        self.game.run_judge()
        player.queue = []
        player.send(+HST)
        power = self.game.judge.map.powers[player.power]
        self.assertContains(ORD (SPR, 1901) ([power.units[0]], HLD) (SUC),
                player.queue)
    def test_history_turn(self):
        self.set_option('MTL', 5)
        self.set_option('send_ORD', True)
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        self.start_game()
        self.game.run_judge()
        player.queue = []
        player.send(HST(SPR, 1901))
        power = self.game.judge.map.powers[player.power]
        self.assertContains(ORD (SPR, 1901) ([power.units[0]], HLD) (SUC),
                player.queue)
    def test_historian_map(self):
        self.set_option('MTL', 5)
        self.set_option('send_ORD', True)
        self.connect_server()
        self.server.options.log_games = True
        game = self.start_game()
        game.run_judge()
        game.close()
        self.server.check_close()
        self.failIf(self.server.games.has_key(game.game_id))
        
        player = self.connect_player(self.Fake_Player,
                game_id=game.game_id, observe=True)
        player.queue = []
        player.send(+MAP)
        self.assertContains(MAP (self.game.judge.map_name), player.queue)
    @failing(ValueError)  # Until the fleet_rome variant is included
    def test_historian_var(self):
        self.set_option('MTL', 5)
        self.set_option('send_ORD', True)
        self.set_option('variant', 'fleet_rome')
        self.connect_server()
        self.server.options.log_games = True
        game = self.start_game()
        game.run_judge()
        game.close()
        self.server.check_close()
        self.failIf(self.server.games.has_key(game.game_id))
        
        player = self.connect_player(self.Fake_Player,
                game_id=game.game_id, observe=True)
        player.queue = []
        player.send(+VAR)
        self.assertContains(VAR ("fleet_rome"), player.queue)
    def test_historian_sub(self):
        self.set_option('MTL', 5)
        self.set_option('send_ORD', True)
        self.connect_server()
        self.server.options.log_games = True
        game = self.start_game()
        game.run_judge()
        game.close()
        self.server.check_close()
        self.failIf(self.server.games.has_key(game.game_id))
        
        player = self.connect_player(self.Fake_Player,
                game_id=game.game_id, observe=True)
        player.queue = []
        power = game.judge.map.powers.values()[0]
        message = SUB ([power.units[0]], HLD)
        player.send(message)
        self.assertContains(REJ (message), player.queue)
    def test_save_game(self):
        self.set_option('send_ORD', True)
        self.connect_server()
        self.start_game()
        sco = self.game.judge.map.create_SCO()
        now = self.game.judge.map.create_NOW()
        self.game.run_judge()
        self.game.close()
        class Stream(list):
            def write(self, line): self.append(line)
        result = Stream()
        self.game.save(result)
        expected = [
            self.game.listing(),
            MAP (self.game.judge.map_name),
            VAR (self.game.judge.variant_name),
            self.game.variant.mdf(),
            HLO (OBS) (0) (self.game.game_options),
            sco,
            now,
        ] + sorted([
            ORD (SPR, 1901) ([unit], HLD) (SUC)
            for unit in self.game.judge.map.units
        ]) + [
            self.game.judge.map.create_NOW(),
            self.game.summarize()
        ]
        self.assertEqual([str(msg) + '\n' for msg in expected], result)
    def test_archive_game(self):
        self.connect_server()
        self.server.options.log_games = True
        self.start_game()
        self.game.run_judge()
        self.game.close()
        self.server.check_close()
        self.failUnless(self.game.saved)
        self.failIf(self.server.games)
    def test_summary_request(self):
        self.connect_server()
        self.set_option('bot_min', 0)
        master = self.connect_player(self.Fake_Master)
        master.admin('Server: start holdbots')
        self.wait_for_actions()
        master.send(+DRW)
        self.game.run_judge()
        master.queue = []
        master.send(+SMR)
        self.assertContains(+DRW, master.queue)
        self.assertEqual(SMR, master.queue[-1][0])
    def test_long_limits(self):
        limit = 5*60*60 + 30
        self.set_option('MTL', limit)
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        self.start_game()
        self.failUnlessEqual(player.game_opts.MTL, limit)
    def test_clock(self):
        limit = 5*60*60 + 30
        self.set_option('MTL', limit)
        times = []
        def catch_times(message):
            seconds = int(Time(*message.fold()[1]))
            times.append(seconds)
        
        self.connect_server()
        player = self.connect_player(Clock)
        player.handle_TME = catch_times
        game = self.start_game()
        sleep(12)
        game.run()
        self.failUnlessEqual(times, [limit, limit - 5, limit - 10])
    @failing(ValueError)  # Until the fleet_rome variant is included
    def test_variant_map_name(self):
        ''' Variants should use the name of the map in MAP messages.
            For example, Fleet Rome should use MAP ("standard").
        '''#'''
        self.set_option('variant', 'fleet_rome')
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        self.assertContains(MAP ("standard"), player.queue)
    @failing(ValueError)  # Until the fleet_rome variant is included
    def test_variant_name(self):
        ''' The server should answer a VAR command with the variant name.'''
        self.set_option('variant', 'fleet_rome')
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        player.send(+VAR)
        self.assertContains(VAR ("fleet_rome"), player.queue)

class Server_Press(ServerTestCase):
    ''' Press-handling tests'''
    def setUp(self):
        ServerTestCase.setUp(self)
        self.set_option('quit', False)
        self.set_option('shuffle', False)
        self.connect_server()
        self.sender = self.connect_player(self.Fake_Player) # Austria
        self.recipient = self.connect_player(self.Fake_Player) # England
        self.eliminated = self.connect_player(self.Fake_Player) # France
        self.disconnected = self.connect_player(self.Fake_Player) # Germany
        self.start_game()
        judge_map = self.game.judge.map
        now = judge_map.create_NOW()
        for index, token in enumerate(now):
            if token is self.eliminated.power:
                now[index] = self.disconnected.power
            elif token is SPR: now[index] = FAL
        judge_map.handle_NOW(now)
        self.disconnected.close()
        self.game.run_judge()
    def assertPressReply(self, press, response):
        self.sender.queue = []
        self.recipient.queue = []
        msg = SND(self.recipient.power)(press)
        self.sender.send(msg)
        reply = response(msg)
        self.assertContains(reply, self.sender.queue)
    def assertPressSent(self, press):
        self.assertPressReply(press, YES)
    def assertPressReceived(self, press):
        msg = FRM(self.sender.power)(self.recipient.power)(press)
        self.assertContains(msg, self.recipient.queue)
    def assertPressNotReceived(self, press):
        msg = FRM(self.sender.power)(self.recipient.power)(press)
        self.failIf(msg in self.recipient.queue,
                '"%s" accidentally sent.' % press)
    
    def test_send_press(self):
        ''' The server forwards press of the appropriate level.'''
        press = PRP(PCE(self.sender.power, self.recipient.power))
        self.assertPressSent(press)
        self.assertPressReceived(press)
    def test_send_try(self):
        ''' The server trims high-level tokens from TRY messages.'''
        self.assertPressSent(TRY(IOU, PRP, QRY))
        self.assertPressReceived(TRY(PRP))
    def test_send_eliminated(self):
        ''' The server rejects press including eliminated powers.'''
        out = self.eliminated.power
        press = PRP(ALY(self.sender.power, self.recipient.power) + VSS(out))
        self.assertPressReply(press, OUT(out))
        self.assertPressNotReceived(press)
    def test_send_to_eliminated(self):
        ''' The server rejects press to eliminated powers.'''
        self.recipient = self.eliminated
        out = self.eliminated.power
        press = PRP(ALY(self.sender.power, out) + VSS(self.disconnected.power))
        self.assertPressReply(press, OUT(out))
        self.assertPressNotReceived(press)
    def test_send_to_disconnected(self):
        ''' The server rejects press to disconnected powers.'''
        self.recipient = self.disconnected
        out = self.disconnected.power
        press = PRP(ALY(self.sender.power, out) + VSS(self.eliminated.power))
        self.assertPressReply(press, CCD(out))
        self.assertPressNotReceived(press)
    def test_send_mid(self):
        ''' The server accepts press with a message id, but does not send it.'''
        self.sender.queue = []
        self.recipient.queue = []
        press = PRP(PCE(self.sender.power, self.recipient.power))
        msg = SND(0)(self.recipient.power)(press)
        self.sender.send(msg)
        self.assertContains(YES(msg), self.sender.queue)
        self.assertPressReceived(press)
    def test_send_wrt(self):
        ''' The server accepts press with WRT, but does not send it.'''
        self.sender.queue = []
        self.recipient.queue = []
        press = PRP(PCE(self.sender.power, self.recipient.power))
        msg = SND(0)(self.recipient.power)(press)
        msg += WRT(self.recipient.power, 1)
        self.sender.send(msg)
        self.assertContains(YES(msg), self.sender.queue)
        self.assertPressReceived(press)

class Server_Admin(ServerTestCase):
    ''' Administrative messages handled by the server'''
    def setUp(self):
        ServerTestCase.setUp(self)
        self.set_option('quit', False)
        self.connect_server()
        self.master = self.connect_player(self.Fake_Master)
        self.backup = self.connect_player(self.Fake_Master)
        self.robot  = self.connect_player(self.Fake_Player)
    def assertAdminResponse(self, player, command, response):
        if command:
            self.assertContains(response, player.admin('Server: %s', command))
        else:
            self.assertContains(response,
                [msg.fold()[2][0] for msg in player.queue if msg[0] is ADM])
    def failIfAdminContains(self, player, substring):
        messages = [msg.fold()[2][0] for msg in player.queue if msg[0] is ADM]
        for item in messages:
            if substring in item:
                self.fail('%r found within %s' % (substring, messages))
    def assertAdminVetoable(self, player, command, response):
        self.assertEqual([response, '(You may veto within %s seconds.)' %
                    num2name(self.game_options['veto_time'])],
                player.admin('Server: %s', command))

class Server_Admin_Bots(Server_Admin):
    ''' Starting bots with admin commands'''
    def test_list_bots(self):
        items = self.master.admin('Server: list bots')
        self.failUnlessEqual('Available types of bots:', items[0])
        self.assertContains("  HoldBot - "
            "A simple bot that justs holds units in place.", items)
    def test_start_bot(self):
        ''' Players can start new bots in their current game.'''
        game = self.game
        count = len(game.clients)
        self.assertAdminVetoable(self.master, 'start holdbot',
                'Fake Human Player (Fake_Master) is starting a HoldBot.')
        self.wait_for_actions()
        self.failUnless(len(game.clients) > count)
        self.failIf(game.clients[-1].closed)
    def test_start_bot_a(self):
        ''' Players can start a bot using the indefinite article.'''
        game = self.game
        count = len(game.clients)
        self.assertAdminVetoable(self.master, 'start a holdbot',
                'Fake Human Player (Fake_Master) is starting a HoldBot.')
        self.wait_for_actions()
        self.failUnless(len(game.clients) > count)
        self.failIf(game.clients[-1].closed)
    def test_start_bot_an(self):
        ''' Players can start a bot using the article "an".'''
        # This no longer tests "an" in the response.
        # That requires either monkeypatching EntryPointContainer,
        # or shipping a bot whose name begins with a vowel.
        game = self.game
        count = len(game.clients)
        self.assertAdminVetoable(self.master, 'start an holdbot',
                'Fake Human Player (Fake_Master) is starting a HoldBot.')
        self.wait_for_actions()
        self.failUnless(len(game.clients) > count)
        self.failIf(game.clients[-1].closed)
    def test_start_bot_veto(self):
        ''' Bot starting can be vetoed.'''
        game = self.game
        count = len(game.clients)
        self.master.admin('Server: start holdbot')
        self.assertAdminResponse(self.robot, 'veto start',
                'Fake Player (Fake_Player) has vetoed the HoldBot.')
        self.wait_for_actions()
        self.failIf(len(game.clients) > count)
    def test_start_bot_replacement(self):
        ''' The master can start a bot to replace a disconnected power.'''
        game = self.start_game()
        out = self.robot
        out.close()
        self.master.admin('Ping.')
        name = game.judge.player_name(out.power)
        self.assertAdminVetoable(self.master,
                'start holdbot as %s' % (out.power,),
                'Fake Human Player (Fake_Master) is starting a HoldBot as %s.' % name)
        self.wait_for_actions()
        self.failUnless(game.players[out.power.key].client)
    def test_start_bot_country(self):
        ''' The master can start a bot to take a specific country.'''
        game = self.game
        old_client = game.players[ITA].client
        old_id = old_client and old_client.client_id
        self.assertAdminVetoable(self.master, 'start holdbot as italy',
                'Fake Human Player (Fake_Master) is starting a HoldBot as Italy.')
        self.wait_for_actions()
        new_client = game.players[ITA].client
        self.failUnless(new_client and new_client.client_id != old_id)
    def test_start_bot_illegal(self):
        ''' Bots cannot be started to take over players still in the game.'''
        game = self.start_game()
        old_client = game.players[ITA].client.client_id
        self.assertAdminResponse(self.master, 'start holdbot as Italy',
                'Italy is still in the game.')
        self.wait_for_actions()
        self.failUnlessEqual(game.players[ITA].client.client_id, old_client)
    def test_start_multiple_bots(self):
        ''' Exactly enough bots can be started to fill up the game.'''
        self.assertAdminVetoable(self.master, 'start holdbots',
                'Fake Human Player (Fake_Master) is starting four instances of HoldBot.')
        self.wait_for_actions()
        self.failUnless(self.game.started)
    def test_start_bot_blocking(self):
        ''' Bots can only be started in games with enough players.'''
        self.backup.close()
        self.robot.close()
        self.master.admin('Ping.')
        self.assertAdminResponse(self.master, 'start holdbots',
                'Recruit more players first, or use your own bots.')
    def test_start_bot_same_address(self):
        ''' Players are only counted if they're from different computers.'''
        for client in self.game.clients:
            client.address = 'localhost'
        self.assertAdminResponse(self.master, 'start holdbot',
                'Recruit more players first, or use your own bots.')

class Server_Admin_Local(Server_Admin):
    ''' Admin commands restricted to local connections'''
    def assertUnauthorized(self, player, command):
        self.assertAdminResponse(player, command,
                'You are not authorized to do that.')
    
    def setUp(self):
        Server_Admin.setUp(self)
        self.game.clients[1].address = '127.0.0.1'
    def test_shutdown_master(self):
        ''' Whether a non-local player can shut down the server'''
        self.assertUnauthorized(self.master, 'shutdown')
        self.failIf(self.server.closed)
    def test_shutdown_local(self):
        ''' Whether a local connection can shut down the server'''
        self.assertAdminResponse(self.backup, 'shutdown',
                'The server is shutting down.  Good-bye.')
        self.failUnless(self.server.closed)
    def test_status_request(self):
        ''' Whether a local connection can request game status information'''
        self.assertAdminResponse(self.backup, 'status',
                ('Game %s: Forming; ' % self.game.game_id) +
                'Have 3 players and 0 observers. Need 4 to start.')
    def test_power_listing(self):
        ''' Whether a local connection can power assignments'''
        game = self.game
        power = game.players[game.clients[1].country]
        self.assertAdminResponse(self.backup, 'powers',
                '%s (%d): Fake Human Player (Fake_Master), from 127.0.0.1'
                % (power.pname, power.passcode))

class Server_Admin_Press(Server_Admin):
    ''' Admin commands to change the press level of a game'''
    
    def test_press_enable(self):
        ''' The enable press admin command works'''
        self.assertAdminResponse(self.master, 'enable press',
                'Fake Human Player (Fake_Master) has set the press level to 8000 (Free Text).')
        self.wait_for_actions()
        sender = self.backup
        recipient = self.robot
        self.start_game()
        
        # Level 10 succeeds
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressSent(offer, sender, recipient)
        # Level 40 succeeds
        offer2 = PRP(SCD(sender.power, LON) (recipient.power, PAR))
        self.assertPressSent(offer2, sender, recipient)
        # Level 60 succeeds
        offer[0] = SUG
        self.assertPressSent(offer, sender, recipient)
    def test_press_enable_number(self):
        ''' The enable press admin command works with a numeric level'''
        self.assertAdminResponse(self.master, 'enable press level 40',
                'Fake Human Player (Fake_Master) has set the press level to 40 (Sharing out the Supply Centres).')
        self.wait_for_actions()
        sender = self.backup
        recipient = self.robot
        self.start_game()
        
        # Level 10 succeeds
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressSent(offer, sender, recipient)
        # Level 40 succeeds
        offer2 = PRP(SCD(sender.power, LON) (recipient.power, PAR))
        self.assertPressSent(offer2, sender, recipient)
        # Level 60 fails
        offer[0] = SUG
        self.assertPressHuhd(offer, sender, recipient, 5)
    def test_press_enable_verbal(self):
        ''' The enable press admin command works with a verbal level'''
        self.assertAdminResponse(self.master,
                'enable press level Sharing out the supply centres',
                'Fake Human Player (Fake_Master) has set the press level to 40 (Sharing out the Supply Centres).')
        self.wait_for_actions()
        sender = self.backup
        recipient = self.robot
        self.start_game()
        
        # Level 10 succeeds
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressSent(offer, sender, recipient)
        # Level 40 succeeds
        offer2 = PRP(SCD(sender.power, LON) (recipient.power, PAR))
        self.assertPressSent(offer2, sender, recipient)
        # Level 60 fails
        offer[0] = SUG
        self.assertPressHuhd(offer, sender, recipient, 5)
    def test_press_disable(self):
        ''' The disable press admin command works'''
        self.assertAdminResponse(self.master, 'disable press',
                'Fake Human Player (Fake_Master) has set the press level to 0 (No Press).')
        self.wait_for_actions()
        sender = self.backup
        recipient = self.robot
        self.start_game()
        
        # Level 10 fails
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressHuhd(offer, sender, recipient, 0)
    def test_press_enable_blocked(self):
        ''' The enable press command is blocked after the game starts.'''
        sender = self.backup
        recipient = self.robot
        self.start_game()
        self.assertAdminResponse(self.master, 'enable press',
                'The press level can only be changed before the game starts.')
        self.wait_for_actions()
        
        # Level 10 succeeds
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressSent(offer, sender, recipient)
        # Level 40 fails
        offer2 = PRP(SCD(sender.power, LON) (recipient.power, PAR))
        self.assertPressHuhd(offer2, sender, recipient, 7)
        # Level 60 fails
        offer[0] = SUG
        self.assertPressHuhd(offer, sender, recipient, 5)
    def test_press_disable_blocked(self):
        ''' The disable admin command is blocked after the game starts.'''
        sender = self.backup
        recipient = self.robot
        self.start_game()
        self.assertAdminResponse(self.master, 'disable press',
                'The press level can only be changed before the game starts.')
        self.wait_for_actions()
        
        # Level 10 succeeds
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressSent(offer, sender, recipient)
        # Level 40 fails
        offer2 = PRP(SCD(sender.power, LON) (recipient.power, PAR))
        self.assertPressHuhd(offer2, sender, recipient, 7)
        # Level 60 fails
        offer[0] = SUG
        self.assertPressHuhd(offer, sender, recipient, 5)

class Server_Admin_Eject(Server_Admin):
    def test_eject_player_unstarted(self):
        ''' Players can be ejected from a forming game.'''
        self.assertAdminVetoable(self.master, 'eject Fake Player',
                'Fake Human Player (Fake_Master) is ejecting Fake Player from the game.')
        self.wait_for_actions()
        self.assertAdminResponse(self.master, None,
                'Fake Player (Fake_Player) has disconnected. '
                'Have 2 players and 0 observers. Need 5 to start.')
    def test_eject_player_started(self):
        ''' A player can be ejected by name after the game starts.'''
        game = self.game
        while not game.started: self.connect_player(HoldBot)
        self.assertAdminVetoable(self.master, 'eject Fake Player',
                'Fake Human Player (Fake_Master) is ejecting Fake Player from the game.')
        self.wait_for_actions()
        self.assertContains(CCD(self.robot.power), self.master.queue)
    def test_eject_multiple_unstarted(self):
        ''' Multiple players of the same name can be ejected before the game starts.'''
        self.connect_player(self.Fake_Player)
        self.assertAdminVetoable(self.master, 'eject Fake Player',
                'Fake Human Player (Fake_Master) is ejecting two instances of Fake Player from the game.')
        self.wait_for_actions()
        self.assertAdminResponse(self.master, None,
                'Fake Player (Fake_Player) has disconnected. '
                'Have 2 players and 0 observers. Need 5 to start.')
    def test_eject_multiple_started(self):
        ''' Multiple players of the same name cannot be ejected after the game starts.'''
        self.start_game()
        self.assertAdminResponse(self.master, 'eject Fake Player',
                'Ambiguous player "Fake player"')
    def test_eject_power_unstarted(self):
        ''' Powers cannot be ejected by power name before the game starts.'''
        game = self.game
        name = game.judge.player_name(game.p_order[2])
        self.assertAdminResponse(self.master, 'eject ' + name,
                'Unknown player "%s"' % name)
    def test_eject_power_started(self):
        ''' Powers can be ejected by power name after the game starts.'''
        game = self.start_game()
        name = game.judge.player_name(self.robot.power)
        self.assertAdminVetoable(self.master, 'eject ' + name,
                'Fake Human Player (Fake_Master) is ejecting %s from the game.' % name)
        self.wait_for_actions()
        self.assertContains(CCD(self.robot.power), self.master.queue)
    
    def test_eject_player_veto(self):
        ''' Player ejection can be vetoed by a third party.'''
        self.master.admin('Server: eject Fake Player')
        self.assertAdminResponse(self.backup, 'veto eject',
                'Fake Human Player (Fake_Master) has vetoed the player ejection.')
        self.wait_for_actions()
        self.failIfAdminContains(self.master, 'disconnected')
    def test_eject_self_veto(self):
        ''' Player ejection can be vetoed by the ejected player.'''
        self.master.admin('Server: eject Fake Player')
        self.assertAdminResponse(self.robot, 'veto eject',
                'Fake Player (Fake_Player) has vetoed the player ejection.')
        self.wait_for_actions()
        self.failIfAdminContains(self.master, 'disconnected')
    def test_boot_player_unstarted(self):
        ''' Players can be ejected using 'boot' as well as 'eject'.'''
        self.assertAdminVetoable(self.master, 'boot Fake Player',
                'Fake Human Player (Fake_Master) is booting Fake Player from the game.')
    def test_boot_self_veto(self):
        ''' Player booting cannot be vetoed by the booted player.'''
        self.master.admin('Server: boot Fake Player')
        self.assertAdminResponse(self.robot, 'veto boot',
                "You can't veto your own booting.")
        self.wait_for_actions()
        self.assertAdminResponse(self.master, None,
                'Fake Player (Fake_Player) has disconnected. '
                'Have 2 players and 0 observers. Need 5 to start.')

class Server_Admin_Other(Server_Admin):
    ''' Other administrative messages handled by the server'''
    help_line = '  help - Lists admin commands recognized by the server'
    
    def test_pause(self):
        ''' Players can pause the game.'''
        game = self.start_game()
        self.assertAdminResponse(self.master, 'pause',
                'Fake Human Player (Fake_Master) has paused the game.')
        self.failUnless(game.paused)
        self.assertEqual(self.master.get_time(), None)
    def test_resume(self):
        ''' Players can resume a paused game.'''
        game = self.start_game()
        start = self.master.get_time()
        self.master.admin('Server: pause')
        sleep(7)
        self.assertAdminVetoable(self.master, 'resume',
                'Fake Human Player (Fake_Master) is resuming the game.')
        self.wait_for_actions()
        self.failIf(game.paused)
        end = self.master.get_time()
        self.failUnless(0 <= start - end <= 2,
                'Time difference: %g' % (start - end))
    def test_resume_veto_resume(self):
        ''' An resume command can be vetoed with "veto resume".'''
        game = self.start_game()
        start = self.master.get_time()
        self.master.admin('Server: pause')
        sleep(7)
        self.master.admin('Server: resume')
        self.assertAdminResponse(self.robot, 'veto resume',
                'Fake Player (Fake_Player) has vetoed resuming the game.')
        self.wait_for_actions()
        self.failUnless(game.paused)
        self.assertEqual(self.master.get_time(), None)
    def test_resume_veto(self):
        ''' A resume command can be vetoed with "veto".'''
        game = self.start_game()
        start = self.master.get_time()
        self.master.admin('Server: pause')
        sleep(7)
        self.master.admin('Server: resume')
        self.assertAdminResponse(self.robot, 'veto',
                'Fake Player (Fake_Player) has vetoed resuming the game.')
        self.wait_for_actions()
        self.failUnless(game.paused)
        self.assertEqual(self.master.get_time(), None)
    
    def test_end_cleanup(self):
        ''' Someone can connect to an abandoned game and end it.'''
        game = self.start_game()
        self.master.close()
        self.backup.close()
        self.robot.admin('Ping')
        new_master = self.connect_player(self.Fake_Master,
                power=self.master.power, passcode=self.master.pcode)
        self.assertAdminVetoable(new_master, 'end game',
                'Fake Human Player (Fake_Master) is ending the game.')
        self.wait_for_actions()
        self.failUnless(game.closed)
    def test_end_veto_end(self):
        ''' An end game command can be vetoed with "veto end game".'''
        game = self.start_game()
        self.master.admin('Server: end game')
        self.assertAdminResponse(self.robot, 'veto end game',
                'Fake Player (Fake_Player) has vetoed ending the game.')
        self.wait_for_actions()
        self.failIf(game.closed)
    def test_end_veto(self):
        ''' An end game command can be vetoed with "veto".'''
        game = self.start_game()
        self.master.admin('Server: end game')
        self.assertAdminResponse(self.robot, 'veto',
                'Fake Player (Fake_Player) has vetoed ending the game.')
        self.wait_for_actions()
        self.failIf(game.closed)
    
    def test_unknown_variant(self):
        self.assertAdminResponse(self.master, 'new unknown_variant game',
                'Unknown variant "unknown_variant"')
        self.failUnlessEqual(len(self.server.games), 1)
    def test_list_variants(self):
        items = self.master.admin('Server: list variants')
        self.assertContains('Known map variants: ', items[0])
        self.assertContains('standard', items[0])
    def test_help(self):
        self.assertAdminResponse(self.master, 'help', self.help_line)
    def test_help_caps(self):
        self.assertContains(self.help_line, self.master.admin('HELP'))
    def test_help_server_caps(self):
        self.assertContains(self.help_line, self.master.admin('SERVER: HELP'))
    
    def test_who(self):
        ''' Player names can be listed, without reference to power.'''
        response = self.master.admin('Server: who')
        self.assertEqual(response, [
                'Players:',
                '  Fake Human Player (Fake_Master)',
                '  Fake Human Player (Fake_Master)',
                '  Fake Player (Fake_Player)',
        ], response)
    
    def test_set_time_limit(self):
        self.assertAdminResponse(self.master, 'move time limit 30',
                'Fake Human Player (Fake_Master)'
                ' has set the move time limit to 30 seconds.')
        self.start_game()
        self.assertContains(HLO (self.master.power) (self.master.pcode)
                ((LVL, 20), (MTL, 30)), self.master.queue)
        self.assertContains(TME (30), self.master.queue)
    def test_get_time_limit(self):
        self.assertAdminResponse(self.master, 'move time limit',
                'The move time limit is 60 seconds.')
    def test_time_limit_phase(self):
        self.assertAdminResponse(self.master, 'SPR time limit',
                "Unknown phase 'spr'; try move, build, retreat, or press.")

class Server_Multigame(ServerTestCase):
    def setUp(self):
        ServerTestCase.setUp(self)
        self.connect_server()
        self.master = self.connect_player(self.Fake_Master)
    def new_game(self, variant=None):
        self.master.admin('Server: new%s game' %
                (variant and ' '+variant or ''))
        return self.server.default_game()
    def test_new_game(self):
        self.new_game()
        self.failUnlessEqual(len(self.server.games), 2)
        self.connect_player(self.Fake_Player)
        self.failUnless(len(self.server.default[1].clients))
    def test_start_game(self):
        self.master.admin('Server: start standard game')
        self.failUnlessEqual(len(self.server.games), 2)
    def test_second_connection(self):
        self.new_game()
        self.failUnlessEqual(len(self.server.games), 2)
        self.connect_player(self.Fake_Player)
        self.connect_player(self.Fake_Player)
        self.failUnlessEqual(len(self.server.default[1].clients), 2)
    def test_old_reconnect(self):
        game = self.new_game()
        self.failUnlessEqual(len(self.server.games), 2)
        game.close()
        self.connect_player(self.Fake_Player)
        self.failUnlessEqual(len(self.server.default[0].clients), 2)
    def test_old_bot_connect(self):
        ''' Starting a bot connects it to your game, not the current one.'''
        game = self.server.default_game()
        self.connect_player(self.Fake_Player)
        self.new_game()
        self.master.admin('Server: start holdbot')
        self.wait_for_actions(game)
        self.failUnlessEqual(len(game.clients), 3)
    @fails  # Until the sailho variant is included
    def test_sailho_game(self):
        self.new_game('sailho')
        self.failUnlessEqual(len(self.server.games), 2)
        player = self.connect_player(self.Fake_Player)
        self.assertContains(MAP('sailho'), player.queue)
    def test_RM_change(self):
        old_rep = self.game.variant.rep
        old_id = self.game.game_id
        self.new_game('sailho')
        newbie = self.connect_player(self.Fake_Player, game_id=old_id)
        self.failUnlessEqual(newbie.rep, old_rep)
    
    def test_SEL_reply(self):
        self.master.queue = []
        self.master.send(+SEL)
        self.assertContains(SEL(self.game.game_id), self.master.queue)
    def test_LST_reply(self):
        self.master.queue = []
        self.master.send(+LST)
        params = self.game.game_options.get_params()
        self.assertContains(
                LST (self.game.game_id) (6, NME) ('standard') (params),
                self.master.queue)
        self.assertEqual(YES (LST), self.master.queue[-1])
    @fails  # Until the sailho variant is included
    def test_multigame_LST_reply(self):
        std_params = self.game.game_options.get_params()
        game_id = self.game.game_id
        game = self.new_game('sailho')
        self.master.queue = []
        self.master.send(+LST)
        sailho_params = game.game_options.get_params()
        self.assertContains(
                LST (game_id) (6, NME) ('standard') (std_params),
                self.master.queue)
        self.assertContains(
                LST (game.game_id) (4, NME) ('sailho') (sailho_params),
                self.master.queue)
    def test_single_LST_reply(self):
        std_params = self.game.game_options.get_params()
        game_id = self.game.game_id
        game = self.new_game('sailho')
        self.master.queue = []
        self.master.send(LST(game_id))
        sailho_params = game.game_options.get_params()
        self.assertEqual(
                LST (game_id) (6, NME) ('standard') (std_params),
                self.master.queue[-1])

class Server_Bugfix(ServerTestCase):
    ''' Test cases to reproduce bugs found.'''
    def test_robotic_key_error(self):
        # Introduced in revision 93; crashes the server.
        self.connect_server()
        master = self.connect_player(self.Fake_Master)
        master.admin('Server: start holdbot as %s', self.game.p_order[0])
        master.admin('Server: start 5 holdbots')
        self.connect_player(self.Fake_Player)
    def test_hello_leak(self):
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        player.send(+HLO)
        for message in player.queue:
            if message[0] is HLO: self.fail('Server sent HLO before game start')
    def test_admin_forward(self):
        self.connect_server()
        sender = self.connect_player(self.Fake_Player)
        recipient = self.connect_player(self.Fake_Player)
        sender.admin('Ping.')
        self.assertContains(ADM(sender.name)('Ping.'), recipient.queue)
    def test_NPR_press_block(self):
        ''' The NPR parameter should block press during retreat phases.
            A code overview revealed that it probably doesn't.
        '''#'''
        self.set_option('NPR', True)
        self.connect_server()
        sender = self.connect_player(self.Fake_Player)
        recipient = self.connect_player(self.Fake_Player)
        game = self.start_game()
        game.judge.phase = Turn.retreat_phase
        game.set_deadlines()
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressRejected(offer, sender, recipient)
    def test_NPR_press_allow(self):
        ''' The NPR parameter should block press during retreat phases.
            A code overview revealed that it probably doesn't.
        '''#'''
        self.set_option('NPR', False)
        self.connect_server()
        sender = self.connect_player(self.Fake_Player)
        recipient = self.connect_player(self.Fake_Player)
        game = self.start_game()
        game.judge.phase = Turn.retreat_phase
        game.set_deadlines()
        offer = PRP(PCE(sender.power, recipient.power))
        self.assertPressSent(offer, sender, recipient)
    def test_DSD_reconnect(self):
        ''' The server should resume a paused game when all players reconnect.
        '''#'''
        self.set_option('DSD', True)
        self.set_option('quit', False)
        self.connect_server()
        player = self.connect_player(self.Fake_Player)
        control = self.connect_player(self.Fake_Player)
        game = self.start_game()
        player.close()
        control.admin('Ping.')
        self.wait_for_actions()
        self.failUnless(game.paused)
        self.connect_player(self.Fake_Player,
                power=player.power, passcode=player.pcode)
        self.wait_for_actions()
        self.failIf(game.paused)
    
if __name__ == '__main__': unittest.main()
