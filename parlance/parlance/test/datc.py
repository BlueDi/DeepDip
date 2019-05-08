r'''DATC test cases for the Parlance judge
    Copyright (C) 2001-2008  Lucas B. Kruijswijk and Eric Wald
    
    Some of these cases test DATC options that have not yet been implemented.
    However, enough pass to certify this adjudicator as correct.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import unittest

from parlance.config    import Configuration, GameOptions, variants
from parlance.functions import fails
from parlance.language  import Message
from parlance.tokens    import *
from parlance.xtended   import *

class DiplomacyAdjudicatorTestCase(unittest.TestCase):
    ''' Unit Test base class for testing Diplomacy adjudication.
        Subclasses may override variant_name and game_options;
        these variables are used to set up the judge,
        which is available as self.judge in test functions.
        The default game options set the syntax level to zero
        and leave all other options as language defaults.
    '''#'''
    # The variant to use, as accepted by variant_options
    variant_name = 'standard'
    
    # A dict of game options
    game_options = {'LVL': 0}
    
    def setUp(self):
        ''' Initializes class variables for test cases.'''
        self.set_verbosity(0)
        Configuration._cache.update(self.game_options)
        variant = variants[self.variant_name]
        self.judge = variant.new_judge(GameOptions())
        self.judge.start()
    def set_verbosity(self, verbosity):
        Configuration.set_globally('verbosity', verbosity)
    def init_state(self, season, year, unit_list):
        self.judge.map.handle_NOW(NOW(season, year) % unit_list)
        self.judge.init_turn()
    def chown_sc(self, owner, sc_list):
        # Todo: This could more efficiently change the map itself...
        newsco = self.judge.map.create_SCO()
        idx = newsco.index(owner)
        for center in sc_list:
            newsco.remove(center)
            newsco.insert(idx + 1, center)
        self.judge.map.handle_SCO(newsco)
    
    class Fake_Service:
        ''' Emulates the essentials of a Service object,
            from the Judge's perspective.
            Allows tests to retrieve messages sent to it.
        '''#'''
        def __init__(self, country):
            self.country = country
            self.replies = []
        def send(self, message): self.replies.append(message)
        def send_list(self, message_list): self.replies.extend(message_list)
        def accept(self, message): self.send(YES(message))
        def reject(self, message): self.send(REJ(message))
    def submitOrder(self, country, order):
        client = self.Fake_Service(country)
        self.judge.handle_SUB(client, SUB(order))
        reply = client.replies[0]
        if reply[0] == THX: return reply[-2]
        else:               return reply[0]
    def assertIllegalOrder(self, country, order):
        note = self.submitOrder(country, order)
        self.failIfEqual(note, MBV)
    def assertLegalOrder(self, country, order):
        note = self.submitOrder(country, order)
        self.failUnlessEqual(note, MBV)
    # Comment out two of the following four lines,
    # depending on whether you care about the judge's error code.
    #illegalOrder  = submitOrder
    #legalOrder    = submitOrder
    illegalOrder = assertIllegalOrder
    legalOrder   = assertLegalOrder
    
    def assertContains(self, container, item):
        if item not in container:
            raise self.failureException, '%s not in %s' % (item, container)
    def assertMapState(self, unit_list):
        ''' Runs the judge and tests for the desired outcome.
            For retreating units, omit the list of available retreats,
            but keep the MRT token.
        '''#'''
        self.results = self.judge.run()
        map_units = [unit[:4] for msg in self.results
                for unit in msg.fold()[2:] if msg[0] is NOW]
        for item in unit_list: self.assertContains(map_units, item)
        for item in map_units: self.assertContains(unit_list, item)

class DATC_6_A(DiplomacyAdjudicatorTestCase):
    "6.A.  BASIC CHECKS"
    
    def test_6A1(self):
        "6.A.1.  MOVING TO AN AREA THAT IS NOT A NEIGHBOUR"
        self.illegalOrder(ENG, [(ENG, FLT, NTH), MTO, PIC])
    def test_6A2(self):
        "6.A.2.  MOVE ARMY TO SEA"
        self.illegalOrder(ENG, [(ENG, AMY, LVP), MTO, IRI])
    def test_6A3(self):
        "6.A.3.  MOVE FLEET TO LAND"
        self.illegalOrder(GER, [(GER, FLT, KIE), MTO, MUN])
    def test_6A4(self):
        "6.A.4.  MOVE TO OWN SECTOR"
        self.illegalOrder(GER, [(GER, FLT, KIE), MTO, KIE])
    def test_6A5(self):
        "6.A.5.  MOVE TO OWN SECTOR WITH CONVOY"
        self.init_state(SPR, 1901, [
            [ENG, AMY, LVP],
            [ENG, AMY, YOR],
            [ENG, FLT, NTH],
            [GER, FLT, LON],
            [GER, AMY, WAL],
        ])
        self.illegalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, YOR), CTO, YOR])
        self.illegalOrder(ENG, [(ENG, AMY, YOR), CTO, YOR, VIA, [NTH]])
        self.illegalOrder(ENG, [(ENG, AMY, LVP), SUP, (ENG, AMY, YOR), MTO, YOR])
        self.legalOrder(GER, [(GER, FLT, LON), MTO, YOR])
        self.legalOrder(GER, [(GER, AMY, WAL), SUP, (GER, FLT, LON), MTO, YOR])
        self.assertMapState([
            [ENG, AMY, LVP],
            [ENG, FLT, NTH],
            [GER, FLT, YOR],
            [GER, AMY, WAL],
            [ENG, AMY, YOR, MRT],
        ])
    def test_6A5_old(self):
        "6.A.5.old  MOVE TO OWN SECTOR WITH CONVOY"
        start_state = [
            [ENG, FLT, LON],
            [ENG, FLT, NTH],
            [ENG, AMY, YOR],
            [ENG, AMY, LVP],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), MTO, YOR])
        self.illegalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, YOR), CTO, YOR])
        self.illegalOrder(ENG, [(ENG, AMY, YOR), CTO, YOR, VIA, [NTH]])
        self.illegalOrder(ENG, [(ENG, AMY, LVP), SUP, (ENG, AMY, YOR), MTO, YOR])
        self.assertMapState(start_state)
    def test_6A6(self):
        "6.A.6.  ORDERING A UNIT OF ANOTHER COUNTRY"
        start_state = [
            [ENG, FLT, LON],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(GER, [(ENG, FLT, LON), MTO, NTH])
        self.assertMapState(start_state)
    def test_6A6_modified(self):
        ''' 6.A.6.modified  ORDERING A UNIT OF ANOTHER COUNTRY
            Differs from the above in the country specification of the unit.
        '''#'''
        start_state = [
            [ENG, FLT, LON],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(GER, [(GER, FLT, LON), MTO, NTH])
        self.assertMapState(start_state)
    def test_6A7(self):
        "6.A.7.  ONLY ARMIES CAN BE CONVOYED"
        start_state = [
            [ENG, FLT, LON],
            [ENG, FLT, NTH],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(ENG, [(ENG, FLT, LON), CTO, BEL, VIA, [NTH]])
        self.illegalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.assertMapState(start_state)
    def test_6A7_modified(self):
        ''' 6.A.7.modified  ONLY ARMIES CAN BE CONVOYED
            Differs from the above in the type specification of the unit.
        '''#'''
        start_state = [
            [ENG, FLT, LON],
            [ENG, FLT, NTH],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(ENG, [(ENG, FLT, LON), CTO, BEL, VIA, [NTH]])
        self.illegalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, FLT, LON), CTO, BEL])
        self.assertMapState(start_state)
    def test_6A8(self):
        "6.A.8.  SUPPORT TO HOLD YOURSELF IS NOT POSSIBLE"
        self.init_state(SPR, 1901, [
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
            [AUS, FLT, TRI],
        ])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, TYR), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.illegalOrder(AUS, [(AUS, FLT, TRI), SUP, (AUS, FLT, TRI)])
        self.assertMapState([
            [ITA, AMY, TRI],
            [ITA, AMY, TYR],
            [AUS, FLT, TRI, MRT],
        ])
    def test_6A9(self):
        "6.A.9.  FLEETS MUST FOLLOW COAST IF NOT ON SEA"
        start_state = [
            [ITA, FLT, ROM],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(ITA, [(ITA, FLT, ROM), MTO, VEN])
        self.assertMapState(start_state)
    def test_6A10(self):
        "6.A.10.  SUPPORT ON UNREACHABLE DESTINATION NOT POSSIBLE"
        start_state = [
            [AUS, AMY, VEN],
            [ITA, FLT, ROM],
            [ITA, AMY, APU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, VEN), HLD])
        self.illegalOrder(ITA, [(ITA, FLT, ROM), SUP, (ITA, AMY, APU), MTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, APU), MTO, VEN])
        self.assertMapState(start_state)
    def test_6A10_old(self):
        "6.A.10.old  SUPPORT ON UNREACHABLE DESTINATION IS NOT POSSIBLE"
        start_state = [
            [AUS, AMY, BUD],
            [AUS, FLT, TRI],
            [ITA, AMY, VEN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(AUS, [(AUS, AMY, BUD), SUP, (AUS, FLT, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, FLT, TRI), MTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), HLD])
        self.assertMapState(start_state)
    def test_6A11(self):
        "6.A.11.  SIMPLE BOUNCE"
        start_state = [
            [AUS, AMY, VIE],
            [ITA, AMY, VEN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, VIE), MTO, TYR])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TYR])
        self.assertMapState(start_state)
    def test_6A12(self):
        "6.A.12.  BOUNCE OF THREE UNITS"
        start_state = [
            [AUS, AMY, VIE],
            [ITA, AMY, VEN],
            [GER, AMY, MUN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, VIE), MTO, TYR])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TYR])
        self.legalOrder(GER, [(GER, AMY, MUN), MTO, TYR])
        self.assertMapState(start_state)

class DATC_6_B(DiplomacyAdjudicatorTestCase):
    "6.B.  COASTAL ISSUES"
    
    def test_6B1_fail(self):
        ''' 6.B.1.a  MOVING WITH UNSPECIFIED COAST WHEN COAST IS NECESSARY
            Subject to issue 4.B.1 (default_coast).
            This case causes the move to fail.
            This is the preferred solution for DATC, DPTG, and DAIDE.
        '''#'''
        self.judge.datc.datc_4b1 = 'a'
        start_state = [
            [FRA, FLT, POR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, POR), MTO, SPA])
        self.assertMapState(start_state)
    def test_6B1_default(self):
        ''' 6.B.1.b  MOVING WITH UNSPECIFIED COAST WHEN COAST IS NECESSARY
            Subject to issue 4.B.1 (default_coast).
            This case chooses a default coast for the move.
        '''#'''
        self.judge.datc.datc_4b1 = 'b'
        start_state = [
            [FRA, FLT, POR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, POR), MTO, SPA])
        self.assertMapState([
            [FRA, FLT, [SPA, NCS]],
        ])
    def test_6B2_infer(self):
        ''' 6.B.2.a  MOVING WITH UNSPECIFIED COAST WHEN COAST IS NOT NECESSARY
            Subject to issue 4.B.2 (infer_coast).
            This case moves to the only available coast.
            This is the preferred solution for DATC and DPTG.
        '''#'''
        self.judge.datc.datc_4b2 = 'a'
        start_state = [
            [FRA, FLT, GAS],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, SPA])
        self.assertMapState([
            [FRA, FLT, [SPA, NCS]],
        ])
    def test_6B2_fail(self):
        ''' 6.B.2.c  MOVING WITH UNSPECIFIED COAST WHEN COAST IS NOT NECESSARY
            Subject to issue 4.B.2 (infer_coast).
            This case marks the move as illegal.
            This seems to be the preferred solution for DAIDE.
        '''#'''
        self.judge.datc.datc_4b2 = 'c'
        start_state = [
            [FRA, FLT, GAS],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, GAS), MTO, SPA])
        self.assertMapState(start_state)
    def test_6B3_change(self):
        ''' 6.B.3.a  MOVING WITH WRONG COAST WHEN COAST IS NOT NECESSARY
            Subject to issue 4.B.3 (change_coast).
            This case moves to the only possible coast.
        '''#'''
        self.judge.datc.datc_4b3 = 'a'
        start_state = [
            [FRA, FLT, GAS],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, [SPA, NCS]],
        ])
    def test_6B3_fail(self):
        ''' 6.B.3.b  MOVING WITH WRONG COAST WHEN COAST IS NOT NECESSARY
            Subject to issue 4.B.3 (change_coast).
            This case marks the move as illegal.
            This is the preferred solution for DATC.
        '''#'''
        self.judge.datc.datc_4b3 = 'b'
        start_state = [
            [FRA, FLT, GAS],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, GAS), MTO, (SPA, SCS)])
        self.assertMapState(start_state)
    def test_6B4(self):
        "6.B.4.  SUPPORT TO UNREACHABLE COAST ALLOWED"
        self.init_state(SPR, 1901, [
            [FRA, FLT, GAS],
            [FRA, FLT, MAR],
            [ITA, FLT, WES],
        ])
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, (SPA, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, MAR), SUP, (FRA, FLT, GAS), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, [SPA, NCS]],
            [FRA, FLT, MAR],
            [ITA, FLT, WES],
        ])
    def test_6B5(self):
        "6.B.5.  SUPPORT FROM UNREACHABLE COAST NOT ALLOWED"
        start_state = [
            [FRA, FLT, [SPA, NCS]],
            [FRA, FLT, MAR],
            [ITA, FLT, GOL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, NCS]), SUP, (FRA, FLT, MAR), MTO, GOL])
        self.legalOrder(FRA, [(FRA, FLT, MAR), MTO, GOL])
        self.legalOrder(ITA, [(ITA, FLT, GOL), HLD])
        self.assertMapState(start_state)
    def test_6B6(self):
        "6.B.6.  SUPPORT CAN BE CUT WITH OTHER COAST"
        self.init_state(SPR, 1901, [
            [ENG, FLT, IRI],
            [ENG, FLT, NAO],
            [FRA, FLT, [SPA, NCS]],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, IRI), SUP, (ENG, FLT, NAO), MTO, MAO])
        self.legalOrder(ENG, [(ENG, FLT, NAO), MTO, MAO])
        self.legalOrder(FRA, [(FRA, FLT, [SPA, NCS]), SUP, (FRA, FLT, MAO)])
        self.legalOrder(FRA, [(FRA, FLT, MAO), HLD])
        self.legalOrder(ITA, [(ITA, FLT, GOL), MTO, (SPA, SCS)])
        self.assertMapState([
            [ITA, FLT, GOL],
            [FRA, FLT, [SPA, NCS]],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [FRA, FLT, MAO, MRT],
        ])
    def test_6B7_required(self):
        ''' 6.B.7.a  SUPPORTING WITH UNSPECIFIED COAST"
            Subject to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts are required and must match.
        '''#'''
        self.judge.datc.datc_4b4 = 'a'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, (SPA, NCS)])
        self.illegalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, [SPA, SCS]],
        ])
    def test_6B7_optional(self):
        ''' 6.B.7.d  SUPPORTING WITH UNSPECIFIED COAST"
            Subject to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts are optional, but must match if specified.
            This is the preferred solution for DATC.
        '''#'''
        self.judge.datc.datc_4b4 = 'd'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, (SPA, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState(start_state)
    def test_6B7_illegal(self):
        ''' 6.B.7.e  SUPPORTING WITH UNSPECIFIED COAST"
            Subject to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts are not allowed in support orders.
            This is the preferred solution for DPTG and DAIDE.
        '''#'''
        self.judge.datc.datc_4b4 = 'e'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, (SPA, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, MAO), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.illegalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, POR],
            [FRA, FLT, [SPA, NCS]],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ])
    def test_6B8_required(self):
        ''' 6.B.8.a  SUPPORTING WITH UNSPECIFIED COAST WHEN ONLY ONE COAST IS POSSIBLE"
            Subject to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts are required and must match.
        '''#'''
        self.judge.datc.datc_4b4 = 'a'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, (SPA, NCS)])
        self.illegalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, GAS), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, GOL],
            [ITA, FLT, [SPA, SCS]],
        ])
    def test_6B8_optional(self):
        ''' 6.B.8.d  SUPPORTING WITH UNSPECIFIED COAST WHEN ONLY ONE COAST IS POSSIBLE"
            Subject to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts are optional, but must match if specified.
            This is the preferred solution for DATC.
        '''#'''
        self.judge.datc.datc_4b4 = 'd'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, (SPA, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, GAS), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState(start_state)
    def test_6B8_illegal(self):
        ''' 6.B.8.e  SUPPORTING WITH UNSPECIFIED COAST WHEN ONLY ONE COAST IS POSSIBLE"
            Subject to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts are not allowed in support orders.
            This is the preferred solution for DPTG and DAIDE.
        '''#'''
        self.judge.datc.datc_4b4 = 'e'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, GAS],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, (SPA, NCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, GAS), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.illegalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, POR],
            [FRA, FLT, [SPA, NCS]],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ])
    def test_6B9_required(self):
        ''' 6.B.9.a  SUPPORTING WITH WRONG COAST
            Related to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts must match.
            This server does not support allowing mismatched support orders.
        '''#'''
        self.judge.datc.datc_4b4 = 'a'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, (SPA, SCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, MAO), MTO, (SPA, NCS)])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, [SPA, SCS]],
        ])
    def test_6B9_optional(self):
        ''' 6.B.9.d  SUPPORTING WITH WRONG COAST
            Related to issue 4.B.4 (support_coast, require_coast).
            In this case, coasts must match if specified.
            This is the preferred solution for DATC.
            This server does not support allowing mismatched support orders.
        '''#'''
        self.judge.datc.datc_4b4 = 'd'
        start_state = [
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, (SPA, SCS)])
        self.legalOrder(FRA, [(FRA, FLT, POR), SUP, (FRA, FLT, MAO), MTO, (SPA, NCS)])
        self.legalOrder(ITA, [(ITA, FLT, WES), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, GOL), SUP, (ITA, FLT, WES), MTO, (SPA, SCS)])
        self.assertMapState([
            [FRA, FLT, POR],
            [FRA, FLT, MAO],
            [ITA, FLT, GOL],
            [ITA, FLT, [SPA, SCS]],
        ])
    def test_6B10_fail(self):
        ''' 6.B.10.a  UNIT ORDERED WITH WRONG COAST
            Subject to issue 4.B.5 (wrong_coast).
            In this case, coast specification must match the unit.
            This is the preferred solution for DAIDE.
        '''#'''
        self.judge.datc.datc_4b5 = 'a'
        start_state = [
            [FRA, FLT, [SPA, SCS]],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, NCS]), MTO, GOL])
        self.assertMapState(start_state)
    def test_6B10_ignore(self):
        ''' 6.B.10.b  UNIT ORDERED WITH WRONG COAST
            Subject to issue 4.B.5 (wrong_coast).
            In this case, coast specification is ignored for the ordered unit.
            This is the preferred solution for DATC.
        '''#'''
        self.judge.datc.datc_4b5 = 'b'
        start_state = [
            [FRA, FLT, [SPA, SCS]],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, FLT, [SPA, NCS]), MTO, GOL])
        self.assertMapState([
            [FRA, FLT, GOL],
        ])
    def test_6B11_a(self):
        ''' 6.B.11.a  COAST CAN NOT BE ORDERED TO CHANGE
            Related to issue 4.B.5 (wrong_coast).
        '''#'''
        self.judge.datc.datc_4b5 = 'a'
        start_state = [
            [FRA, FLT, [SPA, NCS]],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, SCS]), MTO, GOL])
        self.assertMapState(start_state)
    def test_6B11_b(self):
        ''' 6.B.11.b  COAST CAN NOT BE ORDERED TO CHANGE
            Related to issue 4.B.5 (wrong_coast).
        '''#'''
        self.judge.datc.datc_4b5 = 'b'
        start_state = [
            [FRA, FLT, [SPA, NCS]],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, SCS]), MTO, GOL])
        self.assertMapState(start_state)
    def test_6B12_fail(self):
        ''' 6.B.12.a  ARMY MOVEMENT WITH COASTAL SPECIFICATION
            Subject to issue 4.B.6 (ignore_coast).
            In this case, armies cannot accept a coast specification.
            This is the preferred solution for DAIDE.
        '''#'''
        self.judge.datc.datc_4b6 = 'a'
        start_state = [
            [FRA, AMY, GAS]
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, AMY, GAS), MTO, (SPA, NCS)])
        self.assertMapState(start_state)
    def test_6B12_ignore(self):
        ''' 6.B.12.b  ARMY MOVEMENT WITH COASTAL SPECIFICATION
            Subject to issue 4.B.6 (ignore_coast).
            In this case, coast specification is ignored for armies.
            This is the preferred solution for DATC.
        '''#'''
        self.judge.datc.datc_4b6 = 'b'
        start_state = [
            [FRA, AMY, GAS]
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, AMY, GAS), MTO, (SPA, NCS)])
        self.assertMapState([
            [FRA, AMY, SPA],
        ])
    def test_6B13(self):
        "6.B.13.  COASTAL CRAWL NOT ALLOWED"
        start_state = [
            [TUR, FLT, [BUL, SCS]],
            [TUR, FLT, CON],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(TUR, [(TUR, FLT, CON), MTO, (BUL, ECS)])
        self.legalOrder(TUR, [(TUR, FLT, [BUL, SCS]), MTO, CON])
        self.assertMapState(start_state)
    def test_6B14_fail(self):
        ''' 6.B.14.a  BUILDING WITH UNSPECIFIED COAST
            Subject to issue 4.B.7 (build_coast).
            In this case, coast specification is required for fleet builds.
            This is the preferred solution for DATC and DAIDE.
        '''#'''
        self.judge.datc.datc_4b7 = 'a'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [(RUS, FLT, STP), BLD])
        self.assertMapState(start_state)
    @fails
    def test_6B14_default(self):
        ''' 6.B.14.b  BUILDING WITH UNSPECIFIED COAST
            Subject to issue 4.B.7 (build_coast).
            In this case, fleets are built in a default coast if unspecified.
        '''#'''
        self.judge.datc.datc_4b7 = 'b'
        start_state = []
        self.init_state(WIN, 1901, start_state)
        self.illegalOrder(RUS, [(RUS, FLT, STP), BLD])
        self.assertMapState([
            [RUS, FLT, [STP, NCS]],
        ])

