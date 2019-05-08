r'''Test cases for Parlance clients
    Copyright (C) 2004-2008  Eric Wald
    
    This module tests the basic client classes of the framework, as well as
    the HoldBot player based on them.  Other bots should have their own test
    scripts, but may use the tests in here as a base.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import unittest

from parlance.config     import Configuration, GameOptions
from parlance.functions  import fails
from parlance.language   import Token
from parlance.player     import AutoObserver, Player, HoldBot
from parlance.tokens     import *
from parlance.validation import Validator
from parlance.xtended    import ENG, FRA, GER, standard

class NumberToken(object):
    def __eq__(self, other):
        if isinstance(other, Token): return other.is_integer()
        else: return NotImplemented
    def tokenize(self): return [self]
    def __repr__(self): return 'NumberToken'
    def __radd__(self, other): return other + ' #'
Number = NumberToken()

class PlayerTestCase(unittest.TestCase):
    ''' Basic Player Functionality'''
    
    game_options = {
        'LVL': 8000,
        'PDA': True,
        'variant' : 'standard',
        'quit' : True,
        'host' : '',
        'send_SET': False,
        'send_ORD': False,
        'draw': 3,
        'response': 'die',
    }
    def setUp(self):
        ''' Initializes class variables for test cases.'''
        self.set_verbosity(0)
        Configuration._cache.update(self.game_options)
        self.variant = standard
        opts = GameOptions()
        self.params = opts.get_params()
        self.level = opts.LVL
        self.validator = Validator(opts.LVL)
        self.player = None
        self.replies = []
    def handle_message(self, message):
        #print message
        reply = self.validator.validate_client_message(message)
        self.failIf(reply, reply)
        self.replies.append(message)
    def tearDown(self):
        if self.player: self.send(+OFF)
    def set_verbosity(self, verbosity):
        Configuration.set_globally('verbosity', verbosity)
    def send(self, message): self.player.handle_message(message)
    def accept(self, message): self.send(YES(message))
    def reject(self, message): self.send(REJ(message))
    def connect_player(self, player_class, **kwargs):
        self.player = player_class(send_method=self.handle_message,
                representation=self.variant.rep, **kwargs)
        self.player.register()
        self.player.threaded = []
    def send_hello(self, country=None):
        self.send(HLO(country or ENG)(self.level)(self.params))
    def seek_reply(self, message, error=None):
        while self.replies:
            msg = self.replies.pop(0)
            if msg == message: break
        else: self.fail(error or 'Expected: ' + str(message))
    def start_game(self):
        while self.replies:
            msg = self.replies.pop(0)
            if msg[0] is NME: self.accept(msg); break
        else: self.fail('No NME message')
        self.send(MAP(self.variant.mapname))
        while self.replies:
            msg = self.replies.pop(0)
            if msg[0] is MDF: self.send(self.variant.map_mdf)
            elif msg[0] is YES and msg[2] is MAP: break
        else: self.fail('Failed to accept the map')
        self.send_hello()
        self.send(self.variant.sco())
        self.send(self.variant.now())
    def assertContains(self, item, series):
        self.failUnless(item in series, 'Expected %r among %r' % (item, series))

class Player_Tests(PlayerTestCase):
    class Test_Player(Player):
        def handle_REJ_YES(self, message): self.send(+HLO)
        def handle_press_THK(self, sender, press):
            self.send_press(sender, WHY(press))
        def handle_press_SUG(self, *args):
            raise NotImplementedError, 'Intentionally raising an error.'
        def generate_orders(self): pass
    def test_press_response(self):
        self.connect_player(self.Test_Player)
        self.start_game()
        self.replies = []
        offer = PRP(PCE(ENG, FRA))
        self.send(FRM(FRA)(ENG)(offer))
        self.seek_reply(SND(FRA)(HUH(ERR + offer)))
        self.seek_reply(SND(FRA)(TRY()))
    def test_press_response_legacy(self):
        # Same as above, but with WRT syntax
        # Note that this only works with validation off.
        self.connect_player(self.Test_Player)
        self.start_game()
        self.replies = []
        offer = THK(PCE(ENG, GER))
        self.player.validator = None
        self.send(FRM(FRA, 0)(ENG)(offer) + WRT(ENG, 0))
        self.seek_reply(SND(FRA)(WHY(offer)))
    def test_validate_option(self):
        # Todo: Fix this test to actually test the client_opts option again.
        self.connect_player(self.Test_Player)
        validator = self.player.validator
        self.player.validator = None
        self.send(REJ(YES))
        self.seek_reply(+HLO)
        self.failIf(self.player.closed)
        self.player.validator = validator or Validator()
        self.send(REJ(YES))
        self.failUnless(self.player.closed)
    @fails  # Until the fleet_rome variant is included
    def test_known_map(self):
        self.connect_player(self.Test_Player)
        self.seek_reply(NME (self.player.name) (self.player.version))
        self.send(MAP('fleet_rome'))
        self.seek_reply(YES(MAP('fleet_rome')))
    def test_unknown_map(self):
        self.connect_player(self.Test_Player)
        self.seek_reply(NME (self.player.name) (self.player.version))
        self.send(MAP('unknown'))
        self.seek_reply(+MDF)
        self.send(standard.mdf())
        self.seek_reply(YES(MAP('unknown')))
    def test_HLO_PDA(self):
        ''' The HLO message should be valid with level 10 parameters.'''
        self.connect_player(self.Test_Player)
        if not self.player.validator: self.player.validator = Validator()
        self.start_game()
        self.failIf(self.player.closed)
    def test_press_error(self):
        ''' Errors in handle_press methods should send HUH(message ERR) press.'''
        self.connect_player(self.Test_Player)
        self.start_game()
        offer = SUG(DRW)
        self.send(FRM(GER)(ENG)(offer))
        self.seek_reply(SND(GER)(HUH(offer ++ ERR)))
    def test_AutoObserver(self):
        ''' Former doctests of the AutoObserver class.'''
        result = []
        def handle_message(msg):
            if msg[0] is ADM:
                result.append(msg)
                player.handle_ADM(msg)
        player = AutoObserver(send_method=handle_message,
                representation=self.variant.rep)
        player.handle_ADM(ADM('Server')('An Observer has connected. '
            'Have 5 players and 1 observers. Need 2 to start'))
        player.handle_ADM(ADM('Geoff')('Does the observer want to play?'))
        self.failUnlessEqual(result[-1],
                ADM ( "AutoObserver" ) ( "Sorry; I'm just a bot." ))
        player.handle_ADM(ADM('Geoff')('Are you sure about that?'))
        self.failUnlessEqual(result[-1],
                ADM ( "AutoObserver" ) ( "Yes, I'm sure." ))
        player.handle_ADM(ADM('DanM')('Do any other observers care to jump in?'))
        self.failUnlessEqual(len(result), 2)
    def test_uppercase_mapname(self):
        ''' Clients should recognize map names in upper case.'''
        self.connect_player(self.Test_Player)
        while self.replies:
            msg = self.replies.pop(0)
            if msg[0] is NME: self.accept(msg); break
        else: self.fail('No NME message')
        msg = MAP(self.variant.mapname.upper())
        self.send(msg)
        self.seek_reply(YES(msg))
    def test_HUH_bounce(self):
        ''' A client should deal with HUH response to its HUH message.'''
        Configuration.set_globally('validate', True)
        Configuration.set_globally('response', 'complain')
        #self.set_verbosity(7)
        self.connect_player(self.Test_Player)
        while self.replies:
            msg = self.replies.pop(0)
            if msg[0] is NME: self.accept(msg); break
        else: self.fail('No NME message')
        # Syntactically incorrect message, just to prompt HUH
        self.send(MAP(0))
        self.seek_reply(HUH(MAP(ERR, 0)))
        self.send(HUH(ERR, HUH(MAP(ERR, 0))))
        self.failUnlessEqual(self.replies, [])

class Player_HoldBot(PlayerTestCase):
    def setUp(self):
        PlayerTestCase.setUp(self)
        self.connect_player(HoldBot)
    def test_press_response(self):
        self.start_game()
        self.replies = []
        offer = PRP(PCE(ENG, FRA))
        self.send(FRM(FRA)(ENG)(offer))
        self.seek_reply(SND(FRA)(HUH(ERR + offer)))
        self.seek_reply(SND(FRA)(TRY()))

class Player_Bots(PlayerTestCase):
    def connect_player(self, bot_class):
        PlayerTestCase.connect_player(self, bot_class)
        def handle_THX(player, message):
            ''' Fail on bad order submission.'''
            folded = message.fold()
            result = folded[2][0]
            if result != MBV:
                self.fail('Invalid order submitted: ' + str(message))
        def handle_MIS(player, message):
            ''' Fail on incomplete order submission.'''
            self.fail('Missing orders: ' + str(message))
        self.player.handle_THX = handle_THX
        self.player.handle_MIS = handle_MIS
    def attempt_one_phase(self, bot_class):
        ''' Demonstrates that the given bot can at least start up
            and submit a complete set of orders for the first season.
        '''#'''
        self.connect_player(bot_class)
        self.start_game()
        result = [message[0] for message in self.replies]
        self.assertContains(SUB, result)
        self.failIf(HUH in result)
    
    def test_holdbot(self):
        self.attempt_one_phase(HoldBot)

if __name__ == '__main__': unittest.main()