class DATC_6_C(DiplomacyAdjudicatorTestCase):
    "6.C.  CIRCULAR MOVEMENT"
    def test_6C1(self):
        "6.C.1.  THREE ARMY CIRCULAR MOVEMENT"
        self.init_state(SPR, 1901, [
            [TUR, FLT, ANK],
            [TUR, AMY, CON],
            [TUR, AMY, SMY],
        ])
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, CON), MTO, SMY])
        self.legalOrder(TUR, [(TUR, AMY, SMY), MTO, ANK])
        self.assertMapState([
            [TUR, AMY, ANK],
            [TUR, FLT, CON],
            [TUR, AMY, SMY],
        ])
    def test_6C2(self):
        "6.C.2.  THREE ARMY CIRCULAR MOVEMENT WITH SUPPORT"
        self.init_state(SPR, 1901, [
            [TUR, FLT, ANK],
            [TUR, AMY, CON],
            [TUR, AMY, SMY],
            [TUR, AMY, BUL],
        ])
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, CON), MTO, SMY])
        self.legalOrder(TUR, [(TUR, AMY, SMY), MTO, ANK])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, ANK), MTO, CON])
        self.assertMapState([
            [TUR, AMY, ANK],
            [TUR, FLT, CON],
            [TUR, AMY, SMY],
            [TUR, AMY, BUL],
        ])
    def test_6C3(self):
        "6.C.3.  A DISRUPTED THREE ARMY CIRCULAR MOVEMENT"
        start_state = [
            [TUR, FLT, ANK],
            [TUR, AMY, CON],
            [TUR, AMY, SMY],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, CON), MTO, SMY])
        self.legalOrder(TUR, [(TUR, AMY, SMY), MTO, ANK])
        self.legalOrder(TUR, [(TUR, AMY, BUL), MTO, CON])
        self.assertMapState(start_state)
    def test_6C4(self):
        "6.C.4.  A CIRCULAR MOVEMENT WITH ATTACKED CONVOY"
        self.init_state(SPR, 1901, [
            [AUS, AMY, TRI],
            [AUS, AMY, SER],
            [TUR, AMY, BUL],
            [TUR, FLT, ION],
            [TUR, FLT, AEG],
            [TUR, FLT, ADR],
            [ITA, FLT, NAP],
        ])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, SER])
        self.legalOrder(AUS, [(AUS, AMY, SER), MTO, BUL])
        self.legalOrder(TUR, [(TUR, AMY, BUL), CTO, TRI, VIA, [AEG, ION, ADR]])
        self.legalOrder(TUR, [(TUR, FLT, AEG), CVY, (TUR, AMY, BUL), CTO, TRI])
        self.legalOrder(TUR, [(TUR, FLT, ION), CVY, (TUR, AMY, BUL), CTO, TRI])
        self.legalOrder(TUR, [(TUR, FLT, ADR), CVY, (TUR, AMY, BUL), CTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, NAP), MTO, ION])
        self.assertMapState([
            [AUS, AMY, SER],
            [AUS, AMY, BUL],
            [TUR, AMY, TRI],
            [TUR, FLT, ION],
            [TUR, FLT, AEG],
            [TUR, FLT, ADR],
            [ITA, FLT, NAP],
        ])
    def test_6C5(self):
        "6.C.5.  A DISRUPTED CIRCULAR MOVEMENT DUE TO DISLODGED CONVOY"
        self.init_state(SPR, 1901, [
            [AUS, AMY, TRI],
            [AUS, AMY, SER],
            [TUR, AMY, BUL],
            [TUR, FLT, ION],
            [TUR, FLT, AEG],
            [TUR, FLT, ADR],
            [ITA, FLT, NAP],
            [ITA, FLT, TUN],
        ])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, SER])
        self.legalOrder(AUS, [(AUS, AMY, SER), MTO, BUL])
        self.legalOrder(TUR, [(TUR, AMY, BUL), CTO, TRI, VIA, [AEG, ION, ADR]])
        self.legalOrder(TUR, [(TUR, FLT, AEG), CVY, (TUR, AMY, BUL), CTO, TRI])
        self.legalOrder(TUR, [(TUR, FLT, ION), CVY, (TUR, AMY, BUL), CTO, TRI])
        self.legalOrder(TUR, [(TUR, FLT, ADR), CVY, (TUR, AMY, BUL), CTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, NAP), MTO, ION])
        self.legalOrder(ITA, [(ITA, FLT, TUN), SUP, (ITA, FLT, NAP), MTO, ION])
        self.assertMapState([
            [AUS, AMY, TRI],
            [AUS, AMY, SER],
            [TUR, AMY, BUL],
            [TUR, FLT, AEG],
            [TUR, FLT, ADR],
            [ITA, FLT, ION],
            [ITA, FLT, TUN],
            [TUR, FLT, ION, MRT],
        ])
    def test_6C6(self):
        "6.C.6.  TWO ARMIES WITH TWO CONVOYS"
        self.init_state(SPR, 1901, [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [FRA, FLT, ECH],
            [FRA, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.assertMapState([
            [ENG, FLT, NTH],
            [ENG, AMY, BEL],
            [FRA, FLT, ECH],
            [FRA, AMY, LON],
        ])
    def test_6C7(self):
        "6.C.7.  DISRUPTED UNIT SWAP"
        start_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [FRA, FLT, ECH],
            [FRA, AMY, BEL],
            [FRA, AMY, BUR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, AMY, BUR), MTO, BEL])
        self.assertMapState(start_state)

class DATC_6_D(DiplomacyAdjudicatorTestCase):
    "6.D.  SUPPORTS AND DISLODGES"
    def test_6D1(self):
        "6.D.1.  SUPPORTED HOLD CAN PREVENT DISLODGEMENT"
        start_state = [
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, ADR), SUP, (AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), HLD])
        self.legalOrder(ITA, [(ITA, AMY, TYR), SUP, (ITA, AMY, VEN)])
        self.assertMapState(start_state)
    def test_6D2(self):
        "6.D.2.  A MOVE CUTS SUPPORT ON HOLD"
        start_state = [
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [AUS, AMY, VIE],
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, ADR), SUP, (AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, AMY, VIE), MTO, TYR])
        self.legalOrder(ITA, [(ITA, AMY, VEN), HLD])
        self.legalOrder(ITA, [(ITA, AMY, TYR), SUP, (ITA, AMY, VEN)])
        self.assertMapState([
            [AUS, FLT, ADR],
            [AUS, AMY, VEN],
            [AUS, AMY, VIE],
            [ITA, AMY, TYR],
            [ITA, AMY, VEN, MRT],
        ])
    def test_6D3(self):
        "6.D.3.  A MOVE CUTS SUPPORT ON MOVE"
        start_state = [
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [ITA, AMY, VEN],
            [ITA, FLT, ION],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, ADR), SUP, (AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, VEN), HLD])
        self.legalOrder(ITA, [(ITA, FLT, ION), MTO, ADR])
        self.assertMapState(start_state)
    def test_6D4(self):
        "6.D.4.  SUPPORT TO HOLD ON UNIT SUPPORTING A HOLD ALLOWED"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [RUS, FLT, BAL],
            [RUS, AMY, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), SUP, (GER, FLT, KIE)])
        self.legalOrder(GER, [(GER, FLT, KIE), SUP, (GER, AMY, BER)])
        self.legalOrder(RUS, [(RUS, FLT, BAL), SUP, (RUS, AMY, PRU), MTO, BER])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState(start_state)
    def test_6D5(self):
        "6.D.5.  SUPPORT TO HOLD ON UNIT SUPPORTING A MOVE ALLOWED"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [GER, AMY, MUN],
            [RUS, FLT, BAL],
            [RUS, AMY, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), SUP, (GER, AMY, MUN), MTO, SIL])
        self.legalOrder(GER, [(GER, FLT, KIE), SUP, (GER, AMY, BER)])
        self.legalOrder(GER, [(GER, AMY, MUN), MTO, SIL])
        self.legalOrder(RUS, [(RUS, FLT, BAL), SUP, (RUS, AMY, PRU), MTO, BER])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState([
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [GER, AMY, SIL],
            [RUS, FLT, BAL],
            [RUS, AMY, PRU],
        ])
    def test_6D6(self):
        "6.D.6.  SUPPORT TO HOLD ON CONVOYING UNIT ALLOWED"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, BAL],
            [GER, FLT, PRU],
            [RUS, FLT, LVN],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), CTO, SWE, VIA, [BAL]])
        self.legalOrder(GER, [(GER, FLT, BAL), CVY, (GER, AMY, BER), CTO, SWE])
        self.legalOrder(GER, [(GER, FLT, PRU), SUP, (GER, FLT, BAL)])
        self.legalOrder(RUS, [(RUS, FLT, LVN), MTO, BAL])
        self.legalOrder(RUS, [(RUS, FLT, GOB), SUP, (RUS, FLT, LVN), MTO, BAL])
        self.assertMapState([
            [GER, AMY, SWE],
            [GER, FLT, BAL],
            [GER, FLT, PRU],
            [RUS, FLT, LVN],
            [RUS, FLT, GOB],
        ])
    def test_6D7(self):
        "6.D.7.  SUPPORT TO HOLD ON MOVING UNIT NOT ALLOWED"
        start_state = [
            [GER, FLT, BAL],
            [GER, FLT, PRU],
            [RUS, FLT, LVN],
            [RUS, FLT, GOB],
            [RUS, AMY, FIN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, FLT, BAL), MTO, SWE])
        self.legalOrder(GER, [(GER, FLT, PRU), SUP, (GER, FLT, BAL)])
        self.legalOrder(RUS, [(RUS, FLT, LVN), MTO, BAL])
        self.legalOrder(RUS, [(RUS, FLT, GOB), SUP, (RUS, FLT, LVN), MTO, BAL])
        self.legalOrder(RUS, [(RUS, AMY, FIN), MTO, SWE])
        self.assertMapState([
            [GER, FLT, PRU],
            [RUS, FLT, BAL],
            [RUS, FLT, GOB],
            [RUS, AMY, FIN],
            [GER, FLT, BAL, MRT],
        ])
    def test_6D8(self):
        "6.D.8.  FAILED CONVOY CAN NOT RECEIVE HOLD SUPPORT"
        self.init_state(SPR, 1901, [
            [AUS, FLT, ION],
            [AUS, AMY, SER],
            [AUS, AMY, ALB],
            [TUR, AMY, BUL],
            [TUR, AMY, GRE],
        ])
        self.legalOrder(AUS, [(AUS, FLT, ION), HLD])
        self.legalOrder(AUS, [(AUS, AMY, SER), SUP, (AUS, AMY, ALB), MTO, GRE])
        self.legalOrder(AUS, [(AUS, AMY, ALB), MTO, GRE])
        self.legalOrder(TUR, [(TUR, AMY, GRE), CTO, NAP, VIA, [ION]])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, AMY, GRE)])
        self.assertMapState([
            [AUS, FLT, ION],
            [AUS, AMY, SER],
            [AUS, AMY, GRE],
            [TUR, AMY, BUL],
            [TUR, AMY, GRE, MRT],
        ])
    def test_6D9(self):
        "6.D.9.  SUPPORT TO MOVE ON HOLDING UNIT NOT ALLOWED"
        self.init_state(SPR, 1901, [
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
            [AUS, AMY, ALB],
            [AUS, AMY, TRI],
        ])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, TYR), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(AUS, [(AUS, AMY, ALB), SUP, (AUS, AMY, TRI), MTO, SER])
        self.legalOrder(AUS, [(AUS, AMY, TRI), HLD])
        self.assertMapState([
            [ITA, AMY, TRI],
            [ITA, AMY, TYR],
            [AUS, AMY, ALB],
            [AUS, AMY, TRI, MRT],
        ])
    def test_6D10(self):
        "6.D.10.  SELF DISLODGMENT PROHIBITED"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [GER, AMY, MUN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), HLD])
        self.legalOrder(GER, [(GER, FLT, KIE), MTO, BER])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (GER, FLT, KIE), MTO, BER])
        self.assertMapState(start_state)
    def test_6D11(self):
        "6.D.11.  NO SELF DISLODGMENT OF RETURNING UNIT"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [GER, AMY, MUN],
            [RUS, AMY, WAR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), MTO, PRU])
        self.legalOrder(GER, [(GER, FLT, KIE), MTO, BER])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (GER, FLT, KIE), MTO, BER])
        self.legalOrder(RUS, [(RUS, AMY, WAR), MTO, PRU])
        self.assertMapState(start_state)
    def test_6D12(self):
        "6.D.12.  SUPPORTING A FOREIGN UNIT TO DISLODGE OWN UNIT PROHIBITED"
        start_state = [
            [AUS, FLT, TRI],
            [AUS, AMY, VIE],
            [ITA, AMY, VEN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, TRI), HLD])
        self.legalOrder(AUS, [(AUS, AMY, VIE), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.assertMapState(start_state)
    def test_6D13(self):
        "6.D.13.  SUPPORTING A FOREIGN UNIT TO DISLODGE A RETURNING OWN UNIT PROHIBITED"
        start_state = [
            [AUS, FLT, TRI],
            [AUS, AMY, VIE],
            [ITA, AMY, VEN],
            [ITA, FLT, APU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, TRI), MTO, ADR])
        self.legalOrder(AUS, [(AUS, AMY, VIE), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, APU), MTO, ADR])
        self.assertMapState(start_state)
    def test_6D14(self):
        "6.D.14.  SUPPORTING A FOREIGN UNIT IS NOT ENOUGH TO PREVENT DISLODGEMENT"
        start_state = [
            [AUS, FLT, TRI],
            [AUS, AMY, VIE],
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
            [ITA, FLT, ADR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, TRI), HLD])
        self.legalOrder(AUS, [(AUS, AMY, VIE), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, TYR), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, ADR), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.assertMapState([
            [AUS, AMY, VIE],
            [ITA, AMY, TRI],
            [ITA, AMY, TYR],
            [ITA, FLT, ADR],
            [AUS, FLT, TRI, MRT],
        ])
    def test_6D15(self):
        "6.D.15.  DEFENDER CAN NOT CUT SUPPORT FOR ATTACK ON ITSELF"
        start_state = [
            [RUS, FLT, CON],
            [RUS, FLT, BLA],
            [TUR, FLT, ANK],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(RUS, [(RUS, FLT, CON), SUP, (RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.assertMapState([
            [RUS, FLT, CON],
            [RUS, FLT, ANK],
            [TUR, FLT, ANK, MRT],
        ])
    def test_6D16(self):
        "6.D.16.  CONVOYING A UNIT DISLODGING A UNIT OF SAME POWER IS ALLOWED"
        start_state = [
            [ENG, AMY, LON],
            [ENG, FLT, NTH],
            [FRA, FLT, ECH],
            [FRA, AMY, BEL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, AMY, LON), HLD])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, ECH), SUP, (FRA, AMY, BEL), MTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [NTH]])
        self.assertMapState([
            [ENG, FLT, NTH],
            [FRA, FLT, ECH],
            [FRA, AMY, LON],
            [ENG, AMY, LON, MRT],
        ])
    def test_6D17(self):
        "6.D.17.  DISLODGEMENT CUTS SUPPORTS"
        start_state = [
            [RUS, FLT, CON],
            [RUS, FLT, BLA],
            [TUR, FLT, ANK],
            [TUR, AMY, SMY],
            [TUR, AMY, ARM],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(RUS, [(RUS, FLT, CON), SUP, (RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, SMY), SUP, (TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, ARM), MTO, ANK])
        self.assertMapState([
            [RUS, FLT, BLA],
            [TUR, FLT, CON],
            [TUR, AMY, SMY],
            [TUR, AMY, ARM],
            [RUS, FLT, CON, MRT],
        ])
    def test_6D18(self):
        "6.D.18.  A SURVIVING UNIT WILL SUSTAIN SUPPORT"
        start_state = [
            [RUS, FLT, CON],
            [RUS, FLT, BLA],
            [RUS, AMY, BUL],
            [TUR, FLT, ANK],
            [TUR, AMY, SMY],
            [TUR, AMY, ARM],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(RUS, [(RUS, FLT, CON), SUP, (RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, AMY, BUL), SUP, (RUS, FLT, CON)])
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, SMY), SUP, (TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, ARM), MTO, ANK])
        self.assertMapState([
            [RUS, FLT, CON],
            [RUS, FLT, ANK],
            [RUS, AMY, BUL],
            [TUR, AMY, SMY],
            [TUR, AMY, ARM],
            [TUR, FLT, ANK, MRT],
        ])
    def test_6D19(self):
        "6.D.19.  EVEN WHEN SURVIVING IS IN ALTERNATIVE WAY"
        start_state = [
            [RUS, FLT, CON],
            [RUS, FLT, BLA],
            [RUS, AMY, SMY],
            [TUR, FLT, ANK],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(RUS, [(RUS, FLT, CON), SUP, (RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, AMY, SMY), SUP, (TUR, FLT, ANK), MTO, CON])
        self.legalOrder(TUR, [(TUR, FLT, ANK), MTO, CON])
        self.assertMapState([
            [RUS, FLT, CON],
            [RUS, FLT, ANK],
            [RUS, AMY, SMY],
            [TUR, FLT, ANK, MRT],
        ])
    def test_6D20(self):
        "6.D.20.  UNIT CAN NOT CUT SUPPORT OF ITS OWN COUNTRY"
        start_state = [
            [ENG, FLT, LON],
            [ENG, FLT, NTH],
            [ENG, AMY, YOR],
            [FRA, FLT, ECH],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, NTH), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, ECH])
        self.legalOrder(ENG, [(ENG, AMY, YOR), MTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, ECH), HLD])
        self.assertMapState([
            [ENG, FLT, LON],
            [ENG, FLT, ECH],
            [ENG, AMY, YOR],
            [FRA, FLT, ECH, MRT],
        ])
    def test_6D21(self):
        "6.D.21.  DISLODGING DOES NOT CANCEL A SUPPORT CUT"
        start_state = [
            [AUS, FLT, TRI],
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
            [GER, AMY, MUN],
            [RUS, AMY, SIL],
            [RUS, AMY, BER],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, FLT, TRI), HLD])
        self.legalOrder(ITA, [(ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, TYR), SUP, (ITA, AMY, VEN), MTO, TRI])
        self.legalOrder(GER, [(GER, AMY, MUN), MTO, TYR])
        self.legalOrder(RUS, [(RUS, AMY, SIL), MTO, MUN])
        self.legalOrder(RUS, [(RUS, AMY, BER), SUP, (RUS, AMY, SIL), MTO, MUN])
        self.assertMapState([
            [AUS, FLT, TRI],
            [ITA, AMY, VEN],
            [ITA, AMY, TYR],
            [RUS, AMY, MUN],
            [RUS, AMY, BER],
            [GER, AMY, MUN, MRT],
        ])
    def test_6D22(self):
        "6.D.22.  IMPOSSIBLE FLEET MOVE CAN NOT BE SUPPORTED"
        start_state = [
            [GER, FLT, KIE],
            [GER, AMY, BUR],
            [RUS, AMY, MUN],
            [RUS, AMY, BER],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(GER, [(GER, FLT, KIE), MTO, MUN])
        self.illegalOrder(GER, [(GER, AMY, BUR), SUP, (GER, FLT, KIE), MTO, MUN])
        self.legalOrder(RUS, [(RUS, AMY, MUN), MTO, KIE])
        self.legalOrder(RUS, [(RUS, AMY, BER), SUP, (RUS, AMY, MUN), MTO, KIE])
        self.assertMapState([
            [GER, AMY, BUR],
            [RUS, AMY, KIE],
            [RUS, AMY, BER],
            [GER, FLT, KIE, MRT],
        ])
    def test_6D23(self):
        "6.D.23.  IMPOSSIBLE COAST MOVE CAN NOT BE SUPPORTED"
        start_state = [
            [ITA, FLT, GOL],
            [ITA, FLT, WES],
            [FRA, FLT, [SPA, NCS]],
            [FRA, FLT, MAR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ITA, [(ITA, FLT, GOL), MTO, (SPA, SCS)])
        self.legalOrder(ITA, [(ITA, FLT, WES), SUP, (ITA, FLT, GOL), MTO, SPA])
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, NCS]), MTO, GOL])
        self.illegalOrder(FRA, [(FRA, FLT, MAR), SUP, (FRA, FLT, [SPA, NCS]), MTO, GOL])
        self.assertMapState([
            [ITA, FLT, [SPA, SCS]],
            [ITA, FLT, WES],
            [FRA, FLT, MAR],
            [FRA, FLT, [SPA, NCS], MRT],
        ])
    def test_6D24(self):
        "6.D.24.  IMPOSSIBLE ARMY MOVE CAN NOT BE SUPPORTED"
        start_state = [
            [FRA, AMY, MAR],
            [FRA, FLT, [SPA, SCS]],
            [ITA, FLT, GOL],
            [TUR, FLT, TYS],
            [TUR, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(FRA, [(FRA, AMY, MAR), MTO, GOL])
        self.illegalOrder(FRA, [(FRA, FLT, [SPA, SCS]), SUP, (FRA, AMY, MAR), MTO, GOL])
        self.legalOrder(ITA, [(ITA, FLT, GOL), HLD])
        self.legalOrder(TUR, [(TUR, FLT, TYS), SUP, (TUR, FLT, WES), MTO, GOL])
        self.legalOrder(TUR, [(TUR, FLT, WES), MTO, GOL])
        self.assertMapState([
            [FRA, AMY, MAR],
            [FRA, FLT, [SPA, SCS]],
            [TUR, FLT, TYS],
            [TUR, FLT, GOL],
            [ITA, FLT, GOL, MRT],
        ])
    def test_6D25(self):
        "6.D.25.  FAILING HOLD SUPPORT CAN BE SUPPORTED"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [RUS, FLT, BAL],
            [RUS, AMY, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, FLT, KIE), SUP, (GER, AMY, BER)])
        self.legalOrder(GER, [(GER, AMY, BER), SUP, (RUS, AMY, PRU)])
        self.legalOrder(RUS, [(RUS, FLT, BAL), SUP, (RUS, AMY, PRU), MTO, BER])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState(start_state)
    def test_6D26(self):
        "6.D.26.  FAILING MOVE SUPPORT CAN BE SUPPORTED"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [RUS, FLT, BAL],
            [RUS, AMY, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), SUP, (RUS, AMY, PRU), MTO, SIL])
        self.legalOrder(GER, [(GER, FLT, KIE), SUP, (GER, AMY, BER)])
        self.legalOrder(RUS, [(RUS, FLT, BAL), SUP, (RUS, AMY, PRU), MTO, BER])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState(start_state)
    def test_6D27(self):
        "6.D.27.  FAILING CONVOY CAN BE SUPPORTED"
        start_state = [
            [ENG, FLT, SWE],
            [ENG, FLT, DEN],
            [GER, AMY, BER],
            [RUS, FLT, BAL],
            [RUS, FLT, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, SWE), MTO, BAL])
        self.legalOrder(ENG, [(ENG, FLT, DEN), SUP, (ENG, FLT, SWE), MTO, BAL])
        self.legalOrder(GER, [(GER, AMY, BER), HLD])
        self.legalOrder(RUS, [(RUS, FLT, BAL), CVY, (GER, AMY, BER), CTO, LVN])
        self.legalOrder(RUS, [(RUS, FLT, PRU), SUP, (RUS, FLT, BAL)])
        self.assertMapState(start_state)
    def test_6D33(self):
        "6.D.33.  UNWANTED SUPPORT ALLOWED"
        start_state = [
            [AUS, AMY, SER],
            [AUS, AMY, VIE],
            [RUS, AMY, GAL],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, SER), MTO, BUD])
        self.legalOrder(AUS, [(AUS, AMY, VIE), MTO, BUD])
        self.legalOrder(RUS, [(RUS, AMY, GAL), SUP, (AUS, AMY, SER), MTO, BUD])
        self.legalOrder(TUR, [(TUR, AMY, BUL), MTO, SER])
        self.assertMapState([
            [AUS, AMY, BUD],
            [AUS, AMY, VIE],
            [RUS, AMY, GAL],
            [TUR, AMY, SER],
        ])
    def test_6D34(self):
        "6.D.34.  SUPPORT TARGETING OWN AREA NOT ALLOWED"
        start_state = [
            [GER, AMY, BER],
            [GER, AMY, SIL],
            [GER, FLT, BAL],
            [ITA, AMY, PRU],
            [RUS, AMY, WAR],
            [RUS, AMY, LVN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), MTO, PRU])
        self.legalOrder(GER, [(GER, AMY, SIL), SUP, (GER, AMY, BER), MTO, PRU])
        self.legalOrder(GER, [(GER, FLT, BAL), SUP, (GER, AMY, BER), MTO, PRU])
        self.illegalOrder(ITA, [(ITA, AMY, PRU), SUP, (RUS, AMY, LVN), MTO, PRU])
        self.legalOrder(RUS, [(RUS, AMY, WAR), SUP, (RUS, AMY, LVN), MTO, PRU])
        self.legalOrder(RUS, [(RUS, AMY, LVN), MTO, PRU])
        self.assertMapState([
            [GER, AMY, PRU],
            [GER, AMY, SIL],
            [GER, FLT, BAL],
            [RUS, AMY, WAR],
            [RUS, AMY, LVN],
            [ITA, AMY, PRU, MRT],
        ])

class DATC_6_D_Quasi(DiplomacyAdjudicatorTestCase):
    ''' 6.D.  SUPPORTING ILLEGAL MOVES
        These tests are subject to issue 4.E.1 (quasi_legal).
    '''#'''
    def setUp(self):
        ''' Initializes class variables for test cases.'''
        super(DATC_6_D_Quasi, self).setUp()
        self.judge.game_opts.AOA = True
        self.illegalOrder = self.legalOrder
    
    # With Quasi-Legal orders
    def test_6D28_quasi(self):
        "6.D.28.a  IMPOSSIBLE MOVE AND SUPPORT"
        self.judge.datc.datc_4e1 = 'a'
        start_state = [
            [AUS, AMY, BUD],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (RUS, FLT, RUM)])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, HOL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, RUM])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, RUM])
        self.assertMapState([
            [AUS, AMY, BUD],
            [RUS, FLT, RUM, MRT],
            [TUR, FLT, RUM],
            [TUR, AMY, BUL],
        ])
    def test_6D29_quasi_change(self):
        ''' 6.D.29.a.a  MOVE TO IMPOSSIBLE COAST AND SUPPORT
            Also subject to issue 4.B.3 (change_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'a'
        self.judge.datc.datc_4b3 = 'a'
        start_state = [
            [AUS, AMY, BUD],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (RUS, FLT, RUM)])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, (BUL, SCS)])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, RUM])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, RUM])
        self.assertMapState([
            [AUS, AMY, BUD],
            [RUS, FLT, RUM, MRT],
            [TUR, FLT, RUM],
            [TUR, AMY, BUL],
        ])
    def test_6D29_quasi_fail(self):
        ''' 6.D.29.a.b  MOVE TO IMPOSSIBLE COAST AND SUPPORT
            Also subject to issue 4.B.3 (change_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'a'
        self.judge.datc.datc_4b3 = 'b'
        start_state = [
            [AUS, AMY, BUD],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (RUS, FLT, RUM)])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, (BUL, SCS)])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, RUM])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, RUM])
        self.assertMapState([
            [AUS, AMY, BUD],
            [RUS, FLT, RUM, MRT],
            [TUR, FLT, RUM],
            [TUR, AMY, BUL],
        ])
    def test_6D30_quasi_fail(self):
        ''' 6.D.30.a.a  MOVE WITHOUT COAST AND SUPPORT
            Also subject to issue 4.B.1 (default_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'a'
        self.judge.datc.datc_4b1 = 'a'
        start_state = [
            [ITA, FLT, AEG],
            [RUS, FLT, CON],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ITA, [(ITA, FLT, AEG), SUP, (RUS, FLT, CON)])
        self.legalOrder(RUS, [(RUS, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, CON])
        self.assertMapState([
            [ITA, FLT, AEG],
            [RUS, FLT, CON, MRT],
            [TUR, FLT, CON],
            [TUR, AMY, BUL],
        ])
    def test_6D30_quasi_default(self):
        ''' 6.D.30.a.b  MOVE WITHOUT COAST AND SUPPORT
            Also subject to issue 4.B.1 (default_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'a'
        self.judge.datc.datc_4b1 = 'b'
        start_state = [
            [ITA, FLT, AEG],
            [RUS, FLT, CON],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ITA, [(ITA, FLT, AEG), SUP, (RUS, FLT, CON)])
        self.legalOrder(RUS, [(RUS, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, CON])
        self.assertMapState([
            [ITA, FLT, AEG],
            [RUS, FLT, CON, MRT],
            [TUR, FLT, CON],
            [TUR, AMY, BUL],
        ])
    def test_6D31_quasi(self):
        "6.D.31.a  A TRICKY IMPOSSIBLE SUPPORT"
        self.judge.datc.datc_4e1 = 'a'
        start_state = [
            [AUS, AMY, RUM],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, RUM), CTO, ARM, VIA, [BLA]])
        self.legalOrder(TUR, [(TUR, FLT, BLA), SUP, (AUS, AMY, RUM), MTO, ARM])
        self.assertMapState(start_state)
    def test_6D32_quasi(self):
        "6.D.32.a  A MISSING FLEET"
        self.judge.datc.datc_4e1 = 'a'
        start_state = [
            [ENG, FLT, EDI],
            [ENG, AMY, LVP],
            [FRA, FLT, LON],
            [GER, AMY, YOR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, EDI), SUP, (ENG, AMY, LVP), MTO, YOR])
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, YOR])
        self.legalOrder(FRA, [(FRA, FLT, LON), SUP, (GER, AMY, YOR)])
        self.legalOrder(GER, [(GER, AMY, YOR), MTO, HOL])
        self.assertMapState([
            [ENG, FLT, EDI],
            [ENG, AMY, YOR],
            [FRA, FLT, LON],
            [GER, AMY, YOR, MRT],
        ])
    
    # Without Quasi-Legal orders
    def test_6D28_illegal(self):
        "6.D.28.d  IMPOSSIBLE MOVE AND SUPPORT"
        self.judge.datc.datc_4e1 = 'd'
        start_state = [
            [AUS, AMY, BUD],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (RUS, FLT, RUM)])
        self.illegalOrder(RUS, [(RUS, FLT, RUM), MTO, HOL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, RUM])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, RUM])
        self.assertMapState(start_state)
    def test_6D29_illegal_change(self):
        ''' 6.D.29.d.a  MOVE TO IMPOSSIBLE COAST AND SUPPORT
            Also subject to issue 4.B.3 (change_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'd'
        self.judge.datc.datc_4b3 = 'a'
        start_state = [
            [AUS, AMY, BUD],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (RUS, FLT, RUM)])
        self.legalOrder(RUS, [(RUS, FLT, RUM), MTO, (BUL, SCS)])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, RUM])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, RUM])
        self.assertMapState([
            [AUS, AMY, BUD],
            [RUS, FLT, RUM, MRT],
            [TUR, FLT, RUM],
            [TUR, AMY, BUL],
        ])
    def test_6D29_illegal_fail(self):
        ''' 6.D.29.d.b  MOVE TO IMPOSSIBLE COAST AND SUPPORT
            Also subject to issue 4.B.3 (change_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'd'
        self.judge.datc.datc_4b3 = 'b'
        start_state = [
            [AUS, AMY, BUD],
            [RUS, FLT, RUM],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (RUS, FLT, RUM)])
        self.illegalOrder(RUS, [(RUS, FLT, RUM), MTO, (BUL, SCS)])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, RUM])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, RUM])
        self.assertMapState(start_state)
    def test_6D30_illegal_fail(self):
        ''' 6.D.30.d.a  MOVE WITHOUT COAST AND SUPPORT
            Also subject to issue 4.B.1 (default_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'd'
        self.judge.datc.datc_4b1 = 'a'
        start_state = [
            [ITA, FLT, AEG],
            [RUS, FLT, CON],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ITA, [(ITA, FLT, AEG), SUP, (RUS, FLT, CON)])
        self.illegalOrder(RUS, [(RUS, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, CON])
        self.assertMapState(start_state)
    def test_6D30_illegal_default(self):
        ''' 6.D.30.d.b  MOVE WITHOUT COAST AND SUPPORT
            Also subject to issue 4.B.1 (default_coast).
        '''#'''
        self.judge.datc.datc_4e1 = 'd'
        self.judge.datc.datc_4b1 = 'b'
        start_state = [
            [ITA, FLT, AEG],
            [RUS, FLT, CON],
            [TUR, FLT, BLA],
            [TUR, AMY, BUL],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ITA, [(ITA, FLT, AEG), SUP, (RUS, FLT, CON)])
        self.legalOrder(RUS, [(RUS, FLT, CON), MTO, BUL])
        self.legalOrder(TUR, [(TUR, FLT, BLA), MTO, CON])
        self.legalOrder(TUR, [(TUR, AMY, BUL), SUP, (TUR, FLT, BLA), MTO, CON])
        self.assertMapState([
            [ITA, FLT, AEG],
            [RUS, FLT, CON, MRT],
            [TUR, FLT, CON],
            [TUR, AMY, BUL],
        ])
    def test_6D31_illegal(self):
        "6.D.31.d  A TRICKY IMPOSSIBLE SUPPORT"
        self.judge.datc.datc_4e1 = 'd'
        start_state = [
            [AUS, AMY, RUM],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, RUM), CTO, ARM, VIA, [BLA]])
        self.illegalOrder(TUR, [(TUR, FLT, BLA), SUP, (AUS, AMY, RUM), MTO, ARM])
        self.assertMapState(start_state)
    def test_6D32_illegal(self):
        "6.D.32.d  A MISSING FLEET"
        self.judge.datc.datc_4e1 = 'd'
        start_state = [
            [ENG, FLT, EDI],
            [ENG, AMY, LVP],
            [FRA, FLT, LON],
            [GER, AMY, YOR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, EDI), SUP, (ENG, AMY, LVP), MTO, YOR])
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, YOR])
        self.legalOrder(FRA, [(FRA, FLT, LON), SUP, (GER, AMY, YOR)])
        self.illegalOrder(GER, [(GER, AMY, YOR), MTO, HOL])
        self.assertMapState(start_state)

class DATC_6_E(DiplomacyAdjudicatorTestCase):
    "6.E.  HEAD TO HEAD BATTLES AND BELEAGUERED GARRISON"
    def test_6E1(self):
        "6.E.1.  DISLODGED UNIT HAS NO EFFECT ON ATTACKERS AREA"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [GER, AMY, SIL],
            [RUS, AMY, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), MTO, PRU])
        self.legalOrder(GER, [(GER, FLT, KIE), MTO, BER])
        self.legalOrder(GER, [(GER, AMY, SIL), SUP, (GER, AMY, BER), MTO, PRU])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState([
            [GER, AMY, PRU],
            [GER, FLT, BER],
            [GER, AMY, SIL],
            [RUS, AMY, PRU, MRT],
        ])
    def test_6E2(self):
        "6.E.2.  NO SELF DISLODGEMENT IN HEAD TO HEAD BATTLE"
        start_state = [
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [GER, AMY, MUN],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), MTO, KIE])
        self.legalOrder(GER, [(GER, FLT, KIE), MTO, BER])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (GER, AMY, BER), MTO, KIE])
        self.assertMapState(start_state)
    def test_6E3(self):
        "6.E.3.  NO HELP IN DISLODGING OWN UNIT"
        start_state = [
            [GER, AMY, BER],
            [GER, AMY, MUN],
            [ENG, FLT, KIE],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, AMY, BER), MTO, KIE])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (ENG, FLT, KIE), MTO, BER])
        self.legalOrder(ENG, [(ENG, FLT, KIE), MTO, BER])
        self.assertMapState(start_state)
    def test_6E4(self):
        "6.E.4.  NON-DISLODGED LOSER HAS STILL EFFECT"
        start_state = [
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
            [FRA, FLT, NTH],
            [FRA, FLT, BEL],
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [ENG, FLT, NWG],
            [AUS, AMY, KIE],
            [AUS, AMY, RUH],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, FLT, HOL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, HOL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), SUP, (GER, FLT, HOL), MTO, NTH])
        self.legalOrder(FRA, [(FRA, FLT, NTH), MTO, HOL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, NTH), MTO, HOL])
        self.legalOrder(ENG, [(ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, EDI), SUP, (ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(AUS, [(AUS, AMY, RUH), MTO, HOL])
        self.legalOrder(AUS, [(AUS, AMY, KIE), SUP, (AUS, AMY, RUH), MTO, HOL])
        self.assertMapState(start_state)
    def test_6E5(self):
        "6.E.5.  LOSER DISLODGED BY ANOTHER ARMY HAS STILL EFFECT"
        start_state = [
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
            [FRA, FLT, NTH],
            [FRA, FLT, BEL],
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [ENG, FLT, NWG],
            [ENG, FLT, LON],
            [AUS, AMY, KIE],
            [AUS, AMY, RUH],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, FLT, HOL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, HOL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), SUP, (GER, FLT, HOL), MTO, NTH])
        self.legalOrder(FRA, [(FRA, FLT, NTH), MTO, HOL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, NTH), MTO, HOL])
        self.legalOrder(ENG, [(ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, EDI), SUP, (ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, NWG), MTO, NTH])
        self.legalOrder(AUS, [(AUS, AMY, RUH), MTO, HOL])
        self.legalOrder(AUS, [(AUS, AMY, KIE), SUP, (AUS, AMY, RUH), MTO, HOL])
        self.assertMapState([
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
            [FRA, FLT, NTH, MRT],
            [FRA, FLT, BEL],
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [ENG, FLT, NTH],
            [ENG, FLT, LON],
            [AUS, AMY, KIE],
            [AUS, AMY, RUH],
        ])
    def test_6E6(self):
        "6.E.6.  NOT DISLODGE BECAUSE OF OWN SUPPORT HAS STILL EFFECT"
        start_state = [
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [FRA, FLT, NTH],
            [FRA, FLT, BEL],
            [FRA, FLT, ECH],
            [AUS, AMY, KIE],
            [AUS, AMY, RUH],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(GER, [(GER, FLT, HOL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, HOL), MTO, NTH])
        self.legalOrder(FRA, [(FRA, FLT, NTH), MTO, HOL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, NTH), MTO, HOL])
        self.legalOrder(FRA, [(FRA, FLT, ECH), SUP, (GER, FLT, HOL), MTO, NTH])
        self.legalOrder(AUS, [(AUS, AMY, RUH), MTO, HOL])
        self.legalOrder(AUS, [(AUS, AMY, KIE), SUP, (AUS, AMY, RUH), MTO, HOL])
        self.assertMapState(start_state)
    def test_6E7(self):
        "6.E.7.  NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON"
        start_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, YOR],
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [RUS, FLT, SKA],
            [RUS, FLT, NWY],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, NTH), HLD])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HOL), SUP, (GER, FLT, HEL), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, SKA), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.assertMapState(start_state)
    def test_6E8(self):
        "6.E.8.  NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON AND HEAD TO HEAD BATTLE"
        start_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, YOR],
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [RUS, FLT, SKA],
            [RUS, FLT, NWY],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, NWY])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HOL), SUP, (GER, FLT, HEL), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, SKA), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.assertMapState(start_state)
    def test_6E9(self):
        "6.E.9.  ALMOST SELF DISLODGEMENT WITH BELEAGUERED GARRISON"
        start_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, YOR],
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [RUS, FLT, SKA],
            [RUS, FLT, NWY],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, NWG])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HOL), SUP, (GER, FLT, HEL), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, SKA), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.assertMapState([
            [ENG, FLT, NWG],
            [ENG, FLT, YOR],
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [RUS, FLT, SKA],
            [RUS, FLT, NTH],
        ])
    def test_6E10(self):
        "6.E.10.  ALMOST CIRCULAR MOVEMENT WITH NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON"
        start_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, YOR],
            [GER, FLT, HOL],
            [GER, FLT, HEL],
            [GER, FLT, DEN],
            [RUS, FLT, SKA],
            [RUS, FLT, NWY],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, DEN])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HOL), SUP, (GER, FLT, HEL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, DEN), MTO, HEL])
        self.legalOrder(RUS, [(RUS, FLT, NWY), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, SKA), SUP, (RUS, FLT, NWY), MTO, NTH])
        self.assertMapState(start_state)
    def test_6E11(self):
        "6.E.11.  NO SELF DISLODGEMENT WITH BELEAGUERED GARRISON, UNIT SWAP WITH ADJACENT CONVOYING AND TWO COASTS"
        start_state = [
            [FRA, AMY, SPA],
            [FRA, FLT, MAO],
            [FRA, FLT, GOL],
            [GER, AMY, MAR],
            [GER, AMY, GAS],
            [ITA, FLT, POR],
            [ITA, FLT, WES],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(FRA, [(FRA, AMY, SPA), CTO, POR, VIA, [MAO]])
        self.legalOrder(FRA, [(FRA, FLT, MAO), CVY, (FRA, AMY, SPA), CTO, POR])
        self.legalOrder(FRA, [(FRA, FLT, GOL), SUP, (ITA, FLT, POR), MTO, SPA])
        self.legalOrder(GER, [(GER, AMY, MAR), SUP, (GER, AMY, GAS), MTO, SPA])
        self.legalOrder(GER, [(GER, AMY, GAS), MTO, SPA])
        self.legalOrder(ITA, [(ITA, FLT, POR), MTO, (SPA, NCS)])
        self.legalOrder(ITA, [(ITA, FLT, WES), SUP, (ITA, FLT, POR), MTO, SPA])
        self.assertMapState([
            [FRA, AMY, POR],
            [FRA, FLT, MAO],
            [FRA, FLT, GOL],
            [GER, AMY, MAR],
            [GER, AMY, GAS],
            [ITA, FLT, [SPA, NCS]],
            [ITA, FLT, WES],
        ])
    def test_6E12(self):
        "6.E.12.  SUPPORT ON ATTACK ON OWN UNIT CAN BE USED FOR OTHER MEANS"
        start_state = [
            [AUS, AMY, BUD],
            [AUS, AMY, SER],
            [ITA, AMY, VIE],
            [RUS, AMY, GAL],
            [RUS, AMY, RUM],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(AUS, [(AUS, AMY, BUD), MTO, RUM])
        self.legalOrder(AUS, [(AUS, AMY, SER), SUP, (ITA, AMY, VIE), MTO, BUD])
        self.legalOrder(ITA, [(ITA, AMY, VIE), MTO, BUD])
        self.legalOrder(RUS, [(RUS, AMY, GAL), MTO, BUD])
        self.legalOrder(RUS, [(RUS, AMY, RUM), SUP, (RUS, AMY, GAL), MTO, BUD])
        self.assertMapState(start_state)
    def test_6E13(self):
        "6.E.13.  THREE WAY BELEAGUERED GARRISON"
        start_state = [
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [FRA, FLT, BEL],
            [FRA, FLT, ECH],
            [GER, FLT, NTH],
            [RUS, FLT, NWG],
            [RUS, FLT, NWY],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, EDI), SUP, (ENG, FLT, YOR), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), MTO, NTH])
        self.legalOrder(FRA, [(FRA, FLT, BEL), MTO, NTH])
        self.legalOrder(FRA, [(FRA, FLT, ECH), SUP, (FRA, FLT, BEL), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, NTH), HLD])
        self.legalOrder(RUS, [(RUS, FLT, NWG), MTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, NWY), SUP, (RUS, FLT, NWG), MTO, NTH])
        self.assertMapState(start_state)
    def test_6E14(self):
        "6.E.14.  ILLEGAL HEAD TO HEAD BATTLE CAN STILL DEFEND"
        start_state = [
            [ENG, AMY, LVP],
            [RUS, FLT, EDI],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, EDI])
        self.illegalOrder(RUS, [(RUS, FLT, EDI), MTO, LVP])
        self.assertMapState(start_state)
    def test_6E15(self):
        "6.E.15.  THE FRIENDLY HEAD TO HEAD BATTLE"
        start_state = [
            [ENG, FLT, HOL],
            [ENG, AMY, RUH],
            [FRA, AMY, KIE],
            [FRA, AMY, MUN],
            [FRA, AMY, SIL],
            [GER, AMY, BER],
            [GER, FLT, DEN],
            [GER, FLT, HEL],
            [RUS, FLT, BAL],
            [RUS, AMY, PRU],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, FLT, HOL), SUP, (ENG, AMY, RUH), MTO, KIE])
        self.legalOrder(ENG, [(ENG, AMY, RUH), MTO, KIE])
        self.legalOrder(FRA, [(FRA, AMY, KIE), MTO, BER])
        self.legalOrder(FRA, [(FRA, AMY, MUN), SUP, (FRA, AMY, KIE), MTO, BER])
        self.legalOrder(FRA, [(FRA, AMY, SIL), SUP, (FRA, AMY, KIE), MTO, BER])
        self.legalOrder(GER, [(GER, AMY, BER), MTO, KIE])
        self.legalOrder(GER, [(GER, FLT, DEN), SUP, (GER, AMY, BER), MTO, KIE])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, AMY, BER), MTO, KIE])
        self.legalOrder(RUS, [(RUS, FLT, BAL), SUP, (RUS, AMY, PRU), MTO, BER])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState(start_state)

class DATC_6_F(DiplomacyAdjudicatorTestCase):
    "6.F.  CONVOYS"
    def test_6F1(self):
        "6.F.1.  NO CONVOY IN COASTAL AREAS"
        start_state = [
            [TUR, AMY, GRE],
            [TUR, FLT, AEG],
            [TUR, FLT, CON],
            [TUR, FLT, BLA],
        ]
        self.init_state(SPR, 1901, start_state)
        self.illegalOrder(TUR, [(TUR, AMY, GRE), CTO, SEV, VIA, [AEG, CON, BLA]])
        self.illegalOrder(TUR, [(TUR, FLT, AEG), CVY, (TUR, AMY, GRE), CTO, SEV])
        self.illegalOrder(TUR, [(TUR, FLT, CON), CVY, (TUR, AMY, GRE), CTO, SEV])
        self.illegalOrder(TUR, [(TUR, FLT, BLA), CVY, (TUR, AMY, GRE), CTO, SEV])
        self.assertMapState(start_state)
    def test_6F2(self):
        "6.F.2.  AN ARMY BEING CONVOYED CAN BOUNCE AS NORMAL"
        start_state = [
            [ENG, FLT, ECH],
            [ENG, AMY, LON],
            [FRA, AMY, PAR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BRE, VIA, [ECH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BRE])
        self.legalOrder(FRA, [(FRA, AMY, PAR), MTO, BRE])
        self.assertMapState(start_state)
    def test_6F3(self):
        "6.F.3.  AN ARMY BEING CONVOYED CAN RECEIVE SUPPORT"
        start_state = [
            [ENG, FLT, ECH],
            [ENG, AMY, LON],
            [ENG, FLT, MAO],
            [FRA, AMY, PAR],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BRE, VIA, [ECH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BRE])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, AMY, LON), MTO, BRE])
        self.legalOrder(FRA, [(FRA, AMY, PAR), MTO, BRE])
        self.assertMapState([
            [ENG, FLT, ECH],
            [ENG, AMY, BRE],
            [ENG, FLT, MAO],
            [FRA, AMY, PAR],
        ])
    def test_6F4(self):
        "6.F.4.  AN ATTACKED CONVOY IS NOT DISRUPTED"
        start_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [GER, FLT, SKA],
        ]
        self.init_state(SPR, 1901, start_state)
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, HOL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, HOL])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.assertMapState([
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
            [GER, FLT, SKA],
        ])
    def test_6F5(self):
        "6.F.5.  A BELEAGUERED CONVOY IS NOT DISRUPTED"
        steady_state = [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, FLT, SKA],
            [GER, FLT, DEN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, HOL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, HOL])
        self.legalOrder(FRA, [(FRA, FLT, ECH), MTO, NTH])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, DEN), SUP, (GER, FLT, SKA), MTO, NTH])
        self.assertMapState(steady_state + [
            [ENG, AMY, HOL],
        ])
    def test_6F6(self):
        "6.F.6.  DISLODGED CONVOY DOES NOT CUT SUPPORT"
        steady_state = [
            [ENG, AMY, LON],
            [GER, AMY, HOL],
            [GER, AMY, BEL],
            [GER, FLT, HEL],
            [FRA, AMY, PIC],
            [FRA, AMY, BUR],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, NTH],
            [GER, FLT, SKA],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, HOL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, HOL])
        self.legalOrder(GER, [(GER, AMY, HOL), SUP, (GER, AMY, BEL)])
        self.legalOrder(GER, [(GER, AMY, BEL), SUP, (GER, AMY, HOL)])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH, MRT],
            [GER, FLT, NTH],
        ])
    def test_6F7(self):
        "6.F.7.  DISLODGED CONVOY DOES NOT CAUSE CONTESTED AREA"
        steady_state = [
            [ENG, AMY, LON],
            [GER, FLT, HEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [GER, FLT, SKA],
            [ENG, FLT, NTH],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, HOL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, HOL])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.assertMapState(steady_state + [
            [GER, FLT, NTH],
            [ENG, FLT, NTH, MRT],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), RTO, HOL])
        self.assertMapState(steady_state + [
            [GER, FLT, NTH],
            [ENG, FLT, HOL],
        ])
    def test_6F8(self):
        "6.F.8.  DISLODGED CONVOY DOES NOT CAUSE A BOUNCE"
        steady_state = [
            [ENG, AMY, LON],
            [GER, FLT, HEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [GER, FLT, SKA],
            [ENG, FLT, NTH],
            [GER, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, HOL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, HOL])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, AMY, BEL), MTO, HOL])
        self.assertMapState(steady_state + [
            [GER, FLT, NTH],
            [ENG, FLT, NTH, MRT],
            [GER, AMY, HOL],
        ])

class DATC_6_F_Routes(DiplomacyAdjudicatorTestCase):
    "6.F.  MULTI-ROUTE CONVOYS"
    # All depend on or relate to 4.A.1 (disrupt_all)
    def test_6F9_any(self):
        "6.F.9.a  DISLODGE OF MULTI-ROUTE CONVOY"
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_6F10_any(self):
        "6.F.10.a  DISLODGE OF MULTI-ROUTE CONVOY WITH FOREIGN FLEET"
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [ENG, FLT, NTH],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [GER, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(GER, [(GER, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [GER, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_6F11_any(self):
        "6.F.11.a  DISLODGE OF MULTI-ROUTE CONVOY WITH ONLY FOREIGN FLEETS"
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [ENG, AMY, LON],
            [RUS, FLT, NTH],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [GER, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(GER, [(GER, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [GER, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_6F12_any(self):
        "6.F.12.a  DISLODGED CONVOYING FLEET NOT ON ROUTE"
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [ENG, FLT, ECH],
            [FRA, FLT, NAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [ENG, FLT, IRI],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.illegalOrder(ENG, [(ENG, FLT, IRI), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, NAO), SUP, (FRA, FLT, MAO), MTO, IRI])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, IRI])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [ENG, FLT, IRI, MRT],
            [FRA, FLT, IRI],
        ])
    def test_6F13_any(self):
        "6.F.13.a  THE UNWANTED ALTERNATIVE"
        # 4.A.6, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, FLT, ECH],
            [GER, FLT, HOL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [ENG, FLT, NTH],
            [GER, FLT, DEN],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(GER, [(GER, FLT, HOL), SUP, (GER, FLT, DEN), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, DEN), MTO, NTH])
        self.assertMapState(steady_state + [
            [ENG, AMY, LON],
            [ENG, FLT, NTH, MRT],
            [GER, FLT, NTH],
        ])
    
    def test_6F9_all(self):
        "6.F.9.b  DISLODGE OF MULTI-ROUTE CONVOY"
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [ENG, FLT, NTH],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, ECH],
            [ENG, AMY, LON],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_6F10_all(self):
        "6.F.10.b  DISLODGE OF MULTI-ROUTE CONVOY WITH FOREIGN FLEET"
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [ENG, FLT, NTH],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [GER, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(GER, [(GER, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [GER, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_6F11_all(self):
        "6.F.11.b  DISLODGE OF MULTI-ROUTE CONVOY WITH ONLY FOREIGN FLEETS"
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [RUS, FLT, NTH],
            [FRA, FLT, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [GER, FLT, ECH],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(GER, [(GER, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BRE), SUP, (FRA, FLT, MAO), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [GER, FLT, ECH, MRT],
            [FRA, FLT, ECH],
        ])
    def test_6F12_all(self):
        "6.F.12.b  DISLODGED CONVOYING FLEET NOT ON ROUTE"
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [ENG, FLT, ECH],
            [FRA, FLT, NAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [ENG, FLT, IRI],
            [FRA, FLT, MAO],
        ])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.illegalOrder(ENG, [(ENG, FLT, IRI), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, NAO), SUP, (FRA, FLT, MAO), MTO, IRI])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, IRI])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [ENG, FLT, IRI, MRT],
            [FRA, FLT, IRI],
        ])
    def test_6F13_all(self):
        "6.F.13.b  THE UNWANTED ALTERNATIVE"
        # 4.A.6, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, FLT, ECH],
            [GER, FLT, HOL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [ENG, FLT, NTH],
            [GER, FLT, DEN],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(GER, [(GER, FLT, HOL), SUP, (GER, FLT, DEN), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, DEN), MTO, NTH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [ENG, FLT, NTH, MRT],
            [GER, FLT, NTH],
        ])

class DATC_6_F_Paradox_1982(DiplomacyAdjudicatorTestCase):
    "6.F.  CONVOY PARADOX (1982 RESOLUTION)"
    # All depend on or relate to 4.A.2 (paradox)
    def setUp(self):
        super(DATC_6_F_Paradox_1982, self).setUp()
        self.judge.datc.datc_4a2 = 'b'
    
    def test_6F14(self):
        "6.F.14.b  SIMPLE CONVOY PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, ECH, MRT],
        ])
    def test_6F15(self):
        "6.F.15.b  SIMPLE CONVOY PARADOX WITH ADDITIONAL CONVOY"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [ITA, FLT, IRI],
            [ITA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
            [ITA, AMY, NAF],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(ITA, [(ITA, AMY, NAF), CTO, WAL, VIA, [MAO, IRI]])
        self.legalOrder(ITA, [(ITA, FLT, MAO), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.legalOrder(ITA, [(ITA, FLT, IRI), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, ECH, MRT],
            [ITA, AMY, WAL],
        ])
    def test_6F16(self):
        "6.F.16.b  PANDIN'S PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state)
    def test_6F17(self):
        "6.F.17.b  PANDIN'S EXTENDED PARADOX"
        steady_state = [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
            [FRA, FLT, YOR],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, YOR), SUP, (FRA, AMY, BRE), MTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state + [
            [ENG, FLT, LON, MRT],
            [FRA, AMY, LON],
        ])
    def test_6F18(self):
        "6.F.18.b  BETRAYAL PARADOX"
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, FLT, ECH],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [FRA, FLT, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (ENG, FLT, NTH)])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [FRA, FLT, BEL, MRT],
        ])
    def test_6F19_any(self):
        "6.F.19.b.a  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, TYS],
            [ITA, FLT, ROM],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
            [FRA, FLT, TYS, MRT],
            [ITA, FLT, TYS],
        ])
    def test_6F19_all(self):
        "6.F.19.b.b  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, TYS],
            [ITA, FLT, ROM],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
            [FRA, FLT, TYS, MRT],
            [ITA, FLT, TYS],
        ])
    def test_6F20_any(self):
        "6.F.20.b.a  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F20_all(self):
        "6.F.20.b.b  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
        ])
    def test_6F21(self):
        "6.F.21.b  DAD'S ARMY CONVOY"
        steady_state = [
            [RUS, AMY, EDI],
            [RUS, FLT, NWG],
            [FRA, FLT, IRI],
            [FRA, FLT, MAO],
            [ENG, FLT, NAO],
            [ENG, AMY, LVP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [RUS, AMY, NWY],
            [ENG, FLT, CLY],
        ])
        self.legalOrder(RUS, [(RUS, AMY, EDI), SUP, (RUS, AMY, NWY), MTO, CLY])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, NWY), CTO, CLY])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, CLY, VIA, [NWG]])
        self.legalOrder(FRA, [(FRA, FLT, IRI), SUP, (FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, CLY, VIA, [NAO]])
        self.legalOrder(ENG, [(ENG, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, CLY])
        self.legalOrder(ENG, [(ENG, FLT, CLY), SUP, (ENG, FLT, NAO)])
        self.assertMapState(steady_state + [
            [RUS, AMY, CLY],
            [ENG, FLT, CLY, MRT],
        ])
    def test_6F22(self):
        "6.F.22.b  SECOND ORDER PARADOX WITH TWO RESOLUTIONS"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [RUS, AMY, NWY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [RUS, FLT, NTH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH, MRT],
            [GER, FLT, ECH],
            [RUS, FLT, NTH, MRT],
        ])
    def test_6F22_extended(self):
        ''' 6.F.22.extended.b  SECOND ORDER PARADOX WITH TWO RESOLUTIONS
            The Russian move from St Petersbug to Edinburgh is not part
            of the paradox (and the paradox breaker should not be applied
            on this order). When the paradox is resolved and Edinburgh
            is empty, the Russian convoy in St Petersburg can succeed.
        '''#'''
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [RUS, AMY, NWY],
            [RUS, FLT, NWG],
            [RUS, FLT, BAR],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [RUS, FLT, NTH],
            [RUS, AMY, STP],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, BAR), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, STP), CTO, EDI, VIA, [BAR, NWG]])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH, MRT],
            [GER, FLT, ECH],
            [RUS, FLT, NTH, MRT],
            [RUS, AMY, EDI],
        ])
    def test_6F23(self):
        "6.F.23.b  SECOND ORDER PARADOX WITH TWO EXCLUSIVE CONVOYS"
        steady_state = [
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, BEL],
            [GER, FLT, LON],
            [ITA, FLT, MAO],
            [ITA, FLT, IRI],
            [RUS, AMY, NWY],
            [RUS, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, FLT, LON), SUP, (RUS, FLT, NTH)])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(ITA, [(ITA, FLT, IRI), SUP, (ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])
    def test_6F24(self):
        "6.F.24.b  SECOND ORDER PARADOX WITH NO RESOLUTION"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [RUS, AMY, NWY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [RUS, FLT, NTH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [RUS, FLT, NTH, MRT],
        ])

class DATC_6_F_Paradox_Szykman(DiplomacyAdjudicatorTestCase):
    "6.F.  CONVOY PARADOX (SZYKMAN RESOLUTION)"
    # All depend on or relate to 4.A.2 (paradox)
    def setUp(self):
        super(DATC_6_F_Paradox_Szykman, self).setUp()
        self.judge.datc.datc_4a2 = 'd'
    
    def test_6F14(self):
        "6.F.14.d  SIMPLE CONVOY PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, ECH, MRT],
        ])
    def test_6F15(self):
        "6.F.15.d  SIMPLE CONVOY PARADOX WITH ADDITIONAL CONVOY"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [ITA, FLT, IRI],
            [ITA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
            [ITA, AMY, NAF],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(ITA, [(ITA, AMY, NAF), CTO, WAL, VIA, [MAO, IRI]])
        self.legalOrder(ITA, [(ITA, FLT, MAO), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.legalOrder(ITA, [(ITA, FLT, IRI), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, ECH, MRT],
            [ITA, AMY, WAL],
        ])
    def test_6F16(self):
        "6.F.16.d  PANDIN'S PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state)
    def test_6F17(self):
        "6.F.17.d  PANDIN'S EXTENDED PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, YOR],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, YOR), SUP, (FRA, AMY, BRE), MTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state + [
        ])
    def test_6F18(self):
        "6.F.18.d  BETRAYAL PARADOX"
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [ENG, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (ENG, FLT, NTH)])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.assertMapState(steady_state + [
        ])
    def test_6F19_any(self):
        "6.F.19.d.a  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, TYS],
            [ITA, FLT, ROM],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
            [FRA, FLT, TYS, MRT],
            [ITA, FLT, TYS],
        ])
    def test_6F19_all(self):
        "6.F.19.d.b  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
            [ITA, FLT, ROM],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
        ])
    def test_6F20_any(self):
        "6.F.20.d.a  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F20_all(self):
        "6.F.20.d.b  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F21(self):
        "6.F.21.d  DAD'S ARMY CONVOY"
        steady_state = [
            [RUS, AMY, EDI],
            [RUS, FLT, NWG],
            [FRA, FLT, IRI],
            [ENG, AMY, LVP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [RUS, AMY, NWY],
            [FRA, FLT, MAO],
            [ENG, FLT, NAO],
            [ENG, FLT, CLY],
        ])
        self.legalOrder(RUS, [(RUS, AMY, EDI), SUP, (RUS, AMY, NWY), MTO, CLY])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, NWY), CTO, CLY])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, CLY, VIA, [NWG]])
        self.legalOrder(FRA, [(FRA, FLT, IRI), SUP, (FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, CLY, VIA, [NAO]])
        self.legalOrder(ENG, [(ENG, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, CLY])
        self.legalOrder(ENG, [(ENG, FLT, CLY), SUP, (ENG, FLT, NAO)])
        self.assertMapState(steady_state + [
            [RUS, AMY, CLY],
            [FRA, FLT, NAO],
            [ENG, FLT, NAO, MRT],
            [ENG, FLT, CLY, MRT],
        ])
    def test_6F22(self):
        "6.F.22.d  SECOND ORDER PARADOX WITH TWO RESOLUTIONS"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [RUS, AMY, NWY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [RUS, FLT, NTH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH, MRT],
            [GER, FLT, ECH],
            [RUS, FLT, NTH, MRT],
        ])
    def test_6F22_extended(self):
        ''' 6.F.22.extended.d  SECOND ORDER PARADOX WITH TWO RESOLUTIONS
            The Russian move from St Petersbug to Edinburgh is not part
            of the paradox (and the paradox breaker should not be applied
            on this order). When the paradox is resolved and Edinburgh
            is empty, the Russian convoy in St Petersburg can succeed.
        '''#'''
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [RUS, AMY, NWY],
            [RUS, FLT, NWG],
            [RUS, FLT, BAR],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [RUS, FLT, NTH],
            [RUS, AMY, STP],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, BAR), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, STP), CTO, EDI, VIA, [BAR, NWG]])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH, MRT],
            [GER, FLT, ECH],
            [RUS, FLT, NTH, MRT],
            [RUS, AMY, EDI],
        ])
    def test_6F23(self):
        "6.F.23.d  SECOND ORDER PARADOX WITH TWO EXCLUSIVE CONVOYS"
        steady_state = [
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, BEL],
            [GER, FLT, LON],
            [ITA, FLT, MAO],
            [ITA, FLT, IRI],
            [RUS, AMY, NWY],
            [RUS, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, FLT, LON), SUP, (RUS, FLT, NTH)])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(ITA, [(ITA, FLT, IRI), SUP, (ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])
    def test_6F24(self):
        "6.F.24.d  SECOND ORDER PARADOX WITH NO RESOLUTION"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [RUS, AMY, NWY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [RUS, FLT, NTH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [RUS, FLT, NTH, MRT],
        ])

class DATC_6_F_Paradox_Hold(DiplomacyAdjudicatorTestCase):
    "6.F.  CONVOY PARADOX (ALL-HOLD RESOLUTION)"
    # All depend on or relate to 4.A.2 (paradox)
    def setUp(self):
        super(DATC_6_F_Paradox_Hold, self).setUp()
        self.judge.datc.datc_4a2 = 'e'
    
    def test_6F14(self):
        "6.F.14.e  SIMPLE CONVOY PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
            [FRA, AMY, BRE],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.assertMapState(steady_state)
    def test_6F15(self):
        "6.F.15.e  SIMPLE CONVOY PARADOX WITH ADDITIONAL CONVOY"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [ITA, AMY, NAF],
            [ITA, FLT, IRI],
            [ITA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(ITA, [(ITA, AMY, NAF), CTO, WAL, VIA, [MAO, IRI]])
        self.legalOrder(ITA, [(ITA, FLT, MAO), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.legalOrder(ITA, [(ITA, FLT, IRI), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.assertMapState(steady_state)
    def test_6F16(self):
        "6.F.16.e  PANDIN'S PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state)
    def test_6F17(self):
        "6.F.17.e  PANDIN'S EXTENDED PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, YOR],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, YOR), SUP, (FRA, AMY, BRE), MTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state)
    def test_6F18(self):
        "6.F.18.e  BETRAYAL PARADOX"
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [ENG, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (ENG, FLT, NTH)])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.assertMapState(steady_state)
    def test_6F19_any(self):
        "6.F.19.e.a  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, ION],
            [FRA, FLT, TYS],
            [ITA, FLT, ROM],
            [ITA, FLT, NAP],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
        ])
    def test_6F19_all(self):
        "6.F.19.e.b  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
            [ITA, FLT, ROM],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
        ])
    def test_6F20_any(self):
        "6.F.20.e.a  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F20_all(self):
        "6.F.20.e.b  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F21(self):
        "6.F.21.e  DAD'S ARMY CONVOY"
        steady_state = [
            [RUS, AMY, EDI],
            [RUS, FLT, NWG],
            [FRA, FLT, IRI],
            [ENG, AMY, LVP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [RUS, AMY, NWY],
            [FRA, FLT, MAO],
            [ENG, FLT, NAO],
            [ENG, FLT, CLY],
        ])
        self.legalOrder(RUS, [(RUS, AMY, EDI), SUP, (RUS, AMY, NWY), MTO, CLY])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, NWY), CTO, CLY])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, CLY, VIA, [NWG]])
        self.legalOrder(FRA, [(FRA, FLT, IRI), SUP, (FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, CLY, VIA, [NAO]])
        self.legalOrder(ENG, [(ENG, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, CLY])
        self.legalOrder(ENG, [(ENG, FLT, CLY), SUP, (ENG, FLT, NAO)])
        self.assertMapState(steady_state + [
            [RUS, AMY, CLY],
            [FRA, FLT, NAO],
            [ENG, FLT, NAO, MRT],
            [ENG, FLT, CLY, MRT],
        ])
    def test_6F22(self):
        "6.F.22.e  SECOND ORDER PARADOX WITH TWO RESOLUTIONS"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, EDI],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [GER, FLT, BEL],
            [RUS, FLT, NTH],
            [RUS, AMY, NWY],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])
    def test_6F22_extended(self):
        ''' 6.F.22.extended.e  SECOND ORDER PARADOX WITH TWO RESOLUTIONS
            The Russian move from St Petersbug to Edinburgh is not part
            of the paradox (and the paradox breaker should not be applied
            on this order). When the paradox is resolved and Edinburgh
            is empty, the Russian convoy in St Petersburg can succeed.
        '''#'''
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [GER, FLT, PIC],
            [RUS, AMY, NWY],
            [RUS, FLT, NWG],
            [RUS, FLT, BAR],
            [RUS, FLT, NTH],
            [RUS, AMY, STP],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, BAR), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, STP), CTO, EDI, VIA, [BAR, NWG]])
        self.assertMapState(steady_state + [
        ])
    def test_6F23(self):
        "6.F.23.e  SECOND ORDER PARADOX WITH TWO EXCLUSIVE CONVOYS"
        steady_state = [
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, BEL],
            [GER, FLT, LON],
            [ITA, FLT, MAO],
            [ITA, FLT, IRI],
            [RUS, AMY, NWY],
            [RUS, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, FLT, LON), SUP, (RUS, FLT, NTH)])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(ITA, [(ITA, FLT, IRI), SUP, (ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])
    def test_6F24(self):
        "6.F.24.e  SECOND ORDER PARADOX WITH NO RESOLUTION"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [ENG, FLT, EDI],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [RUS, AMY, NWY],
            [RUS, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])

class DATC_6_F_Paradox_DPTG(DiplomacyAdjudicatorTestCase):
    "6.F.  CONVOY PARADOX (DPTG RESOLUTION)"
    # All depend on or relate to 4.A.2 (paradox)
    def setUp(self):
        super(DATC_6_F_Paradox_DPTG, self).setUp()
        self.judge.datc.datc_4a2 = 'f'
    
    def test_6F14(self):
        "6.F.14.f  SIMPLE CONVOY PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, ECH, MRT],
        ])
    def test_6F15(self):
        "6.F.15.f  SIMPLE CONVOY PARADOX WITH ADDITIONAL CONVOY"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [ITA, FLT, IRI],
            [ITA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, WAL],
            [FRA, FLT, ECH],
            [ITA, AMY, NAF],
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(ITA, [(ITA, AMY, NAF), CTO, WAL, VIA, [MAO, IRI]])
        self.legalOrder(ITA, [(ITA, FLT, MAO), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.legalOrder(ITA, [(ITA, FLT, IRI), CVY, (ITA, AMY, NAF), CTO, WAL])
        self.assertMapState(steady_state + [
            [ENG, FLT, ECH],
            [FRA, FLT, ECH, MRT],
            [ITA, AMY, WAL],
        ])
    def test_6F16(self):
        "6.F.16.f  PANDIN'S PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state)
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state)
    def test_6F17(self):
        "6.F.17.f  PANDIN'S EXTENDED PARADOX"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, WAL],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, YOR],
            [GER, FLT, NTH],
            [GER, FLT, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, WAL), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, YOR), SUP, (FRA, AMY, BRE), MTO, LON])
        self.legalOrder(GER, [(GER, FLT, NTH), SUP, (GER, FLT, BEL), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, BEL), MTO, ECH])
        self.assertMapState(steady_state + [
        ])
    def test_6F18(self):
        "6.F.18.f  BETRAYAL PARADOX"
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, LON],
            [ENG, FLT, ECH],
            [FRA, FLT, BEL],
            [GER, FLT, HEL],
            [GER, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, ECH), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (ENG, FLT, NTH)])
        self.legalOrder(GER, [(GER, FLT, HEL), SUP, (GER, FLT, SKA), MTO, NTH])
        self.legalOrder(GER, [(GER, FLT, SKA), MTO, NTH])
        self.assertMapState(steady_state + [
        ])
    def test_6F19_any(self):
        "6.F.19.f.a  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, TYS],
            [ITA, FLT, ROM],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
            [FRA, FLT, TYS, MRT],
            [ITA, FLT, TYS],
        ])
    def test_6F19_all(self):
        "6.F.19.f.b  MULTI-ROUTE CONVOY DISRUPTION PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [FRA, FLT, ION],
            [ITA, FLT, NAP],
            [ITA, FLT, ROM],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ROM), MTO, TYS])
        self.legalOrder(ITA, [(ITA, FLT, ROM), MTO, TYS])
        self.assertMapState(steady_state + [
        ])
    def test_6F20_any(self):
        "6.F.20.f.a  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'a'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F20_all(self):
        "6.F.20.f.b  UNWANTED MULTI-ROUTE CONVOY PARADOX"
        # 4.A.1, as well
        self.judge.datc.datc_4a1 = 'b'
        steady_state = [
            [FRA, AMY, TUN],
            [FRA, FLT, TYS],
            [ITA, FLT, NAP],
            [TUR, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, FLT, ION],
            [TUR, FLT, EAS],
        ])
        self.legalOrder(FRA, [(FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(FRA, [(FRA, FLT, TYS), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(ITA, [(ITA, FLT, NAP), SUP, (ITA, FLT, ION)])
        self.legalOrder(ITA, [(ITA, FLT, ION), CVY, (FRA, AMY, TUN), CTO, NAP])
        self.legalOrder(TUR, [(TUR, FLT, AEG), SUP, (TUR, FLT, EAS), MTO, ION])
        self.legalOrder(TUR, [(TUR, FLT, EAS), MTO, ION])
        self.assertMapState(steady_state + [
            [ITA, FLT, ION, MRT],
            [TUR, FLT, ION],
        ])
    def test_6F21(self):
        "6.F.21.f  DAD'S ARMY CONVOY"
        steady_state = [
            [RUS, AMY, EDI],
            [RUS, FLT, NWG],
            [FRA, FLT, IRI],
            [ENG, AMY, LVP],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [RUS, AMY, NWY],
            [FRA, FLT, MAO],
            [ENG, FLT, NAO],
            [ENG, FLT, CLY],
        ])
        self.legalOrder(RUS, [(RUS, AMY, EDI), SUP, (RUS, AMY, NWY), MTO, CLY])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, NWY), CTO, CLY])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, CLY, VIA, [NWG]])
        self.legalOrder(FRA, [(FRA, FLT, IRI), SUP, (FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, NAO])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, CLY, VIA, [NAO]])
        self.legalOrder(ENG, [(ENG, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, CLY])
        self.legalOrder(ENG, [(ENG, FLT, CLY), SUP, (ENG, FLT, NAO)])
        self.assertMapState(steady_state + [
            [RUS, AMY, CLY],
            [FRA, FLT, NAO],
            [ENG, FLT, NAO, MRT],
            [ENG, FLT, CLY, MRT],
        ])
    def test_6F22(self):
        "6.F.22.f  SECOND ORDER PARADOX WITH TWO RESOLUTIONS"
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [RUS, AMY, NWY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [RUS, FLT, NTH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH, MRT],
            [GER, FLT, ECH],
            [RUS, FLT, NTH, MRT],
        ])
    def test_6F22_extended(self):
        ''' 6.F.22.extended.f  SECOND ORDER PARADOX WITH TWO RESOLUTIONS
            The Russian move from St Petersbug to Edinburgh is not part
            of the paradox (and the paradox breaker should not be applied
            on this order). When the paradox is resolved and Edinburgh
            is empty, the Russian convoy in St Petersburg can succeed.
        '''#'''
        steady_state = [
            [ENG, FLT, LON],
            [FRA, AMY, BRE],
            [GER, FLT, BEL],
            [RUS, AMY, NWY],
            [RUS, FLT, NWG],
            [RUS, FLT, BAR],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, EDI],
            [FRA, FLT, ECH],
            [GER, FLT, PIC],
            [RUS, FLT, NTH],
            [RUS, AMY, STP],
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (GER, FLT, PIC), MTO, ECH])
        self.legalOrder(GER, [(GER, FLT, PIC), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, BAR), CVY, (RUS, AMY, STP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, STP), CTO, EDI, VIA, [BAR, NWG]])
        self.assertMapState(steady_state + [
            [ENG, FLT, NTH],
            [FRA, FLT, ECH, MRT],
            [GER, FLT, ECH],
            [RUS, FLT, NTH, MRT],
            [RUS, AMY, EDI],
        ])
    def test_6F23(self):
        "6.F.23.f  SECOND ORDER PARADOX WITH TWO EXCLUSIVE CONVOYS"
        steady_state = [
            [ENG, FLT, EDI],
            [ENG, FLT, YOR],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [GER, FLT, BEL],
            [GER, FLT, LON],
            [ITA, FLT, MAO],
            [ITA, FLT, IRI],
            [RUS, AMY, NWY],
            [RUS, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(GER, [(GER, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(GER, [(GER, FLT, LON), SUP, (RUS, FLT, NTH)])
        self.legalOrder(ITA, [(ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(ITA, [(ITA, FLT, IRI), SUP, (ITA, FLT, MAO), MTO, ECH])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])
    def test_6F24(self):
        "6.F.24.f  SECOND ORDER PARADOX WITH NO RESOLUTION"
        steady_state = [
            [ENG, FLT, LON],
            [ENG, FLT, IRI],
            [ENG, FLT, MAO],
            [ENG, FLT, EDI],
            [FRA, AMY, BRE],
            [FRA, FLT, ECH],
            [FRA, FLT, BEL],
            [RUS, AMY, NWY],
            [RUS, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, LON), SUP, (ENG, FLT, EDI), MTO, NTH])
        self.legalOrder(ENG, [(ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, MAO), SUP, (ENG, FLT, IRI), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, BRE), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BRE), CTO, LON])
        self.legalOrder(FRA, [(FRA, FLT, BEL), SUP, (FRA, FLT, ECH)])
        self.legalOrder(RUS, [(RUS, AMY, NWY), CTO, BEL, VIA, [NTH]])
        self.legalOrder(RUS, [(RUS, FLT, NTH), CVY, (RUS, AMY, NWY), CTO, BEL])
        self.assertMapState(steady_state + [
        ])

class DATC_6_G_CTO(DiplomacyAdjudicatorTestCase):
    "6.G.  CONVOYING TO ADJACENT PLACES"
    # This batch always uses CTO for the possibly convoyed units,
    # even where that's not really the intent.
    def test_6G1(self):
        "6.G.1.c  TWO UNITS CAN SWAP PLACES BY CONVOY"
        steady_state = [
            [ENG, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), CTO, SWE, VIA, [SKA]])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G2(self):
        "6.G.2.c  KIDNAPPING AN ARMY"
        steady_state = [
            [GER, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), CTO, SWE, VIA, [SKA]])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G3(self):
        "6.G.3.c  KIDNAPPING WITH A DISRUPTED CONVOY"
        steady_state = [
            [FRA, AMY, PIC],
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), CTO, BEL, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.assertMapState(steady_state + [
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
        ])
    def test_6G4(self):
        "6.G.4.c  KIDNAPPING WITH A DISRUPTED CONVOY AND OPPOSITE MOVE"
        steady_state = [
            [FRA, AMY, PIC],
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [ENG, AMY, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), CTO, BEL, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, BEL), MTO, PIC])
        self.assertMapState(steady_state + [
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
        ])
    def test_6G5(self):
        "6.G.5.c  SWAPPING WITH INTENT"
        steady_state = [
            [ITA, FLT, TYS],
            [TUR, FLT, ION],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, AMY, ROM],
            [TUR, AMY, APU],
        ])
        self.legalOrder(ITA, [(ITA, AMY, ROM), MTO, APU])
        self.legalOrder(ITA, [(ITA, FLT, TYS), CVY, (TUR, AMY, APU), CTO, ROM])
        self.legalOrder(TUR, [(TUR, AMY, APU), CTO, ROM, VIA, [ION, TYS]])
        self.legalOrder(TUR, [(TUR, FLT, ION), CVY, (TUR, AMY, APU), CTO, ROM])
        self.assertMapState(steady_state + [
            [ITA, AMY, APU],
            [TUR, AMY, ROM],
        ])
    def test_6G6(self):
        "6.G.6.c  SWAPPING WITH UNINTENDED INTENT"
        steady_state = [
            [ENG, FLT, ECH],
            [FRA, FLT, IRI],
            [FRA, FLT, NTH],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [GER, AMY, EDI],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(GER, [(GER, AMY, EDI), MTO, LVP])
        self.legalOrder(FRA, [(FRA, FLT, IRI), HLD])
        self.legalOrder(FRA, [(FRA, FLT, NTH), HLD])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [GER, AMY, LVP],
        ])
    def test_6G8(self):
        "6.G.8.c  EXPLICIT CONVOY THAT ISN'T THERE"
        steady_state = [
            [FRA, AMY, BEL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
        ])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, HOL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, HEL])
        self.legalOrder(ENG, [(ENG, AMY, HOL), MTO, KIE])
        self.assertMapState(steady_state + [
            [ENG, FLT, HEL],
            [ENG, AMY, KIE],
        ])
    def test_6G9(self):
        "6.G.9.c  SWAPPED OR DISLODGED?"
        steady_state = [
            [ENG, FLT, SKA],
            [ENG, FLT, FIN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), CTO, SWE, VIA, [SKA]])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G12(self):
        "6.G.12.c  SWAPPING TWO UNITS WITH TWO CONVOYS"
        steady_state = [
            [ENG, FLT, NWG],
            [ENG, FLT, NAO],
            [GER, FLT, NTH],
            [GER, FLT, IRI],
            [GER, FLT, ECH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [GER, AMY, EDI],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, EDI, VIA, [NAO, NWG]])
        self.legalOrder(ENG, [(ENG, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NWG), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(GER, [(GER, AMY, EDI), CTO, LVP, VIA, [NTH, ECH, IRI]])
        self.legalOrder(GER, [(GER, FLT, NTH), CVY, (GER, AMY, EDI), CTO, LVP])
        self.legalOrder(GER, [(GER, FLT, ECH), CVY, (GER, AMY, EDI), CTO, LVP])
        self.legalOrder(GER, [(GER, FLT, IRI), CVY, (GER, AMY, EDI), CTO, LVP])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [GER, AMY, LVP],
        ])
    def test_6G16(self):
        "6.G.16.c  THE TWO UNIT IN ONE AREA BUG, MOVING BY CONVOY"
        steady_state = [
            [ENG, AMY, DEN],
            [ENG, FLT, BAL],
            [ENG, FLT, NTH],
            [RUS, FLT, SKA],
            [RUS, FLT, NWG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, AMY, DEN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, BAL), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, NWY])
        self.legalOrder(RUS, [(RUS, AMY, SWE), CTO, NWY, VIA, [SKA]])
        self.legalOrder(RUS, [(RUS, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, NWG), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G17(self):
        "6.G.17.c  THE TWO UNIT IN ONE AREA BUG, MOVING OVER LAND"
        steady_state = [
            [ENG, AMY, DEN],
            [ENG, FLT, BAL],
            [ENG, FLT, SKA],
            [ENG, FLT, NTH],
            [RUS, FLT, NWG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), CTO, SWE, VIA, [SKA]])
        self.legalOrder(ENG, [(ENG, AMY, DEN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, BAL), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, NWY])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, NWG), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G18(self):
        "6.G.18.c  THE TWO UNIT IN ONE AREA BUG, WITH DOUBLE CONVOY"
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
            [ENG, AMY, YOR],
            [ENG, AMY, RUH],
            [FRA, FLT, ECH],
            [FRA, AMY, WAL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [FRA, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, HOL), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, YOR), MTO, LON])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(ENG, [(ENG, AMY, RUH), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.legalOrder(FRA, [(FRA, AMY, WAL), SUP, (FRA, AMY, BEL), MTO, LON])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, LON],
        ])

class DATC_6_G_MTO(DiplomacyAdjudicatorTestCase):
    "6.G.  CONVOYING TO ADJACENT PLACES"
    # Most of these depend on or relate to 4.A.3
    # This batch always uses MTO for the possibly convoyed units,
    # sometimes allowing the judge to guess the intent.
    def test_6G1_f(self):
        "6.G.1.m.f  TWO UNITS CAN SWAP PLACES BY CONVOY"
        self.judge.datc.datc_4a3 = 'f'
        steady_state = [
            [ENG, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
        ])
    def test_6G1_d(self):
        "6.G.1.m.d  TWO UNITS CAN SWAP PLACES BY CONVOY"
        self.judge.datc.datc_4a3 = 'd'
        steady_state = [
            [ENG, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G2(self):
        "6.G.2.m  KIDNAPPING AN ARMY"
        steady_state = [
            [GER, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.assertMapState(steady_state + [
        ])
    def test_6G3(self):
        "6.G.3.m  KIDNAPPING WITH A DISRUPTED CONVOY"
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
        ])
    def test_6G4(self):
        "6.G.4.m  KIDNAPPING WITH A DISRUPTED CONVOY AND OPPOSITE MOVE"
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, PIC],
            [FRA, FLT, BRE],
            [ENG, FLT, ECH],
            [ENG, AMY, BEL],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (FRA, AMY, PIC), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, BEL), MTO, PIC])
        self.assertMapState(steady_state + [
            [FRA, AMY, BEL],
            [FRA, FLT, ECH],
            [ENG, FLT, ECH, MRT],
            [ENG, AMY, BEL, MRT],
        ])
    def test_6G5_f(self):
        "6.G.5.m.f  SWAPPING WITH INTENT"
        self.judge.datc.datc_4a3 = 'f'
        steady_state = [
            [ITA, FLT, TYS],
            [ITA, AMY, ROM],
            [TUR, AMY, APU],
            [TUR, FLT, ION],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ITA, [(ITA, AMY, ROM), MTO, APU])
        self.legalOrder(ITA, [(ITA, FLT, TYS), CVY, (TUR, AMY, APU), CTO, ROM])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, ROM])
        self.legalOrder(TUR, [(TUR, FLT, ION), CVY, (TUR, AMY, APU), CTO, ROM])
        self.assertMapState(steady_state + [
        ])
    def test_6G5_d(self):
        "6.G.5.m.d  SWAPPING WITH INTENT"
        self.judge.datc.datc_4a3 = 'd'
        steady_state = [
            [ITA, FLT, TYS],
            [TUR, FLT, ION],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ITA, AMY, ROM],
            [TUR, AMY, APU],
        ])
        self.legalOrder(ITA, [(ITA, AMY, ROM), MTO, APU])
        self.legalOrder(ITA, [(ITA, FLT, TYS), CVY, (TUR, AMY, APU), CTO, ROM])
        self.legalOrder(TUR, [(TUR, AMY, APU), MTO, ROM])
        self.legalOrder(TUR, [(TUR, FLT, ION), CVY, (TUR, AMY, APU), CTO, ROM])
        self.assertMapState(steady_state + [
            [ITA, AMY, APU],
            [TUR, AMY, ROM],
        ])
    def test_6G6_f(self):
        "6.G.6.m.f  SWAPPING WITH UNINTENDED INTENT"
        self.judge.datc.datc_4a3 = 'f'
        steady_state = [
            [ENG, FLT, ECH],
            [ENG, AMY, LVP],
            [GER, AMY, EDI],
            [FRA, FLT, IRI],
            [FRA, FLT, NTH],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(GER, [(GER, AMY, EDI), MTO, LVP])
        self.legalOrder(FRA, [(FRA, FLT, IRI), HLD])
        self.legalOrder(FRA, [(FRA, FLT, NTH), HLD])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.assertMapState(steady_state + [
        ])
    def test_6G6_d(self):
        "6.G.6.m.d  SWAPPING WITH UNINTENDED INTENT"
        self.judge.datc.datc_4a3 = 'd'
        steady_state = [
            [ENG, FLT, ECH],
            [FRA, FLT, IRI],
            [FRA, FLT, NTH],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [GER, AMY, EDI],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(GER, [(GER, AMY, EDI), MTO, LVP])
        self.legalOrder(FRA, [(FRA, FLT, IRI), HLD])
        self.legalOrder(FRA, [(FRA, FLT, NTH), HLD])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [GER, AMY, LVP],
        ])
    def test_6G9_f(self):
        "6.G.9.m.f  SWAPPED OR DISLODGED?"
        self.judge.datc.datc_4a3 = 'f'
        steady_state = [
            [ENG, FLT, SKA],
            [ENG, FLT, FIN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, SWE, MRT],
        ])
    def test_6G9_d(self):
        "6.G.9.m.d  SWAPPED OR DISLODGED?"
        self.judge.datc.datc_4a3 = 'd'
        steady_state = [
            [ENG, FLT, SKA],
            [ENG, FLT, FIN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])

class DATC_6_G_Disputable(DiplomacyAdjudicatorTestCase):
    "6.G.  CONVOYING TO ADJACENT PLACES"
    # Many of these depend on or relate to 4.A.3
    def test_6G7_always(self):
        "6.G.7.a  SWAPPING WITH ILLEGAL INTENT"
        self.judge.datc.datc_4a3 = 'a'
        steady_state = [
            [ENG, FLT, SKA],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.illegalOrder(RUS, [(RUS, FLT, GOB), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G7_swap(self):
        "6.G.7.b  SWAPPING WITH ILLEGAL INTENT"
        self.judge.datc.datc_4a3 = 'b'
        steady_state = [
            [ENG, FLT, SKA],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.illegalOrder(RUS, [(RUS, FLT, GOB), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G7_undisrupted(self):
        "6.G.7.c  SWAPPING WITH ILLEGAL INTENT"
        self.judge.datc.datc_4a3 = 'c'
        steady_state = [
            [ENG, FLT, SKA],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.illegalOrder(RUS, [(RUS, FLT, GOB), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G7_intent_quasi(self):
        "6.G.7.d.a  SWAPPING WITH ILLEGAL INTENT"
        # 4.E.1 (quasi_legal)
        self.judge.datc.datc_4a3 = 'd'
        self.judge.datc.datc_4e1 = 'a'
        self.judge.game_opts.AOA = True
        self.illegalOrder = self.legalOrder
        steady_state = [
            [ENG, FLT, SKA],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.illegalOrder(RUS, [(RUS, FLT, GOB), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, NWY],
        ])
    def test_6G7_intent_illegal(self):
        "6.G.7.d.d  SWAPPING WITH ILLEGAL INTENT"
        # 4.E.1 (quasi_legal)
        self.judge.datc.datc_4a3 = 'd'
        self.judge.datc.datc_4e1 = 'd'
        self.judge.game_opts.AOA = True
        self.illegalOrder = self.legalOrder
        steady_state = [
            [ENG, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.illegalOrder(RUS, [(RUS, FLT, GOB), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.assertMapState(steady_state + [
        ])
    def test_6G7_explicit(self):
        "6.G.7.e  SWAPPING WITH ILLEGAL INTENT"
        self.judge.datc.datc_4a3 = 'e'
        steady_state = [
            [ENG, FLT, SKA],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [RUS, FLT, GOB],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(ENG, [(ENG, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.illegalOrder(RUS, [(RUS, FLT, GOB), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.assertMapState(steady_state + [
        ])
    @fails
    def test_6G10_never(self):
        "6.G.10.a  SWAPPED OR AN HEAD TO HEAD BATTLE?"
        self.judge.datc.datc_4a7 = 'a'
        steady_state = [
            [ENG, FLT, DEN],
            [ENG, FLT, FIN],
            [GER, FLT, SKA],
            [RUS, FLT, BAR],
            [FRA, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
            [FRA, FLT, NWG],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), CTO, SWE, VIA, [SKA]])
        self.legalOrder(ENG, [(ENG, FLT, DEN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, BAR), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(FRA, [(FRA, FLT, NWG), MTO, NWY])
        self.legalOrder(FRA, [(FRA, FLT, NTH), SUP, (FRA, FLT, NWG), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, SWE, MRT],
            [FRA, FLT, NWY],
        ])
    def test_6G10_bounce(self):
        "6.G.10.b  SWAPPED OR AN HEAD TO HEAD BATTLE?"
        self.judge.datc.datc_4a7 = 'b'
        steady_state = [
            [ENG, FLT, DEN],
            [ENG, FLT, FIN],
            [GER, FLT, SKA],
            [RUS, FLT, BAR],
            [FRA, FLT, NWG],
            [FRA, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), CTO, SWE, VIA, [SKA]])
        self.legalOrder(ENG, [(ENG, FLT, DEN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (ENG, AMY, NWY), CTO, SWE])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, BAR), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(FRA, [(FRA, FLT, NWG), MTO, NWY])
        self.legalOrder(FRA, [(FRA, FLT, NTH), SUP, (FRA, FLT, NWG), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, SWE, MRT],
        ])
    def test_6G11_Szykman(self):
        "6.G.11.d  A CONVOY TO AN ADJACENT PLACE WITH A PARADOX"
        # This situation becomes paradoxical if we must choose
        # between the land and convoy routes (4.A.3 a or d).
        self.judge.datc.datc_4a3 = 'f'
        self.judge.datc.datc_4a2 = 'd'
        steady_state = [
            [ENG, FLT, NTH],
            [RUS, FLT, BAR],
            [RUS, FLT, SKA],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), MTO, SKA])
        self.legalOrder(ENG, [(ENG, FLT, NWY), SUP, (ENG, FLT, NTH), MTO, SKA])
        self.legalOrder(RUS, [(RUS, AMY, SWE), MTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, BAR), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, FLT, NWY, MRT],
            [RUS, AMY, NWY],
        ])
    def test_6G13_given(self):
        "6.G.13.a  SUPPORT CUT ON ATTACK ON ITSELF VIA CONVOY"
        self.judge.datc.datc_4a4 = 'a'
        steady_state = [
            [AUS, FLT, ADR],
            [ITA, FLT, VEN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [AUS, AMY, TRI],
            [ITA, AMY, ALB],
        ])
        self.legalOrder(AUS, [(AUS, AMY, TRI), CTO, VEN, VIA, [ADR]])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, ALB), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, VEN), SUP, (ITA, AMY, ALB), MTO, TRI])
        self.assertMapState(steady_state + [
            [AUS, AMY, TRI, MRT],
            [ITA, AMY, TRI],
        ])
    @fails
    def test_6G13_cut(self):
        "6.G.13.b  SUPPORT CUT ON ATTACK ON ITSELF VIA CONVOY"
        self.judge.datc.datc_4a4 = 'b'
        steady_state = [
            [AUS, FLT, ADR],
            [AUS, AMY, TRI],
            [ITA, AMY, ALB],
            [ITA, FLT, VEN],
        ]
        self.init_state(SPR, 1901, steady_state + [
        ])
        self.legalOrder(AUS, [(AUS, AMY, TRI), CTO, VEN, VIA, [ADR]])
        self.legalOrder(AUS, [(AUS, FLT, ADR), CVY, (AUS, AMY, TRI), CTO, VEN])
        self.legalOrder(ITA, [(ITA, AMY, ALB), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, VEN), SUP, (ITA, AMY, ALB), MTO, TRI])
        self.assertMapState(steady_state + [
        ])
    @fails
    def test_6G14_never(self):
        "6.G.14.a  BOUNCE BY CONVOY TO ADJACENT PLACE"
        self.judge.datc.datc_4a7 = 'a'
        steady_state = [
            [ENG, FLT, DEN],
            [ENG, FLT, FIN],
            [GER, FLT, SKA],
            [RUS, FLT, BAR],
            [FRA, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, NWG],
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, DEN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(FRA, [(FRA, FLT, NWG), MTO, NWY])
        self.legalOrder(FRA, [(FRA, FLT, NTH), SUP, (FRA, FLT, NWG), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(RUS, [(RUS, AMY, SWE), CTO, NWY, VIA, [SKA]])
        self.legalOrder(RUS, [(RUS, FLT, BAR), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [FRA, FLT, NWY],
            [ENG, AMY, SWE],
            [RUS, AMY, SWE, MRT],
        ])
    def test_6G14_bounce(self):
        "6.G.14.b  BOUNCE BY CONVOY TO ADJACENT PLACE"
        self.judge.datc.datc_4a7 = 'b'
        steady_state = [
            [ENG, FLT, DEN],
            [ENG, FLT, FIN],
            [GER, FLT, SKA],
            [RUS, FLT, BAR],
            [FRA, FLT, NWG],
            [FRA, FLT, NTH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, NWY],
            [RUS, AMY, SWE],
        ])
        self.legalOrder(ENG, [(ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, DEN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(ENG, [(ENG, FLT, FIN), SUP, (ENG, AMY, NWY), MTO, SWE])
        self.legalOrder(FRA, [(FRA, FLT, NWG), MTO, NWY])
        self.legalOrder(FRA, [(FRA, FLT, NTH), SUP, (FRA, FLT, NWG), MTO, NWY])
        self.legalOrder(GER, [(GER, FLT, SKA), CVY, (RUS, AMY, SWE), CTO, NWY])
        self.legalOrder(RUS, [(RUS, AMY, SWE), CTO, NWY, VIA, [SKA]])
        self.legalOrder(RUS, [(RUS, FLT, BAR), SUP, (RUS, AMY, SWE), MTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, SWE],
            [RUS, AMY, SWE, MRT],
        ])
    @fails
    def test_6G15_never(self):
        "6.G.15.a  BOUNCE AND DISLODGE WITH DOUBLE CONVOY"
        self.judge.datc.datc_4a7 = 'a'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
            [ENG, AMY, LON],
            [FRA, FLT, ECH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, YOR],
            [FRA, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, HOL), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, YOR), MTO, LON])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, BEL, MRT],
        ])
    def test_6G15_bounce(self):
        "6.G.15.b  BOUNCE AND DISLODGE WITH DOUBLE CONVOY"
        self.judge.datc.datc_4a7 = 'b'
        steady_state = [
            [ENG, FLT, NTH],
            [ENG, AMY, HOL],
            [ENG, AMY, YOR],
            [FRA, FLT, ECH],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LON],
            [FRA, AMY, BEL],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LON), CTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, HOL), SUP, (ENG, AMY, LON), MTO, BEL])
        self.legalOrder(ENG, [(ENG, AMY, YOR), MTO, LON])
        self.legalOrder(ENG, [(ENG, AMY, LON), CTO, BEL, VIA, [NTH]])
        self.legalOrder(FRA, [(FRA, FLT, ECH), CVY, (FRA, AMY, BEL), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, BEL), CTO, LON, VIA, [ECH]])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [FRA, AMY, BEL, MRT],
        ])

class DATC_6_H(DiplomacyAdjudicatorTestCase):
    "6.H.  RETREATING"
    def test_6H1(self):
        "6.H.1.  NO SUPPORTS DURING RETREAT"
        steady_state = [
            [AUS, AMY, SER],
            [ITA, AMY, VEN],
            [ITA, FLT, AEG],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [AUS, FLT, TRI],
            [TUR, FLT, GRE],
            [ITA, AMY, TYR],
            [ITA, FLT, ION],
        ])
        self.legalOrder(AUS, [(AUS, FLT, TRI), HLD])
        self.legalOrder(AUS, [(AUS, AMY, SER), HLD])
        self.legalOrder(TUR, [(TUR, FLT, GRE), HLD])
        self.legalOrder(ITA, [(ITA, AMY, VEN), SUP, (ITA, AMY, TYR), MTO, TRI])
        self.legalOrder(ITA, [(ITA, AMY, TYR), MTO, TRI])
        self.legalOrder(ITA, [(ITA, FLT, ION), MTO, GRE])
        self.legalOrder(ITA, [(ITA, FLT, AEG), SUP, (ITA, FLT, ION), MTO, GRE])
        self.assertMapState(steady_state + [
            [AUS, FLT, TRI, MRT],
            [TUR, FLT, GRE, MRT],
            [ITA, AMY, TRI],
            [ITA, FLT, GRE],
        ])
        self.legalOrder(AUS, [(AUS, FLT, TRI), RTO, ALB])
        self.illegalOrder(AUS, [(AUS, AMY, SER), SUP, (AUS, FLT, TRI), MTO, ALB])
        self.legalOrder(TUR, [(TUR, FLT, GRE), RTO, ALB])
        self.assertMapState(steady_state + [
            [ITA, AMY, TRI],
            [ITA, FLT, GRE],
        ])
    def test_6H2(self):
        "6.H.2.  NO SUPPORTS FROM RETREATING UNIT"
        steady_state = [
            [ENG, FLT, YOR],
            [GER, AMY, KIE],
            [RUS, AMY, SWE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [GER, AMY, RUH],
            [RUS, AMY, FIN],
            [ENG, FLT, NWY],
            [RUS, FLT, EDI],
            [RUS, FLT, HOL],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, AMY, LVP), MTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NWY), HLD])
        self.legalOrder(GER, [(GER, AMY, KIE), SUP, (GER, AMY, RUH), MTO, HOL])
        self.legalOrder(GER, [(GER, AMY, RUH), MTO, HOL])
        self.legalOrder(RUS, [(RUS, FLT, EDI), HLD])
        self.legalOrder(RUS, [(RUS, AMY, SWE), SUP, (RUS, AMY, FIN), MTO, NWY])
        self.legalOrder(RUS, [(RUS, AMY, FIN), MTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, HOL), HLD])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [GER, AMY, HOL],
            [RUS, AMY, NWY],
            [ENG, FLT, NWY, MRT],
            [RUS, FLT, EDI, MRT],
            [RUS, FLT, HOL, MRT],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NWY), RTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, EDI), RTO, NTH])
        self.illegalOrder(RUS, [(RUS, FLT, HOL), SUP, (RUS, FLT, EDI), MTO, NTH])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [GER, AMY, HOL],
            [RUS, AMY, NWY],
        ])
    def test_6H3(self):
        "6.H.3.  NO CONVOY DURING RETREAT"
        steady_state = [
            [ENG, FLT, NTH],
            [GER, FLT, KIE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, HOL],
            [GER, AMY, RUH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), HLD])
        self.legalOrder(ENG, [(ENG, AMY, HOL), HLD])
        self.legalOrder(GER, [(GER, FLT, KIE), SUP, (GER, AMY, RUH), MTO, HOL])
        self.legalOrder(GER, [(GER, AMY, RUH), MTO, HOL])
        self.assertMapState(steady_state + [
            [ENG, AMY, HOL, MRT],
            [GER, AMY, HOL],
        ])
        self.illegalOrder(ENG, [(ENG, AMY, HOL), CTO, YOR])
        self.illegalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, HOL), CTO, YOR])
        self.assertMapState(steady_state + [
            [GER, AMY, HOL],
        ])
    def test_6H4(self):
        "6.H.4.  NO OTHER MOVES DURING RETREAT"
        steady_state = [
            [ENG, FLT, NTH],
            [GER, FLT, KIE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, HOL],
            [GER, AMY, RUH],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NTH), HLD])
        self.legalOrder(ENG, [(ENG, AMY, HOL), HLD])
        self.legalOrder(GER, [(GER, FLT, KIE), SUP, (GER, AMY, RUH), MTO, HOL])
        self.legalOrder(GER, [(GER, AMY, RUH), MTO, HOL])
        self.assertMapState(steady_state + [
            [ENG, AMY, HOL, MRT],
            [GER, AMY, HOL],
        ])
        self.legalOrder(ENG, [(ENG, AMY, HOL), RTO, BEL])
        self.illegalOrder(ENG, [(ENG, FLT, NTH), RTO, NWY])
        self.assertMapState(steady_state + [
            [ENG, AMY, BEL],
            [GER, AMY, HOL],
        ])
    def test_6H5(self):
        "6.H.5.  A UNIT MAY NOT RETREAT TO THE AREA FROM WHICH IT IS ATTACKED"
        steady_state = [
            [RUS, FLT, CON],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [TUR, FLT, ANK],
            [RUS, FLT, BLA],
        ])
        self.legalOrder(TUR, [(TUR, FLT, ANK), HLD])
        self.legalOrder(RUS, [(RUS, FLT, CON), SUP, (RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, FLT, BLA), MTO, ANK])
        self.assertMapState(steady_state + [
            [TUR, FLT, ANK, MRT],
            [RUS, FLT, ANK],
        ])
        self.illegalOrder(TUR, [(TUR, FLT, ANK), RTO, BLA])
        self.assertMapState(steady_state + [
            [RUS, FLT, ANK],
        ])
    def test_6H5_modified(self):
        "6.H.5.modified  A UNIT MAY NOT RETREAT TO AN OCCUPIED AREA"
        steady_state = [
            [RUS, FLT, CON],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [TUR, FLT, ANK],
            [RUS, FLT, BLA],
        ])
        self.legalOrder(TUR, [(TUR, FLT, ANK), HLD])
        self.legalOrder(RUS, [(RUS, FLT, CON), SUP, (RUS, FLT, BLA), MTO, ANK])
        self.legalOrder(RUS, [(RUS, FLT, BLA), MTO, ANK])
        self.assertMapState(steady_state + [
            [TUR, FLT, ANK, MRT],
            [RUS, FLT, ANK],
        ])
        self.illegalOrder(TUR, [(TUR, FLT, ANK), RTO, CON])
        self.assertMapState(steady_state + [
            [RUS, FLT, ANK],
        ])
    def test_6H6(self):
        "6.H.6.  UNIT MAY NOT RETREAT TO A CONTESTED AREA"
        steady_state = [
            [AUS, AMY, BUD],
            [GER, AMY, MUN],
            [GER, AMY, SIL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [AUS, AMY, TRI],
            [ITA, AMY, VIE],
        ])
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (AUS, AMY, TRI), MTO, VIE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VIE])
        self.legalOrder(GER, [(GER, AMY, MUN), MTO, BOH])
        self.legalOrder(GER, [(GER, AMY, SIL), MTO, BOH])
        self.legalOrder(ITA, [(ITA, AMY, VIE), HLD])
        self.assertMapState(steady_state + [
            [AUS, AMY, VIE],
            [ITA, AMY, VIE, MRT],
        ])
        self.illegalOrder(ITA, [(ITA, AMY, VIE), RTO, BOH])
        self.assertMapState(steady_state + [
            [AUS, AMY, VIE],
        ])
    def test_6H7(self):
        "6.H.7.  MULTIPLE RETREAT TO SAME AREA WILL DISBAND UNITS"
        steady_state = [
            [AUS, AMY, BUD],
            [GER, AMY, MUN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [AUS, AMY, TRI],
            [GER, AMY, SIL],
            [ITA, AMY, VIE],
            [ITA, AMY, BOH],
        ])
        self.legalOrder(AUS, [(AUS, AMY, BUD), SUP, (AUS, AMY, TRI), MTO, VIE])
        self.legalOrder(AUS, [(AUS, AMY, TRI), MTO, VIE])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (GER, AMY, SIL), MTO, BOH])
        self.legalOrder(GER, [(GER, AMY, SIL), MTO, BOH])
        self.legalOrder(ITA, [(ITA, AMY, VIE), HLD])
        self.legalOrder(ITA, [(ITA, AMY, BOH), HLD])
        self.assertMapState(steady_state + [
            [AUS, AMY, VIE],
            [GER, AMY, BOH],
            [ITA, AMY, VIE, MRT],
            [ITA, AMY, BOH, MRT],
        ])
        self.legalOrder(ITA, [(ITA, AMY, VIE), RTO, TYR])
        self.legalOrder(ITA, [(ITA, AMY, BOH), RTO, TYR])
        self.assertMapState(steady_state + [
            [AUS, AMY, VIE],
            [GER, AMY, BOH],
        ])
    def test_6H8(self):
        "6.H.8.  TRIPLE RETREAT TO SAME AREA WILL DISBAND UNITS"
        steady_state = [
            [ENG, FLT, YOR],
            [GER, AMY, KIE],
            [RUS, AMY, SWE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [ENG, FLT, NWY],
            [GER, AMY, RUH],
            [RUS, FLT, EDI],
            [RUS, AMY, FIN],
            [RUS, FLT, HOL],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), MTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, YOR), SUP, (ENG, AMY, LVP), MTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NWY), HLD])
        self.legalOrder(GER, [(GER, AMY, KIE), SUP, (GER, AMY, RUH), MTO, HOL])
        self.legalOrder(GER, [(GER, AMY, RUH), MTO, HOL])
        self.legalOrder(RUS, [(RUS, FLT, EDI), HLD])
        self.legalOrder(RUS, [(RUS, AMY, SWE), SUP, (RUS, AMY, FIN), MTO, NWY])
        self.legalOrder(RUS, [(RUS, AMY, FIN), MTO, NWY])
        self.legalOrder(RUS, [(RUS, FLT, HOL), HLD])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [ENG, FLT, NWY, MRT],
            [GER, AMY, HOL],
            [RUS, FLT, EDI, MRT],
            [RUS, AMY, NWY],
            [RUS, FLT, HOL, MRT],
        ])
        self.legalOrder(ENG, [(ENG, FLT, NWY), RTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, EDI), RTO, NTH])
        self.legalOrder(RUS, [(RUS, FLT, HOL), RTO, NTH])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [GER, AMY, HOL],
            [RUS, AMY, NWY],
        ])
    def test_6H9(self):
        "6.H.9.  DISLODGED UNIT WILL NOT MAKE ATTACKERS AREA CONTESTED"
        steady_state = [
            [ENG, FLT, DEN],
            [GER, AMY, SIL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, HEL],
            [GER, AMY, BER],
            [GER, FLT, KIE],
            [RUS, AMY, PRU],
        ])
        self.legalOrder(ENG, [(ENG, FLT, HEL), MTO, KIE])
        self.legalOrder(ENG, [(ENG, FLT, DEN), SUP, (ENG, FLT, HEL), MTO, KIE])
        self.legalOrder(GER, [(GER, AMY, BER), MTO, PRU])
        self.legalOrder(GER, [(GER, FLT, KIE), HLD])
        self.legalOrder(GER, [(GER, AMY, SIL), SUP, (GER, AMY, BER), MTO, PRU])
        self.legalOrder(RUS, [(RUS, AMY, PRU), MTO, BER])
        self.assertMapState(steady_state + [
            [ENG, FLT, KIE],
            [GER, AMY, PRU],
            [GER, FLT, KIE, MRT],
            [RUS, AMY, PRU, MRT],
        ])
        self.legalOrder(GER, [(GER, FLT, KIE), RTO, BER])
        self.illegalOrder(RUS, [(RUS, AMY, PRU), RTO, BER])
        self.assertMapState(steady_state + [
            [ENG, FLT, KIE],
            [GER, AMY, PRU],
            [GER, FLT, BER],
        ])
    def test_6H10(self):
        "6.H.10.  NOT RETREATING TO ATTACKER DOES NOT MEAN CONTESTED"
        steady_state = [
            [GER, AMY, MUN],
            [RUS, AMY, SIL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, KIE],
            [GER, AMY, BER],
            [GER, AMY, PRU],
            [RUS, AMY, WAR],
        ])
        self.legalOrder(ENG, [(ENG, AMY, KIE), HLD])
        self.legalOrder(GER, [(GER, AMY, BER), MTO, KIE])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (GER, AMY, BER), MTO, KIE])
        self.legalOrder(GER, [(GER, AMY, PRU), HLD])
        self.legalOrder(RUS, [(RUS, AMY, WAR), MTO, PRU])
        self.legalOrder(RUS, [(RUS, AMY, SIL), SUP, (RUS, AMY, WAR), MTO, PRU])
        self.assertMapState(steady_state + [
            [ENG, AMY, KIE, MRT],
            [GER, AMY, PRU, MRT],
            [GER, AMY, KIE],
            [RUS, AMY, PRU],
        ])
        self.legalOrder(GER, [(GER, AMY, PRU), RTO, BER])
        self.illegalOrder(ENG, [(ENG, AMY, KIE), RTO, BER])
        self.assertMapState(steady_state + [
            [GER, AMY, BER],
            [GER, AMY, KIE],
            [RUS, AMY, PRU],
        ])
    def test_6H11_blocked(self):
        "6.H.11.a  RETREAT WHEN DISLODGED BY ADJACENT CONVOY"
        # 4.A.3, 4.A.5
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [FRA, FLT, WES],
            [FRA, FLT, GOL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, GAS],
            [ITA, AMY, MAR],
        ])
        self.legalOrder(FRA, [(FRA, AMY, GAS), CTO, MAR, VIA, [MAO, WES, GOL]])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, GAS), MTO, MAR])
        self.legalOrder(FRA, [(FRA, FLT, MAO), CVY, (FRA, AMY, GAS), CTO, MAR])
        self.legalOrder(FRA, [(FRA, FLT, WES), CVY, (FRA, AMY, GAS), CTO, MAR])
        self.legalOrder(FRA, [(FRA, FLT, GOL), CVY, (FRA, AMY, GAS), CTO, MAR])
        self.legalOrder(ITA, [(ITA, AMY, MAR), HLD])
        self.assertMapState(steady_state + [
            [FRA, AMY, MAR],
            [ITA, AMY, MAR, MRT],
        ])
        self.illegalOrder(ITA, [(ITA, AMY, MAR), RTO, GAS])
        self.assertMapState(steady_state + [
            [FRA, AMY, MAR],
        ])
    @fails
    def test_6H11_retreat(self):
        "6.H.11.b  RETREAT WHEN DISLODGED BY ADJACENT CONVOY"
        # 4.A.3, 4.A.5
        steady_state = [
            [FRA, AMY, BUR],
            [FRA, FLT, MAO],
            [FRA, FLT, WES],
            [FRA, FLT, GOL],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, AMY, GAS],
            [ITA, AMY, MAR],
        ])
        self.legalOrder(FRA, [(FRA, AMY, GAS), CTO, MAR, VIA, [MAO, WES, GOL]])
        self.legalOrder(FRA, [(FRA, AMY, BUR), SUP, (FRA, AMY, GAS), MTO, MAR])
        self.legalOrder(FRA, [(FRA, FLT, MAO), CVY, (FRA, AMY, GAS), CTO, MAR])
        self.legalOrder(FRA, [(FRA, FLT, WES), CVY, (FRA, AMY, GAS), CTO, MAR])
        self.legalOrder(FRA, [(FRA, FLT, GOL), CVY, (FRA, AMY, GAS), CTO, MAR])
        self.legalOrder(ITA, [(ITA, AMY, MAR), HLD])
        self.assertMapState(steady_state + [
            [FRA, AMY, MAR],
            [ITA, AMY, MAR, MRT],
        ])
        self.legalOrder(ITA, [(ITA, AMY, MAR), RTO, GAS])
        self.assertMapState(steady_state + [
            [FRA, AMY, MAR],
            [ITA, AMY, GAS],
        ])
    def test_6H12_blocked(self):
        "6.H.12.a  RETREAT WHEN DISLODGED BY ADJACENT CONVOY WHILE TRYING TO DO THE SAME"
        # 4.A.3, 4.A.5
        steady_state = [
            [ENG, AMY, BUR],
            [ENG, FLT, IRI],
            [ENG, FLT, NTH],
            [FRA, FLT, MAO],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
            [RUS, AMY, CLY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [ENG, FLT, ECH],
            [FRA, FLT, BRE],
            [RUS, AMY, EDI],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, EDI, VIA, [IRI, ECH, NTH]])
        self.legalOrder(ENG, [(ENG, FLT, IRI), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, EDI), CTO, LVP, VIA, [NWG, NAO]])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, AMY, CLY), SUP, (RUS, AMY, EDI), MTO, LVP])
        self.assertMapState(steady_state + [
            [ENG, AMY, LVP, MRT],
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
        self.illegalOrder(ENG, [(ENG, AMY, LVP), RTO, EDI])
        self.assertMapState(steady_state + [
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
    @fails
    def test_6H12_retreat(self):
        "6.H.12.b  RETREAT WHEN DISLODGED BY ADJACENT CONVOY WHILE TRYING TO DO THE SAME"
        # 4.A.3, 4.A.5
        steady_state = [
            [ENG, AMY, BUR],
            [ENG, FLT, IRI],
            [ENG, FLT, NTH],
            [FRA, FLT, MAO],
            [RUS, FLT, NWG],
            [RUS, FLT, NAO],
            [RUS, AMY, CLY],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, LVP],
            [ENG, FLT, ECH],
            [FRA, FLT, BRE],
            [RUS, AMY, EDI],
        ])
        self.legalOrder(FRA, [(FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, BRE), MTO, ECH])
        self.legalOrder(ENG, [(ENG, AMY, LVP), CTO, EDI, VIA, [IRI, ECH, NTH]])
        self.legalOrder(ENG, [(ENG, FLT, IRI), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(ENG, [(ENG, FLT, NTH), CVY, (ENG, AMY, LVP), CTO, EDI])
        self.legalOrder(RUS, [(RUS, AMY, EDI), CTO, LVP, VIA, [NWG, NAO]])
        self.legalOrder(RUS, [(RUS, FLT, NWG), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, FLT, NAO), CVY, (RUS, AMY, EDI), CTO, LVP])
        self.legalOrder(RUS, [(RUS, AMY, CLY), SUP, (RUS, AMY, EDI), MTO, LVP])
        self.assertMapState(steady_state + [
            [ENG, AMY, LVP, MRT],
            [ENG, FLT, ECH, MRT],
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
        self.legalOrder(ENG, [(ENG, AMY, LVP), RTO, EDI])
        self.assertMapState(steady_state + [
            [ENG, AMY, EDI],
            [FRA, FLT, ECH],
            [RUS, AMY, LVP],
        ])
    def test_6H13(self):
        "6.H.13.  NO RETREAT WITH CONVOY IN MAIN PHASE"
        steady_state = [
            [ENG, FLT, ECH],
            [FRA, AMY, BRE],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, PIC],
            [FRA, AMY, PAR],
        ])
        self.legalOrder(ENG, [(ENG, AMY, PIC), HLD])
        self.legalOrder(ENG, [(ENG, FLT, ECH), CVY, (ENG, AMY, PIC), CTO, LON])
        self.legalOrder(FRA, [(FRA, AMY, PAR), MTO, PIC])
        self.legalOrder(FRA, [(FRA, AMY, BRE), SUP, (FRA, AMY, PAR), MTO, PIC])
        self.assertMapState(steady_state + [
            [ENG, AMY, PIC, MRT],
            [FRA, AMY, PIC],
        ])
        self.illegalOrder(ENG, [(ENG, AMY, PIC), RTO, LON])
        self.assertMapState(steady_state + [
            [FRA, AMY, PIC],
        ])
    def test_6H14(self):
        "6.H.14.  NO RETREAT WITH SUPPORT IN MAIN PHASE"
        steady_state = [
            [ENG, FLT, ECH],
            [FRA, AMY, BRE],
            [GER, AMY, MUN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, AMY, PIC],
            [FRA, AMY, PAR],
            [FRA, AMY, BUR],
            [GER, AMY, MAR],
        ])
        self.legalOrder(ENG, [(ENG, AMY, PIC), HLD])
        self.legalOrder(ENG, [(ENG, FLT, ECH), SUP, (ENG, AMY, PIC), MTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, PAR), MTO, PIC])
        self.legalOrder(FRA, [(FRA, AMY, BRE), SUP, (FRA, AMY, PAR), MTO, PIC])
        self.legalOrder(FRA, [(FRA, AMY, BUR), HLD])
        self.legalOrder(GER, [(GER, AMY, MAR), MTO, BUR])
        self.legalOrder(GER, [(GER, AMY, MUN), SUP, (GER, AMY, MAR), MTO, BUR])
        self.assertMapState(steady_state + [
            [ENG, AMY, PIC, MRT],
            [FRA, AMY, PIC],
            [FRA, AMY, BUR, MRT],
            [GER, AMY, BUR],
        ])
        self.legalOrder(ENG, [(ENG, AMY, PIC), RTO, BEL])
        self.legalOrder(FRA, [(FRA, AMY, BUR), RTO, BEL])
        self.assertMapState(steady_state + [
            [FRA, AMY, PIC],
            [GER, AMY, BUR],
        ])
    def test_6H15(self):
        "6.H.15.  NO COASTAL CRAWL IN RETREAT"
        steady_state = [
            [FRA, FLT, MAO],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [ENG, FLT, POR],
            [FRA, FLT, [SPA, SCS]],
        ])
        self.legalOrder(ENG, [(ENG, FLT, POR), HLD])
        self.legalOrder(FRA, [(FRA, FLT, [SPA, SCS]), MTO, POR])
        self.legalOrder(FRA, [(FRA, FLT, MAO), SUP, (FRA, FLT, [SPA, SCS]), MTO, POR])
        self.assertMapState(steady_state + [
            [ENG, FLT, POR, MRT],
            [FRA, FLT, POR],
        ])
        self.illegalOrder(ENG, [(ENG, FLT, POR), RTO, [SPA, NCS]])
        self.assertMapState(steady_state + [
            [FRA, FLT, POR],
        ])
    def test_6H16(self):
        "6.H.16.  CONTESTED FOR BOTH COASTS"
        steady_state = [
            [FRA, FLT, MAO],
            [FRA, FLT, GAS],
            [ITA, FLT, TUN],
        ]
        self.init_state(SPR, 1901, steady_state + [
            [FRA, FLT, WES],
            [ITA, FLT, TYS],
        ])
        self.legalOrder(FRA, [(FRA, FLT, MAO), MTO, [SPA, NCS]])
        self.legalOrder(FRA, [(FRA, FLT, GAS), MTO, [SPA, NCS]])
        self.legalOrder(FRA, [(FRA, FLT, WES), HLD])
        self.legalOrder(ITA, [(ITA, FLT, TUN), SUP, (ITA, FLT, TYS), MTO, WES])
        self.legalOrder(ITA, [(ITA, FLT, TYS), MTO, WES])
        self.assertMapState(steady_state + [
            [FRA, FLT, WES, MRT],
            [ITA, FLT, WES],
        ])
        self.illegalOrder(FRA, [(FRA, FLT, WES), RTO, [SPA, SCS]])
        self.assertMapState(steady_state + [
            [ITA, FLT, WES],
        ])

class DATC_6_I(DiplomacyAdjudicatorTestCase):
    "6.I.  BUILDING"
    def test_6I1(self):
        "6.I.1.  TOO MANY BUILD ORDERS"
        # 4.D.4
        steady_state = [
            [GER, AMY, PRU],
            [GER, AMY, RUH],
        ]
        self.init_state(WIN, 1901, steady_state)
        self.illegalOrder(GER, [(GER, AMY, WAR), BLD])
        self.legalOrder(GER, [(GER, AMY, KIE), BLD])
        self.illegalOrder(GER, [(GER, AMY, MUN), BLD])
        self.assertMapState(steady_state + [
            [GER, AMY, KIE],
        ])
    def test_6I2(self):
        "6.I.2.  FLEETS CAN NOT BE BUILD IN LAND AREAS"
        # 4.C.4
        steady_state = [
            [RUS, AMY, STP],
            [RUS, AMY, WAR],
            [RUS, AMY, SEV],
        ]
        self.init_state(WIN, 1901, steady_state)
        self.illegalOrder(RUS, [(RUS, FLT, MOS), BLD])
        self.assertMapState(steady_state)
    def test_6I3(self):
        "6.I.3.  SUPPLY CENTER MUST BE EMPTY FOR BUILDING"
        steady_state = [
            [GER, AMY, BER],
            [GER, AMY, RUH],
        ]
        self.init_state(WIN, 1901, steady_state)
        self.illegalOrder(GER, [(GER, AMY, BER), BLD])
        self.assertMapState(steady_state)
    def test_6I4(self):
        "6.I.4.  BOTH COASTS MUST BE EMPTY FOR BUILDING"
        steady_state = [
            [RUS, FLT, [STP, SCS]],
            [RUS, AMY, WAR],
            [RUS, AMY, SEV],
        ]
        self.init_state(WIN, 1901, steady_state)
        self.illegalOrder(RUS, [(RUS, FLT, [STP, NCS]), BLD])
        self.assertMapState(steady_state)
    def test_6I5(self):
        "6.I.5.  BUILDING IN HOME SUPPLY CENTER THAT IS NOT OWNED"
        steady_state = [
            [GER, AMY, MUN],
        ]
        self.chown_sc(RUS, [BER])
        self.init_state(WIN, 1901, steady_state)
        self.illegalOrder(GER, [(GER, AMY, BER), BLD])
        self.assertMapState(steady_state)
    def test_6I6(self):
        "6.I.6.  BUILDING IN OWNED SUPPLY CENTER THAT IS NOT A HOME SUPPLY CENTER"
        steady_state = [
            [GER, AMY, BER],
            [GER, AMY, KIE],
            [GER, AMY, MUN],
        ]
        self.chown_sc(GER, [WAR])
        self.init_state(WIN, 1901, steady_state)
        self.illegalOrder(GER, [(GER, AMY, WAR), BLD])
        self.assertMapState(steady_state)
    def test_6I7(self):
        "6.I.7.  ONLY ONE BUILD IN A HOME SUPPLY CENTER"
        steady_state = [
            [RUS, AMY, WAR],
            [RUS, AMY, SEV],
        ]
        self.init_state(WIN, 1901, steady_state)
        self.legalOrder(RUS, [(RUS, AMY, MOS), BLD])
        self.illegalOrder(RUS, [(RUS, AMY, MOS), BLD])
        self.assertMapState(steady_state + [
            [RUS, AMY, MOS],
        ])

class DATC_6_J(DiplomacyAdjudicatorTestCase):
    "6.J.  CIVIL DISORDER AND DISBANDS"
    def test_6J1(self):
        "6.J.1.  TOO MANY REMOVE ORDERS"
        # 4.D.6
        steady_state = [
            [FRA, AMY, PAR],
        ]
        self.chown_sc(UNO, [BRE, MAR])
        self.init_state(WIN, 1901, steady_state + [
            [FRA, AMY, PIC],
        ])
        self.illegalOrder(FRA, [(FRA, FLT, GOL), REM])
        self.legalOrder(FRA, [(FRA, AMY, PIC), REM])
        self.illegalOrder(FRA, [(FRA, AMY, PAR), REM])
        self.assertMapState(steady_state)
    def test_6J2(self):
        "6.J.2.  REMOVING THE SAME UNIT TWICE"
        steady_state = [
            [FRA, AMY, PIC],
        ]
        self.chown_sc(UNO, [BRE, MAR])
        self.init_state(WIN, 1901, steady_state + [
            [FRA, AMY, PAR],
            [FRA, AMY, GAL],
        ])
        self.legalOrder(FRA, [(FRA, AMY, PAR), REM])
        self.legalOrder(FRA, [(FRA, AMY, PAR), REM])
        self.assertMapState(steady_state)
    def test_6J3(self):
        "6.J.3.  CIVIL DISORDER TWO ARMIES WITH DIFFERENT DISTANCE"
        steady_state = [
            [RUS, AMY, LVN],
        ]
        self.chown_sc(UNO, [STP, MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, AMY, SWE],
        ])
        self.assertMapState(steady_state)
    def test_6J4(self):
        "6.J.4.  CIVIL DISORDER TWO ARMIES WITH EQUAL DISTANCE"
        steady_state = [
            [RUS, AMY, UKR],
        ]
        self.chown_sc(UNO, [STP, MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, AMY, LVN],
        ])
        self.assertMapState(steady_state)
    def test_6J5(self):
        "6.J.5  CIVIL DISORDER TWO FLEETS WITH DIFFERENT DISTANCE"
        steady_state = [
            [RUS, FLT, SKA],
        ]
        self.chown_sc(UNO, [STP, MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, FLT, BER],
        ])
        self.assertMapState(steady_state)
    @fails
    def test_6J6(self):
        "6.J.6.  CIVIL DISORDER TWO FLEETS WITH EQUAL DISTANCE"
        steady_state = [
            [RUS, FLT, HEL],
        ]
        self.chown_sc(UNO, [STP, MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, FLT, BER],
        ])
        self.assertMapState(steady_state)
    def test_6J7(self):
        "6.J.7.  CIVIL DISORDER TWO FLEETS AND ARMY WITH EQUAL DISTANCE"
        steady_state = [
            [RUS, AMY, BOH],
            [RUS, FLT, SKA],
        ]
        self.chown_sc(UNO, [MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, FLT, NTH],
        ])
        self.assertMapState(steady_state)
    def test_6J8(self):
        "6.J.8.  CIVIL DISORDER A FLEET WITH SHORTER DISTANCE THEN THE ARMY"
        steady_state = [
            [RUS, FLT, BAL],
        ]
        self.chown_sc(UNO, [STP, MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, AMY, TYR],
        ])
        self.assertMapState(steady_state)
    def test_6J9(self):
        "6.J.9.  CIVIL DISORDER MUST BE COUNTED FROM BOTH COASTS"
        steady_state = [
            [RUS, FLT, SKA],
        ]
        self.chown_sc(UNO, [STP, MOS, SEV])
        self.init_state(WIN, 1901, steady_state + [
            [RUS, AMY, TYR],
        ])
        self.assertMapState(steady_state)
    def test_6J10(self):
        "6.J.10.  CIVIL DISORDER COUNTING CONVOYING DISTANCE"
        # 4.D.8
        steady_state = [
            [ITA, FLT, ION],
            [ITA, AMY, GRE],
        ]
        self.chown_sc(UNO, [ROM])
        self.init_state(WIN, 1901, steady_state + [
            [ITA, AMY, SIL],
        ])
        self.assertMapState(steady_state)
    def test_6J11(self):
        "6.J.11.  CIVIL DISORDER COUNTING DISTANCE WITHOUT CONVOYING FLEET"
        # 4.D.8
        steady_state = [
            [ITA, AMY, GRE],
        ]
        self.chown_sc(UNO, [ROM, NAP])
        self.init_state(WIN, 1901, steady_state + [
            [ITA, AMY, SIL],
        ])
        self.assertMapState(steady_state)

if __name__ == '__main__': unittest.main()
