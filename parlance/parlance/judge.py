r'''Parlance adjudication system
    Copyright (C) 2004-2008  Eric Wald
    
    This module implements a decision-making judge for the standard Diplomacy
    rules.  Several of the disputable rules ambiguities are configurable.
    This Judge should work for most map variants, but rule variants may need
    to re-implement it.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

from itertools import chain

from config import Configuration, VerboseObject
from functions import Infinity, all, any, defaultdict, s
from gameboard import Map
from orders import DisbandOrder, HoldOrder, OrderSet, \
        RemoveOrder, WaiveOrder, createUnitOrder
from tokens import *


class DatcOptions(Configuration):
    ''' Options from the Diplomacy Adjudicator Test Cases,
        as written by Lucas B. Kruijswijk.
        A few options have additional possibilities, and some are unsupported.
    '''#'''
    class datc(object):
        ''' Parser for a single DATC option.'''
        __name__ = 'character'
        def __init__(self, possible, supported):
            self.possible = possible
            self.supported = supported
        def __call__(self, value):
            if len(value) != 1:
                raise ValueError('Exactly one character expected')
            elif value not in self.possible:
                raise ValueError('Unknown selection')
            elif value not in self.supported:
                raise ValueError('Unsupported selection')
            return value
    
    __section__ = 'datc'
    __options__ = (
        # Convoy issues
        ('datc_4a1', datc('abc', 'ab'), 'b',
            'multi-route convoy disruption',
            '4.A.1.  MULTI-ROUTE CONVOY DISRUPTION',
            'a: A convoy is disrupted when any possible route is disrupted.',
            'b: A convoy is disrupted when all possible routes are disrupted.',
            'c: Multi-route convoys are not allowed.',
            'DATC: b; DPTG: a; DAIDE: c'),
        ('datc_4a2', datc('abcdef', 'bdef'), 'd',
            'convoy disruption paradoxes',
            '4.A.2.  CONVOY DISRUPTION PARADOXES',
            "a: Convoyed armies don't cut support to fleets attacking its convoy fleet.",
            "b: Convoyed armies don't cut support to or against any convoying fleet.",
            "c: Convoyed armies don't cut support to fleets necessary for the convoy.",
            "d: Convoyed armies in a paradoxical situation don't move.",
            'e: All moves in a paradoxical situation fail.',
            'f: All convoys fail if consistent; otherwise, all moves fail.',
            'DATC: d; DPTG: f; DAIDE: f'),
        ('datc_4a3', datc('abcdef', 'abcdef'), 'd',
            'convoying to adjacent place',
            '4.A.3.  CONVOYING TO ADJACENT PLACE',
            'a: Always choose the convoy route.',
            'b: Choose the land route except in head-to-head situations.',
            'c: Choose the land route except in head-to-head with undisrupted route.',
            "d: Determine the intent from the player's order set.",
            'e: Use the land route unless specifically ordered to be convoyed.',
            'f: Never convoy unless specifically ordered.',
            'DATC: d(c); DPTG: e; DAIDE: f'),
        ('datc_4a4', datc('ab', 'a'), 'a', # Todo: b
            'support cut on attack on itself via convoy',
            '4.A.4.  SUPPORT CUT ON ATTACK ON ITSELF VIA CONVOY',
            'a: Support is not cut.',
            'b: Support is cut.',
            'DATC: a; DPTG: b; DAIDE: b'),
        ('datc_4a5', datc('ab', 'a'), 'b', # Todo: b
            'retreat when dislodged by convoy',
            '4.A.5.  RETREAT WHEN DISLODGED BY CONVOY',
            'a: Dislodged units may not retreat to the starting place of any attacker.',
            'b: Dislodged units may retreat to the starting place of a convoyed attacker.',
            'DATC: b; DPTG: b; DAIDE: a'),
        ('datc_4a6', datc('abc', 'abc'), 'b',
            'convoy path specification',
            '4.A.6.  CONVOY PATH SPECIFICATION',
            'a: Path specifications are ignored.',
            'b: Path specifications are allowed, but not required.',
            'c: Path specifications are required.',
            'DATC: a(b); DPTG: a; DAIDE: c'),
        ('datc_4a7', datc('ab', 'b'), 'b', # Todo: a
            'avoiding a head to head battle to bounce a unit',
            '4.A.7.  AVOIDING A HEAD TO HEAD BATTLE TO BOUNCE A UNIT',
            "a: Dislodged units never have effect on attacker's space.",
            "b: Dislodged units have no effect on attacker's space in head-to-head combat.",
            'DATC: b; DPTG: b; DAIDE: b'),
        
        # Coastal issues
        ('datc_4b1', datc('ab', 'a'), 'a',
            'omitted coast specification in move order when two coasts are possible',
            '4.B.1.  OMITTED COAST SPECIFICATION IN MOVE ORDER WHEN TWO COASTS ARE POSSIBLE',
            'a: Such a move fails.',
            'b: A move is attempted to a default coast.',
            'DATC: a; DPTG: a; DAIDE: a'),
        ('datc_4b2', datc('abc', 'ac'), 'a',
            'omitted coast specification in move order when one coast is possible',
            '4.B.2.  OMITTED COAST SPECIFICATION IN MOVE ORDER WHEN ONE COAST IS POSSIBLE',
            'a: A move is attempted to the only possible coast.',
            'b: A move is attempted to a default coast.',
            'c: The move fails.',
            'DATC: a; DPTG: a; DAIDE: c'),
        ('datc_4b3', datc('ab', 'ab'), 'b',
            'move order to impossible coast',
            '4.B.3.  MOVE ORDER TO IMPOSSIBLE COAST',
            'a: A move is attempted to the only possible coast.',
            'b: The move fails.',
            'DATC: b; DPTG: ?; DAIDE: b'),
        ('datc_4b4', datc('abcde', 'acde'), 'd',
            'coast specification in support order',
            '4.B.4.  COAST SPECIFICATION IN SUPPORT ORDER',
            'a: Missing coast in a support order fails.',
            'b: Missing coast in a support order goes to a default coast.',
            'c: Missing coast in a support order fails unless unambiguous.',
            'd: Support to a specific coast is allowed, but not required.',
            'e: Support to a specific coast is not allowed.',
            'DATC: d; DPTG: e; DAIDE: e'),
        ('datc_4b5', datc('ab', 'ab'), 'a',
            'wrong coast of ordered unit',
            '4.B.5.  WRONG COAST OF ORDERED UNIT',
            'a: The move fails.',
            'b: Coast specification is ignored.',
            'DATC: b; DPTG: ?; DAIDE: a'),
        ('datc_4b6', datc('ab', 'ab'), 'b',
            'unknown coasts or irrelevant coasts',
            '4.B.6.  UNKNOWN COASTS OR IRRELEVANT COASTS',
            'a: The move fails.',
            'b: Coast specification is ignored.',
            'DATC: b; DPTG: ?; DAIDE: a'),
        ('datc_4b7', datc('ab', 'a'), 'a',
            'coast specification in build order',
            '4.B.7.  COAST SPECIFICATION IN BUILD ORDER',
            'a: A fleet build fails if it does not specify a coast when necessary.',
            'b: The fleet is built on a default coast.',
            'DATC: a; DPTG: ?; DAIDE: a'),
        
        # Unit designation and nationality issues
        ('datc_4c1', datc('abc', 'b'), 'b', # Todo: a
            'missing unit designation',
            '4.C.1.  MISSING UNIT DESIGNATION',
            'a: The order is invalid.',
            'b: The order is valid.',
            'c: The order is valid unless a correct order exists.',
            'DATC: b; DPTG: ?; DAIDE: a'),
        ('datc_4c2', datc('abc', 'a'), 'a', # Todo: b
            'wrong unit designation',
            '4.C.2.  WRONG UNIT DESIGNATION',
            'a: The order is invalid.',
            'b: The order is valid.',
            'c: The order is valid unless a correct order exists.',
            'DATC: b; DPTG: ?; DAIDE: a'),
        ('datc_4c3', datc('abc', 'b'), 'b', # Todo: ac
            'missing unit designation in build order',
            '4.C.3.  MISSING UNIT DESIGNATION IN BUILD ORDER',
            'a: The build always fails.',
            'b: The build fails in coastal areas, but succeeds when unambiguous.',
            'c: Armies are built inland, fleets when a specific coast is specified.',
            'DATC: c; DPTG: ?; DAIDE: a'),
        ('datc_4c4', datc('ab', 'a'), 'a', # Todo: b
            'building a fleet in a land area',
            '4.C.4.  BUILDING A FLEET IN A LAND AREA',
            'a: The build always fails.',
            'b: An army is built instead.',
            'DATC: a; DPTG: ?; DAIDE: a'),
        ('datc_4c5', datc('abc', 'b'), 'b', # Todo: a
            'missing nationality in support order',
            '4.C.5.  MISSING NATIONALITY IN SUPPORT ORDER',
            'a: The order is invalid.',
            'b: The order is valid.',
            'c: The order is valid unless another order uses the correct nationality.',
            'DATC: b; DPTG: ?; DAIDE: a'),
        ('datc_4c6', datc('abc', 'a'), 'a', # Todo: b
            'wrong nationality in support order',
            '4.C.6.  WRONG NATIONALITY IN SUPPORT ORDER',
            'a: The order is invalid.',
            'b: The order is valid.',
            'c: The order is valid unless another order uses the correct nationality.',
            'DATC: b; DPTG: ?; DAIDE: a'),
        
        # Too many and too few orders
        ('datc_4d1', datc('abcd', 'b'), 'b',
            'multiple order sets with defined order',
            '4.D.1.  MULTIPLE ORDER SETS WITH DEFINED ORDER',
            'a: All order sets are combined to one set of orders.',
            'b: All order sets are combined, unless latest clearly replaces all earlier.',
            'c: Only the latest order set is considered, unless otherwise specified.',
            'd: Only the latest order set is considered.',
            'DATC: c; DPTG: ?; DAIDE: b'),
        ('datc_4d2', datc('abc', 'c'), 'c',
            'multiple order sets with undefined order',
            '4.D.2.  MULTIPLE ORDER SETS WITH UNDEFINED ORDER',
            'a: All units hold.',
            'b: All order sets are combined.',
            'c: Order sets must have a defined order.',
            'DATC: b; DPTG: ?; DAIDE: c'),
        ('datc_4d3', datc('abc', 'b'), 'b',
            'multiple orders to the same unit',
            '4.D.3.  MULTIPLE ORDERS TO THE SAME UNIT',
            'a: The first order in a set is used.',
            'b: The last order in a set is used.',
            'c: The orders are illegal (the unit holds).',
            'DATC: c; DPTG: ?; DAIDE: b'),
        ('datc_4d4', datc('abc', 'b'), 'b',
            'too many build orders',
            '4.D.4.  TOO MANY BUILD ORDERS',
            'a: All build orders are invalid.',
            'b: The first legal build orders are used.',
            'c: The last legal build orders are used.',
            'DATC: b; DPTG: ?; DAIDE: b'),
        ('datc_4d5', datc('abc', 'c'), 'c',
            'multiple build orders for one area',
            '4.D.5.  MULTIPLE BUILD ORDERS FOR ONE AREA',
            'a: Both build orders fail.',
            'b: The first build order is used.',
            'c: The last build order is used.',
            'DATC: b; DPTG: ?; DAIDE: c'),
        ('datc_4d6', datc('abc', 'b'), 'b',
            'too many disband orders',
            '4.D.6.  TOO MANY DISBAND ORDERS',
            'a: All disbands are handled by civil disorder rules.',
            'b: The first legal disband orders are used.',
            'c: The last legal disband orders are used.',
            'DATC: b; DPTG: ?; DAIDE: b'),
        ('datc_4d7', datc('ab', 'a'), 'a', # Todo: b
            'waiving builds',
            '4.D.7.  WAIVING BUILDS',
            'a: Waiving builds is allowed.',
            'b: Waiving builds is not allowed.',
            'DATC: a; DPTG: ?; DAIDE: a'),
        ('datc_4d8', datc('abcdef', 'e'), 'e', # Todo: abcd
            'removing a unit in civil disorder',
            '4.D.8.  REMOVING A UNIT IN CIVIL DISORDER',
            'a: Convoys count as one move; no fleet necessary.',
            'b: Convoys count as one move, but require fleets of the same nation.',
            'c: Convoys count as one move, but require fleets of any nation.',
            'd: Armies may move as a fleet.',
            'e: Armies may move as a fleet, and fleets may move as an army.',
            'f: The oldest unit not at a supply center is removed.',
            'DATC: d; DPTG: d; DAIDE: ?'),
        ('datc_4d9', datc('ab', 'b'), 'b', # Todo: a?
            'receiving hold support in civil disorder',
            '4.D.9.  RECEIVING HOLD SUPPORT IN CIVIL DISORDER',
            'a: Units in civil disorder cannot receive support.',
            'b: Units in civil disorder can receive support.',
            'DATC: b; DPTG: ?; DAIDE: ?'),
        
        # Miscellaneous issues
        ('datc_4e1', datc('abcd', 'abcd'), 'd',
            'illegal orders',
            '4.E.1.  ILLEGAL ORDERS',
            'a: Every order with the right format is legal.',
            'b: Legal orders may only use places on the map.',
            'c: Only orders that can be valid in a game situation are legal.',
            'd: Only orders that can be valid in the current game situation are legal.',
            'DATC: d; DPTG: a; DAIDE: d'),
        ('datc_4e2', datc('abcde', 'e'), 'e',
            'poorly written orders',
            '4.E.2.  POORLY WRITTEN ORDERS',
            'a: No knowledge of Diplomacy must be used to correct orders.',
            'b: Each order may be corrected to make it legal.',
            'c: Other orders in the set may be considered when correcting an order.',
            'd: Orders may be corrected to match other orders within the set.',
            'e: Orders may not be corrected.',
            'DATC: d; DPTG: ?; DAIDE: e'),
        ('datc_4e3', datc('ab', 'b'), 'b', # Todo: a
            'implicit orders',
            '4.E.3.  IMPLICIT ORDERS',
            'a: Implicit orders are allowed.',
            'b: Implicit orders are not allowed.',
            'DATC: b; DPTG: ?; DAIDE: b'),
        ('datc_4e4', datc('ab', 'ab'), 'b',
            'perpetual orders',
            '4.E.4.  PERPETUAL ORDERS',
            'a: Perpetual orders are allowed.',
            'b: Perpetual orders are not allowed.',
            'DATC: b; DPTG: ?; DAIDE: b'),
        ('datc_4e5', datc('abc', 'abc'), 'c', # Todo: ab
            'proxy orders',
            '4.E.5.  PROXY ORDERS',
            'a: Proxy orders are allowed, with prior notification to the judge.',
            'b: Proxy orders are allowed as part of the normal order set.',
            'c: Proxy orders are not allowed.',
            'DATC: c; DPTG: ?; DAIDE: c'),
        ('datc_4e6', datc('ab', 'b'), 'b',
            'flying dutchman',
            '4.E.6.  FLYING DUTCHMAN',
            'a: Allowed, as long as it is a deception.',
            'b: Checked only on build phases.',
            'DATC: a; DPTG: ?; DAIDE: ?'),
    )


class JudgeInterface(VerboseObject):
    ''' The Arbitrator of Justice and Keeper of the Official Map.
        This class has the minimum skeleton required by the Server.
        
        Flags for the server:
            - unready:  True until each power has a set of valid orders.
            - phase:    Indicates the phase of the current turn.
            - game_result: The message indicating how the game ended, if it has.
        
        phase will be a Turn.phase() result for a game in progress,
        None for games ended or not yet started.
    '''#'''
    
    def __init__(self, variant, game_opts):
        ''' Initializes instance variables.'''
        self.__super.__init__()
        self.map = Map(variant)
        assert self.map.valid
        self.mdf = variant.mdf()
        self.map_name = variant.mapname
        self.variant_name = variant.name
        self.game_opts = game_opts
        self.game_result = None
        self.unready = True
        self.phase = None
    def reset(self):
        ''' Prepares the judge to begin a fresh game with the same map.
        '''#'''
        self.unready = True
        self.phase = None
        self.map.restart()
    def start(self):
        ''' Starts the game, returning NOW and SCO messages.'''
        raise NotImplementedError
    def run(self):
        ''' Process orders, whether or not the powers are all ready.
            Returns applicable ORD, NOW, and SCO messages.
            At the end of the game, returns SLO/DRW and SMY messages.
        '''#'''
        raise NotImplementedError
    
    # Interaction with players
    def handle_MAP(self, client, message): client.send(MAP(self.map_name))
    def handle_VAR(self, client, message): client.send(VAR(self.variant_name))
    def handle_MDF(self, client, message): client.send(self.mdf)
    def handle_NOW(self, client, message): raise NotImplementedError
    def handle_SCO(self, client, message): raise NotImplementedError
    def handle_ORD(self, client, message): raise NotImplementedError
    def handle_SUB(self, client, message): raise NotImplementedError
    def handle_DRW(self, client, message): raise NotImplementedError
    def handle_MIS(self, client, message): raise NotImplementedError
    def handle_NOT_SUB(self, client, message): raise NotImplementedError
    def handle_NOT_DRW(self, client, message): raise NotImplementedError
    
    # Law of Demeter
    def missing_orders(self, country): raise NotImplementedError
    def players(self): return self.map.powers.keys()
    def player_name(self, country): return self.map.powers[country].name
    def score(self, player): return len(self.map.powers[player].centers)
    def turn(self): return self.map.current_turn
    def eliminated(self, country=None):
        ''' Returns the year the power was eliminated,
            or False if it is still in the game.
            Without a country, returns a list of eliminated countries.
        '''#'''
        raise NotImplementedError

class Judge(JudgeInterface):
    ''' Implementation of the Judge interface, for DAIDE rules.'''
    __options__ = (
        # Premature draw conditions
        ('draw', int, 4000, 'total years before setting draw',
            'Maximum length of a game, in game years.',
            'Games exceeding this length will be declared DIAS draws.',
            'Values greater than 8191 might disable this, but could cause other problems.'),
        ('static', int, 1000, 'static years before setting draw',
            'Maximum number of years in which supply center counts do not change.',
            'Comparable to the 50-move rule in FIDE chess.',
            'After this many game years, the game will be declared a DIAS draw.',
            'Note that supply centers changing hands is not enough;',
            'at least one power must have a different total supply center count.',
            'Setting this higher than "total years before setting draw" will disable it.'),
        
        # Parameters for David Norman's Variable-Length mix-in rule.
        ('var_start', int, 5000, 'years before variable end',
            "Parameter for David Norman's Variable-Length mix-in rule,",
            'documented at http://www.diplom.org/Zine/S1998R/Norman/VarLength.html',
            'After this many years, the winning condition will start to decrease.',
            "For David's suggested conditions, use 3 here."),
        ('var_length', int, 0, 'length of variable end',
            "Parameter for David Norman's Variable-Length mix-in rule.",
            'This many years after starting to decrease the winning condition,',
            'it will stop decreasing and remain at its new low value.',
            "For David's suggested conditions, use 9 here.",
            'Setting this to 0 will disable the rule entirely.'),
        ('variation', float, 1.55, 'variation of variable end',
            "Parameter for David Norman's Variable-Length mix-in rule.",
            'The number of centers by which to decrease the winning condition per year.',
            "For David's suggested conditions, use 1.55 here.",
            'Setting this to 0 will disable the rule entirely.'),
        
        # DAIDE compliance settings
        ('full_DRW', bool, False, 'list draw parties in DIAS',
            'Whether to list the countries participating in a draw even in non-PDA games.',
            'Doing so technically violates the syntax, but makes some clients easier.'),
        ('send_SET', bool, False, 'publish order sets',
            'Whether to send SET messages, listing orders actually given by each power.',
            'This message was rejected by the DAIDE community, after it was implemented.',
            'Advantage over ORD messages: It can represent *any* order,',
            'even those to non-existent or foreign units.',
            "Disadvantage: Doesn't list results, and may be large."),
        ('send_ORD', bool, True, 'publish individual orders',
            'Whether to send ORD messages each turn, as required by DAIDE.',
            'Can slow down the game, particularly when syntax-checked by each client.'),
    )
    
    def __init__(self, variant, game_opts):
        ''' Initializes instance variables.'''
        self.__super.__init__(variant, game_opts)
        self.datc = DatcOptions()
        self.last_orders = [REJ(ORD)]
        self.next_orders = OrderSet()
        
        # Game-end conditions
        year = self.map.current_turn.year
        self.var_start  = year + self.options.var_start
        self.var_stop   = self.var_start + self.options.var_length
        self.draw_year  = year + self.options.draw - 1
        self.max_static = self.options.static
        
        centers = 0
        for prov in self.map.spaces.itervalues():
            if prov.is_supply(): centers += 1
        self.win_condition = (centers // 2) + 1
        self.log_debug(11, 'Setting win_condition to %d.', self.win_condition)
    
    # Requests for information
    def handle_NOW(self, client, message): client.send(self.map.create_NOW())
    def handle_SCO(self, client, message): client.send(self.map.create_SCO())
    def handle_ORD(self, client, message): client.send_list(self.last_orders)
    
    # Order submission
    def handle_SUB(self, client, message):
        ''' Processes orders submitted by a power.'''
        country = client.country
        phase = self.phase  # Needed to avoid thread problems
        if country and phase:
            orders = self.next_orders
            for tlist in message.fold()[1:]:
                power = self.map.powers[country]
                order = createUnitOrder(tlist, power, self.map, self.datc)
                note = order.order_note(power, phase, orders)
                self.log_debug(14, ' SUB: %s => %s', order, note)
                order.__note = note
                if note == MBV:
                    order.__result = None
                    orders.add(order, country)
                elif self.game_opts.AOA:
                    if order.is_moving() and self.illegal(order):
                        # Make it act like it's holding
                        self.log_debug(13, ' Changing behavior of "%s" (%s) to hold', order, order.__note)
                        order.is_moving = lambda: False
                    order.__result = note
                    orders.add(order, country)
                    note = MBV
                client.send(THX(order)(note))
            missing = self.missing_orders(country)
            if missing: client.send(missing)
            else: self.unready.discard(country)
        else: client.reject(message)
    def handle_NOT_SUB(self, client, message):
        ''' Cancels orders submitted by a power.'''
        country = client.country
        if country and self.phase and not self.eliminated(country):
            orders = self.next_orders
            if len(message) > 4:
                # Attempt to remove a specific order
                order = createUnitOrder(message.fold()[1][1],
                        country, self.map, self.datc)
                if not orders.remove(order, country):
                    client.reject(message)
                    return
            else: orders.clear(country)
            self.unready.add(country)
            client.accept(message)
        else: client.reject(message)
    def handle_DRW(self, client, message):
        ''' Processes draw requests submitted by a power.'''
        country = client.country
        self.log_debug(11, 'Considering %s from %s', message, country)
        if country and self.phase and not self.eliminated(country):
            winners = self.get_draw_parties(message)
            self.log_debug(11, ' Using %s as the winners', winners)
            if winners:
                self.draws.setdefault(winners, set()).add(country)
                client.accept(message)
            else: client.reject(message)
        else: client.reject(message)
    def handle_NOT_DRW(self, client, message):
        ''' Cancels draw requests submitted by a power.'''
        country = client.country
        if country and self.phase and not self.eliminated(country):
            try: self.draws[self.get_draw_parties(message[2:-1])].remove(country)
            except KeyError: client.reject(message)
            else: client.accept(message)
        else: client.reject(message)
    def handle_MIS(self, client, message):
        ''' Tells a power which or how many orders have yet to be submitted.'''
        country = client.country
        if country and self.phase and not self.eliminated(country):
            missing = self.missing_orders(country)
            if missing: client.send(missing)
            else: client.send(+MIS)
        else: client.reject(message)
    
    # Support functions for the above
    def missing_orders(self, country):
        self.log_debug(14, 'Finding missing orders for %s from %s', country, self.next_orders)
        return self.next_orders.missing_orders(self.phase, self.map.powers[country])
    def get_draw_parties(self, message):
        if len(message) == 1: return frozenset(self.map.current_powers())
        elif self.game_opts.PDA:
            winners = message[2:-1]
            if any(self.eliminated(country) for country in winners):
                self.log_debug(11, 'Somebody among %s has been eliminated', winners)
                return None
            else: return frozenset(winners)
        else:
            self.log_debug(11, 'List of winners not allowed in non-PDA game')
            return None
    def eliminated(self, country=None):
        ''' Returns the year the power was eliminated,
            or False if it is still in the game.
            Without a country, returns a list of eliminated countries.
        '''#'''
        if country:
            return self.map.powers[country].eliminated
        else:
            return [country for country,power in self.map.powers.iteritems()
                    if power.eliminated]
    
    # Turn processing
    def start(self):
        ''' Starts the game, returning SCO and NOW messages.'''
        self.unready = set()
        self.static = 0
        self.init_turn()
        return [self.map.create_SCO(), self.map.create_NOW()]
    def run(self):
        ''' Process orders, whether or not the powers are all ready.
            Returns applicable ORD, NOW, and SCO messages.
            At the end of the game, returns SLO/DRW and SMY messages.
        '''#'''
        msg = self.check_draw()
        if msg:
            results = [msg]
            self.game_result = msg
            self.phase = None
        else:
            # Report civil disorders
            turn = self.map.current_turn
            results = [CCD(country)(turn) for country in self.unready]
            
            # Report submitted orders
            if self.options.send_SET:
                results.extend(self.create_SETs(turn))
            
            # Execute and report orders
            if self.phase == turn.move_phase:
                orders = self.move_algorithm()
                self.last_orders = orders
            elif self.phase == turn.retreat_phase:
                orders = self.retreat_algorithm()
                self.last_orders.extend(orders)
            elif self.phase == turn.build_phase:
                orders = self.build_algorithm()
                self.last_orders.extend(orders)
            if self.options.send_ORD: results.extend(orders)
            
            # Skip to the next phase that requires action
            while True:
                # TODO: Store orders, SCO, and NOW in self.history
                turn = self.map.advance()
                self.phase = turn.phase()
                if self.phase == turn.build_phase:
                    growing = self.map.adjust_ownership()
                    results.append(self.map.create_SCO())
                    msg = self.check_solo(growing)
                if msg:
                    # End the game
                    self.game_result = msg
                    results.append(msg)
                    results.append(self.map.create_NOW())
                    self.phase = None
                    break
                else:
                    self.init_turn()
                    if self.unready:
                        results.append(self.map.create_NOW())
                        break
        return results
    def create_SETs(self, turn):
        return [SET(nation)(turn) % [([order], [order.__note])
                for order in self.next_orders.order_list(nation)]
                for nation in self.map.powers.values()
                if not nation.eliminated]
    def init_turn(self):
        self.draws = {}
        self.unready.clear()
        self.next_orders.clear()
        self.phase = self.map.current_turn.phase()
        self.unready.update([country for country in self.map.powers
                if self.missing_orders(country)])
    def check_draw(self):
        ''' Checks for the end of the game by agreed draw.
            Note that in a PDA game, if more than one combination
            has everybody's vote, the result is arbitrary.
        '''#'''
        in_game = set(self.map.current_powers())
        for winners, voters in self.draws.iteritems():
            if voters >= in_game:
                if self.game_opts.PDA: return DRW(winners)
                elif self.options.full_DRW: return DRW(in_game)
                else: return +DRW
        return None
    def check_solo(self, growing):
        ''' Checks for the end of the game by a solo win.
            Also handles draws by ending year.
        '''#'''
        if growing:
            max_seen = 0
            country = None
            for token, power in self.map.powers.iteritems():
                strength = len(power.centers)
                if strength == max_seen: country = None
                elif strength > max_seen: max_seen = strength; country = token
            self.log_debug(11, 'Checking solo, with (%s, %s, %d, %d).',
                    country, growing, max_seen, self.win_condition)
            if country in growing and max_seen >= self.win_condition:
                return SLO(country)
            self.static = 0
        else: self.static += 1
        
        year = self.map.current_turn.year
        self.log_debug(11, 'Now in %s, with %d static year%s.',
                year, self.static, s(self.static))
        if year >= self.draw_year or self.static >= self.max_static:
            return +DRW
        elif self.var_start <= year < self.var_stop:
            self.win_condition -= self.options.variation
        return None
    
    def build_algorithm(self):
        ''' The main adjudication routine for adjustment phases.
            Returns a list of ORD messages.
        '''#'''
        orders = []
        turn = self.map.current_turn
        for power in self.map.powers.itervalues():
            surplus = power.surplus()
            for order in self.next_orders.order_list(power):
                # Double-check, because previous orders can affect validity.
                result = order.order_note(power, self.phase)
                if result == MBV:
                    if order.order_type == BLD:
                        self.log_debug(11, 'Building %s', order.unit)
                        order.unit.build()
                        surplus += 1
                        result = SUC
                    elif order.order_type == WVE:
                        self.log_debug(11, 'Waiving for %s', power)
                        surplus += 1
                        result = SUC
                    elif order.order_type == REM:
                        self.log_debug(11, 'Removing %s', order.unit)
                        order.unit.die()
                        surplus -= 1
                        result = SUC
                    else:
                        self.log_debug(7, 'Unknown order type %s in build phase', order.order_type)
                        result = FLD
                orders.append(ORD(turn)(order)(result))
            
            # Handle missing orders
            if surplus > 0:
                units = power.farthest_units(self.map.distance)
                while surplus > 0:
                    unit = units.pop(0)
                    self.log_debug(8, 'Removing %s on behalf of %s', unit, power)
                    orders.append(ORD(turn)(RemoveOrder(unit))(SUC))
                    unit.die()
                    surplus -= 1
            while surplus < 0:
                self.log_debug(8, 'Waiving on behalf of %s', power)
                orders.append(ORD(turn)(WaiveOrder(power))(SUC))
                surplus += 1
        return orders
    def retreat_algorithm(self):
        ''' The main adjudication routine for retreat phases.
            Returns a list of ORD messages.
        '''#'''
        orders = []
        removed = []
        destinations = defaultdict(list)
        turn = self.map.current_turn
        for unit in self.map.units:
            if unit.dislodged:
                order = self.unit_order(unit, DisbandOrder)
                if order.order_type == DSB:
                    # Can't delete units while iterating over them
                    removed.append(order.unit)
                    result = SUC
                elif order.order_type == RTO:
                    destinations[order.destination.province.key].append(order)
                    result = None
                else: result = FLD   # Unrecognized order, but correct season
                if result: orders.append(ORD(turn)(order)(result))
        for unit in removed: unit.die()
        for unit_list in destinations.itervalues():
            if len(unit_list) == 1:
                # Successful retreat
                order = unit_list[0]
                orders.append(ORD(turn)(order)(SUC))
                order.unit.move_to(order.destination)
            else:
                # Bouncing
                for order in unit_list:
                    orders.append(ORD(turn)(order)(BNC))
                    order.unit.die()
        return orders
    def move_algorithm(self):
        ''' The main adjudication routine for movement phases.
            Returns a list of ORD messages.
        '''#'''
        # 0) Initialize arrays
        decisions = Decision_Set()
        convoyers = {}
        for province in self.map.spaces.itervalues(): province.entering = []
        
        # 1) Run through the units, collecting orders and checking validity.
        # Each unit gets a Dislodge decision.
        # Each moving unit gets Move, Attack, and Prevent decisions.
        # Each valid supporting unit gets a Support decision.
        # Each province moved into gets a Hold decision.
        for unit in self.map.units:
            order = unit.current_order = self.unit_order(unit, HoldOrder)
            self.log_debug(13, 'Using "%s" for %s', order, unit)
            unit.supports = []
            unit.decisions = {}
            decisions.add(Dislodge_Decision(order))
            if order.is_moving():
                self.add_movement_decisions(order, unit, decisions)
            elif order.is_convoying():
                if order.matches(self.next_orders) and not self.illegal(order):
                    convoyers[unit.coast.province.key] = (order.supported.key, unit.nation.key)
                elif not order.__result: order.__result = NSO
            elif order.is_supporting() and not order.__result:
                if order.matches(self.next_orders):
                    decisions.add(Support_Decision(order))
                else: order.__result = NSO
        self.log_debug(11, "Convoyers = %s", convoyers)
        
        # 2) Clean up order inter-dependencies.
        # Each moving unit in a potential head-to-head conflict
        # gets Head and Defend decisions.
        # Each moving unit gets a Path decision.
        # Find available routes for convoyed units.
        # Tell supported units about their supports.
        for choice in decisions[Decision.MOVE]:
            self.add_path_decisions(choice.order, convoyers, decisions)
        for choice in decisions[Decision.SUPPORT]:
            choice.order.supported.supports.append(choice)
        
        # 3) Initialize the dependencies in each decision.
        decision_list = decisions.sorted()
        for choice in decisions: choice.init_deps()
        
        # 4a) Pre-make some decisions if so requested
        if self.datc.datc_4a2 == 'b':
            resolved = self.eightytwo(decision_list)
            decision_list = [choice for choice in decision_list
                if choice not in resolved]
        
        # 4) Run through the decisions until they are all made.
        while decision_list:
            self.log_debug(11, '%d decisions to make...', len(decision_list))
            for choice in decision_list:
                self.log_debug(14, choice)
                for dep in choice.depends: self.log_debug(15, '- ' + str(dep))
            remaining = [choice for choice in decision_list
                    if not choice.calculate()]
            if len(remaining) == len(decision_list):
                decision_list = self.resolve_paradox(remaining)
            else: decision_list = remaining
        
        # 5) Move units around
        turn = self.map.current_turn
        orders = [ORD (turn) (unit.current_order.strict)
            (self.process_results(unit)) for unit in self.map.units]
        
        # 6) Clean up all of the circular references
        for choice in decisions: del choice.depends
        for unit in self.map.units: del unit.decisions
        
        # 7) Return the ORD messages
        return orders
    
    def add_movement_decisions(self, order, unit, decisions):
        decisions.add(Move_Decision(order))
        decisions.add(Attack_Decision(order))
        decisions.add(Prevent_Decision(order))
        
        into = order.destination.province
        if not into.entering:
            hold = Hold_Decision(into)
            decisions.add(hold)
            into.hold = hold
        into.entering.append(unit)
    def add_path_decisions(self, order, convoyers, decisions):
        # Is anyone moving in the opposite direction?
        unit_list = order.unit.coast.province.entering
        heads = any(u in unit_list for u in order.destination.province.units)
        if heads:
            decisions.add(Head_Decision(order))
            decisions.add(Defend_Decision(order))
        
        # Warning: if any routes are given, a convoy will be attempted.
        # So, only give routes if 4.A.3 allows the convoy.
        # Options 'e' and 'f' are prevented in MoveOrder.create().
        disrupt_any = self.datc.datc_4a1 == 'a'
        try_overland = False
        if order.is_convoyed():
            routes = order.get_routes(convoyers, disrupt_any)
            if order.maybe_overland():
                if not routes: routes = None
                elif self.datc.datc_4a3 == 'd':
                    # Divine the 'intent' of the orders
                    key = (order.unit.key, order.unit.nation.key)
                    if key not in convoyers.itervalues(): routes = None
                elif self.datc.datc_4a3 == 'a': pass
                elif heads: # 'b' or 'c': only if a unit moves opposite
                    if self.datc.datc_4a3 == 'c': try_overland = True
                else: routes = None
        else: routes = None
        
        self.log_debug(11, "Path_Decision(%s, %s, %s, %s) from '%s' for 4.A.1 and '%s' for 4.A.3",
                order, routes and [[s.key for s in p] for p in routes],
                not disrupt_any, try_overland, self.datc.datc_4a1, self.datc.datc_4a3)
        path = Path_Decision(order, routes, not disrupt_any, try_overland)
        if order.__result: path.failed = True
        else: decisions.add(path)
    def unit_order(self, unit, order_class):
        ''' Returns the last order given by the unit's owner.
            Depends on handle_SUB() to weed out invalid orders.
        '''#'''
        result = self.next_orders.get_order(unit)
        if not result:
            result = order_class(unit)
            result.__result = None
        return result
    def illegal(self, order):
        ''' Determine quasi-legality of orders.
            If this returns True, then the unit should act like it's holding;
            False, like it's attempting the order.
            Quasi-legal orders can have side effects:
            - quasi-legal movement cancels any support to hold
            - quasi-legal convoys show intent to convoy
        '''#'''
        # Todo: Improve the algorithm for option C;
        # in particular, FAR for convoy paths with missing fleets is okay
        option = self.datc.datc_4e1
        if   option == 'a': return False
        elif option == 'b': return order.__note == NSP
        elif option == 'c': return order.__note in (NSP, FAR, NAS, CST)
        elif option == 'd': return order.__note != MBV
        else: raise NotImplementedError
    def resolve_paradox(self, decisions):
        ''' Resolve the paradox, somehow.
            This may involve circular motion, convoy paradox,
            or stranger things in certain variants.
        '''#'''
        self.log_debug(7, 'Warning: Paradox resolution')
        decision_list = set(decisions)
        core = self.get_core(decisions)
        convoy = False
        moving_to = set()
        moving_from = set()
        self.log_debug(8, 'Choices in paradox core:')
        for choice in core:
            self.log_debug(8, '- %s', choice)
            if choice.type == Decision.MOVE:
                moving_to.add(choice.into.key)
                moving_from.add(choice.order.destination.province.key)
                for unit in choice.into.units:
                    order = unit.current_order
                    if order.is_convoying() and not order.__result:
                        convoy = True
        
        resolved = None
        if convoy:
            if   self.datc.datc_4a2 == 'd': resolved = self.Szykman(core)
            elif self.datc.datc_4a2 == 'f': resolved = self.dptg(core)
        elif moving_to and moving_to == moving_from:
            resolved = self.circular(core)
        if not resolved: resolved = self.fallback(core)
        self.log_debug(8, 'Resolved choices:')
        for choice in resolved:
            self.log_debug(8, '- %s', choice)
            decision_list.discard(choice)
        return decision_list
    def eightytwo(self, decisions):
        ''' Applies the 1982 rule for convoy disruption paradoxes:
            If a convoyed army attacks a fleet which is supporting an action
            in a body of water, and that body of water contains a convoying
            fleet, that support is not cut.
        '''#'''
        result = []
        self.log_debug(8, 'Applying 1982 convoy-disruption rule.')
        def is_convoyed(choice):
            if choice.type == Decision.ATTACK:
                result = choice.order.is_convoyed()
            else: result = False
            return result
        def is_convoying(unit):
            if unit and unit.current_order.is_convoying():
                if self.datc.datc_4a1 == 'a':
                    convoyed = unit.current_order.supported
                    deps = convoyed.decisions[Decision.PATH].depends
                    result = unit.decisions[Decision.DISLODGE] in deps
                else: result = True
            else: result = False
            return result
        for choice in decisions:
            if choice.type == Decision.SUPPORT:
                convoying = is_convoying(choice.order.destination.province.unit)
                army = any(is_convoyed(attack) for attack in choice.depends)
                self.log_debug(11, '* %s: %s, %s', choice, convoying, army)
                for dep in choice.depends: self.log_debug(17, '- ' + str(dep))
                if convoying and army:
                    choice.passed = True
                    result.append(choice)
        return result
    def Szykman(self, decisions):
        ''' Applies the Szykman rule for convoy disruption paradoxes:
            Any convoyed units in the paradox are treated as if they held.
        '''#'''
        result = []
        self.log_debug(8, 'Applying Szykman convoy-disruption rule.')
        for choice in decisions:
            if choice.type == Decision.ATTACK and choice.min_value == 0:
                choice.max_value = 0
                move = choice.order.unit.decisions[Decision.MOVE]
                move.failed = True
                prevent = choice.order.unit.decisions[Decision.PREVENT]
                prevent.min_value = prevent.max_value = 0
                result.extend([choice, move, prevent])
        return result
    def dptg(self, decisions):
        ''' Applies the DPTG rule for convoy disruption paradoxes:
            In confused circles of subversion, disrupt all movement.
            In unconfused circles of subversion, disrupt only the convoys.
        '''#'''
        self.log_debug(8, 'Applying DPTG convoy-disruption rule.')
        def confused(choice):
            result = (choice.type == Decision.SUPPORT
                    and choice.order.supported.current_order.is_convoying())
            if result: self.log_debug(11, '* Confused: %s', choice)
            return result
        if any(confused(d) for d in decisions):
            return self.fallback(decisions)
        else: return self.Szykman(decisions)
    def circular(self, decisions):
        ''' Resolution for circular movement: All moves succeed.'''
        result = []
        self.log_debug(8, 'Applying circular movement rule.')
        for choice in decisions:
            if choice.type == Decision.MOVE:
                choice.passed = True
                result.append(choice)
        return result
    def fallback(self, decisions):
        ''' Fallback method for paradox resolution:
            All moves and supports in the paradox core simply fail.
            Used for paradoxes in unknown variant rule situations.
        '''#'''
        result = []
        self.log_debug(7, 'Applying fallback rule.')
        for choice in decisions:
            if choice.type in (Decision.MOVE, Decision.SUPPORT):
                choice.failed = True
                result.append(choice)
        return result
    def get_core(self, decisions):
        choices = {}
        for choice in decisions:
            choices[choice] = set([dep for dep in choice.depends
                if dep and not dep.decided()])
            self.log_debug(8, '%s:', choice)
            for dep in choice.depends: self.log_debug(11, '- %s', dep)
        while True:
            additions = False
            for deps in choices.itervalues():
                newdeps = set()
                for choice in deps:
                    newdeps |= choices[choice]
                if not (newdeps <= deps):
                    deps |= newdeps
                    additions = True
            if not additions: break
        result = decisions
        self.log_debug(8, '%d original decisions', len(decisions))
        for choice,dep_list in choices.iteritems():
            self.log_debug(11, '%s -> depends on %d', choice, len(dep_list))
            if len(dep_list) < len(result): result = dep_list
        return result or decisions
    def process_results(self, unit):
        ''' Returns the result of the unit's order, based on decisions.
            False Path    -> DSR or NSO (FAR determined earlier)
            True Dislodge -> RET (Maybe after another result)
            False Support -> CUT (NSO determined earlier)
            False Move    -> BNC (Unless DSR)
            True Move     -> SUC
            True Support  -> SUC
            Convoys and Holds: The document is unclear, so:
            Convoy -> NSO if the convoy didn't pass through it
                      Otherwise, same as convoyed unit
                      In either case, plus RET if must retreat
            Hold   -> RET if must retreat, SUC otherwise
        '''#'''
        order = unit.current_order
        result = order.__result
        self.log_debug(13, 'Processing %s; %s', order, result)
        if not result:
            for choice in unit.decisions.itervalues():
                self.log_debug(14, '- ' + str(choice))
            if order.is_moving():
                path = unit.decisions[Decision.PATH]
                if path.passed:
                    if unit.decisions[Decision.MOVE].passed:
                        self.log_debug(11, 'Moving %s to %s', unit, order.destination)
                        unit.move_to(order.destination)
                        result = SUC
                    else: result = BNC
                elif path.routes: result = DSR
                else: result = NSO
            elif order.is_supporting():
                if unit.decisions[Decision.SUPPORT].passed: result = SUC
                else: result = CUT
            elif order.is_convoying():
                routes = order.supported.decisions[Decision.PATH].routes
                if routes and unit.decisions[Decision.DISLODGE] in routes[0]:
                    self.process_results(order.supported)
                    result = order.supported.current_order.__result
                else: result = NSO
            order.__result = result
            self.log_debug(14, 'Final result: %s', result)
        if unit.decisions[Decision.DISLODGE].passed:
            if not unit.dislodged: unit.retreat(self.collect_retreats(unit))
            if result: return (result, RET)
            else: return RET
        else: return result or SUC
    def collect_retreats(self, unit):
        self.log_debug(8, 'Collecting retreats for %s, dislodged by %s', unit, unit.dislodger)
        return [coast.maybe_coast for coast in
                [self.map.coasts[key] for key in unit.coast.borders_out]
                if self.valid_retreat(coast, unit.dislodger)]
    def valid_retreat(self, retreat, dislodger):
        if retreat.province == dislodger: return False
        for unit in retreat.province.units:
            order = unit.current_order
            if not (order.is_moving() and order.unit.decisions[Decision.MOVE].passed):
                return False
        if retreat.province.entering:
            if retreat.province.hold.max_value > 0: return False
            for unit in retreat.province.entering:
                if unit.current_order.unit.decisions[Decision.PREVENT].max_value > 0:
                    return False
        return True


class Decision_Set(defaultdict):
    ''' Holds a set of Decisions, separating them by type.
        As a list, they are returned in the following order:
        PATH decisions, ATTACK decisions, SUPPORT decisions, DEFEND decisions,
        PREVENT decisions, HOLD decisions, MOVE decisions, DISLODGE decisions.
        This order attempts to maximize decisions made in the first pass.
        (But it could be better by alternating attack and support...)
    '''#'''
    def __init__(self): super(Decision_Set, self).__init__(list)
    def add(self, decision): self[decision.type].append(decision)
    def __iter__(self): return chain(*self.itervalues())
    def sorted(self):
        return (self[Decision.PATH] +
                self[Decision.HEAD] +
                self[Decision.ATTACK] +
                self[Decision.SUPPORT] +
                self[Decision.DEFEND] +
                self[Decision.PREVENT] +
                self[Decision.HOLD] +
                self[Decision.MOVE] +
                self[Decision.DISLODGE])

class Decision(object):
    # Tristate decisions
    MOVE, SUPPORT, DISLODGE, PATH, HEAD = range(5)
    # Numeric decisions
    ATTACK, HOLD, PREVENT, DEFEND = range(5,9)
    
    # Can this be automated?
    type = None
    names = {
        0: 'Move',
        1: 'Support',
        2: 'Dislodge',
        3: 'Path',
        4: 'Head',
        5: 'Attack',
        6: 'Hold',
        7: 'Prevent',
        8: 'Defend',
    }
    
    # We have over a hundred decisions per movement phase;
    # memory management is crucial.
    __slots__ = ('depends', 'into', 'order')
    
    def __init__(self, order):
        self.depends = []    # Decisions on which this one depends.
        self.into    = None  # Province being moved into
        self.order   = order
        
        if self.type != Decision.HOLD:
            order.unit.decisions[self.type] = self
            if order.destination: self.into = order.destination.province
    def __str__(self):
        return '%s decision for %s; %s' % (
            self.names[self.type], self.order.unit, self.state())
    def __repr__(self): return str(self)   # To make lists look nice
    def state(self): raise NotImplementedError
    def battles(self):
        unit_list = self.order.unit.coast.province.entering
        return [unit for unit in self.into.units if unit in unit_list]

class Tristate_Decision(Decision):
    __slots__ = ('passed', 'failed')
    status = {
        (False, False): 'Undecided',
        (True,  False): 'Passed',
        (False, True):  'Failed',
        (True,  True):  'Confused'
    }
    
    def __init__(self, *args):
        Decision.__init__(self, *args)
        self.passed = False
        self.failed = False
    def decided(self):
        if self.passed and self.failed:
            print 'Error in %s, using' % self
            for choice in self.depends: print '-', choice
        #if self.passed or self.failed: print 'Decision made for ' + str(self)
        return self.passed or self.failed
    def state(self):
        return self.status[(self.passed, self.failed)]
    def minmax(self, decision_list):
        ''' Returns the highest maximum and minimum values in the decision list.'''
        min_found = max_found = 0
        for decision in decision_list:
            if decision.min_value > min_found: min_found = decision.min_value
            if decision.max_value > max_found: max_found = decision.max_value
        return min_found, max_found
class Move_Decision(Tristate_Decision):
    __slots__ = ()
    type = Decision.MOVE
    def init_deps(self):
        # Slightly different than the DATC document:
        # the Hold Strength is always counted.
        # However, the Hold Strength will never be greater than the Defend
        # Strength in Standard, because the unit must be moving.
        self.depends.append(self.order.unit.decisions[Decision.ATTACK])
        self.depends.append(self.into.hold)
        self.depends.extend([unit.decisions[Decision.DEFEND]
            for unit in self.battles()])
        self.depends.extend([unit.decisions[Decision.PREVENT]
            for unit in self.into.entering if unit != self.order.unit])
    def calculate(self):
        #print 'Calculating %s:' % str(self)
        #for dep in self.depends: print '+ ' + str(dep)
        attack = self.depends[0]
        min_oppose, max_oppose = self.minmax(self.depends[1:])
        self.passed = attack.min_value >  max_oppose
        self.failed = attack.max_value <= min_oppose
        if self.passed:
            for unit in self.order.destination.province.units:
                unit.dislodger = self.order.unit.coast.province
        return self.decided()
class Support_Decision(Tristate_Decision):
    __slots__ = ()
    type = Decision.SUPPORT
    def init_deps(self):
        self.depends = [self.order.unit.decisions[Decision.DISLODGE]] + [
            u.decisions[Decision.ATTACK]
            for u in self.order.unit.coast.province.entering
            if u.coast.province != self.into
        ]
    def calculate(self):
        dislodge = self.depends[0]
        min_oppose, max_oppose = self.minmax(self.depends[1:])
        self.passed = dislodge.failed and max_oppose == 0
        self.failed = dislodge.passed or  min_oppose >= 1
        return self.decided()
class Dislodge_Decision(Tristate_Decision):
    # Failed: the unit stays; Passed: it must retreat.
    __slots__ = ()
    type = Decision.DISLODGE
    def init_deps(self):
        if self.order.is_moving():
            my_move = self.order.unit.decisions[Decision.MOVE]
        else: my_move = None
        self.depends = [my_move] + [unit.decisions[Decision.MOVE]
            for unit in self.order.unit.coast.province.entering]
    def calculate(self):
        my_move = self.depends[0]
        self.passed = (not my_move or my_move.failed) and any(d.passed for d in self.depends[1:])
        self.failed = (my_move and    my_move.passed) or  all(d.failed for d in self.depends[1:])
        return self.decided()
class Path_Decision(Tristate_Decision):
    # When passed, a convoyed unit will have a good route as routes[0].
    # A unit moving overland will have an empty routes.
    __slots__ = ('routes', 'disrupt_all', 'backup')
    type = Decision.PATH
    def __init__(self, order, routes, disrupt_all, try_overland):
        Tristate_Decision.__init__(self, order)
        self.disrupt_all = disrupt_all
        self.backup = try_overland
        self.routes = routes and [sum([[unit.decisions[Decision.DISLODGE]
                    for unit in prov.units]
                for prov in path], [])
            for path in routes
        ]
    def init_deps(self):
        if self.routes: self.depends = set(sum(self.routes, []))
        else: self.depends = []
    def calculate(self):
        #print 'Calculating %s (%s, %s, %s):' % (self,
        #        self.routes and [[s.key for s in p] for p in self.routes],
        #        self.disrupt_all, self.backup)
        #for dep in self.depends: print '+ ' + str(dep)
        if self.routes:
            # There should be a way to do it in one pass, but this is easier.
            self.failed = self.calc_path_fail()
            if self.failed and self.backup: self.routes = None
            else: self.passed = self.calc_path_pass()
        if not self.routes:
            # None means an overland route; empty list means unavailable convoy.
            if self.routes is None:
                self.passed = self.order.unit.can_move_to(self.order.destination)
            else:
                routes = self.order.routes
                if routes: self.order.set_path([prov.unit for prov in routes[0]])
                self.passed = False
            self.failed = not self.passed
        return self.decided()
    def calc_path_pass(self):
        if self.disrupt_all:
            # Check for any path with no dislodged units
            for path in self.routes:
                for choice in path:
                    if not choice.failed: break
                else:
                    self.set_route(path)
                    return True
            else: return False
        else:
            # Check that no path has potentially dislodged units
            for path in self.routes:
                for choice in path:
                    if not choice.failed: return False
            self.set_route(self.routes[0])
        return True
    def calc_path_fail(self):
        if self.disrupt_all:
            # Check for a dislodged unit on each path
            for path in self.routes:
                for choice in path:
                    if choice.passed: break
                else: return False
            else:
                self.set_route(self.routes[0])
                return True
        else:
            # Check for a dislodged unit on any path
            for path in self.routes:
                for choice in path:
                    if choice.passed:
                        self.set_route(path)
                        return True
        return False
    def set_route(self, path):
        self.routes = [path]
        route = [choice.order.unit for choice in path]
        self.order.set_path(route)
class Head_Decision(Tristate_Decision):
    # Failed: the units bypass each other; Passed: they battle each other.
    __slots__ = ()
    type = Decision.HEAD
    def init_deps(self):
        path = self.order.unit.decisions[Decision.PATH]
        heads = [unit.decisions[Decision.HEAD] for unit in self.battles()]
        self.depends = [path] + heads
    def calculate(self):
        # If this unit is convoyed, it fails.
        # If the opposing heads all fail, it fails.
        # If this unit and an opposing unit move overland, it succeeds.
        # Tricky part is datc_4a3.c:
        # the taken path depends on a Path decision.
        path = self.depends[0]
        heads = self.depends[1:]
        if path.failed: self.failed = True
        elif all(head.failed for head in heads): self.failed = True
        elif path.passed:
            if path.routes: self.failed = True
            elif any(head.overland() for head in heads): self.passed = True
        return self.decided()
    def overland(self):
        path = self.depends[0]
        return self.passed or (path.passed and not path.routes)

class Numeric_Decision(Decision):
    ''' A numeric decision, which is decided when the maximum possible value
        is equal to the minimum possible value.
        The minimum never decreases; the maximum never increases.
    '''#'''
    __slots__ = ('min_value', 'max_value')
    def __init__(self, order):
        Decision.__init__(self, order)
        self.min_value = 0
        self.max_value = Infinity
    def decided(self):
        if self.max_value < self.min_value:
            print 'Error in %s, using' % self
            for choice in self.depends: print '-', choice
        #if self.max_value == self.min_value: print 'Decision made for ' + str(self)
        return self.max_value == self.min_value
    def state(self):
        return 'minimum %d, maximum %s' % (self.min_value, self.max_value)
class Attack_Decision(Numeric_Decision):
    # Strength of the attack
    __slots__ = ()
    type = Decision.ATTACK
    def init_deps(self):
        unit = self.order.unit
        path = unit.decisions[Decision.PATH]
        heads = [other.decisions[Decision.HEAD] for other in self.battles()]
        moves = [other.decisions.get(Decision.MOVE) for other in self.into.units]
        self.depends = [path] + heads + moves + unit.supports
    def calculate(self):
        attacked = self.into.units
        index1 = 1 + len(self.battles())
        index2 = index1 + len(attacked)
        path = self.depends[0]
        heads = self.depends[1:index1]
        moves = zip(attacked, self.depends[index1:index2])
        supports = self.depends[index2:]
        def minimal_test(choice): return choice and choice.passed
        def maximal_test(choice): return choice and not choice.failed
        self.min_value = self.calc_attack(path, heads, moves, supports, minimal_test, maximal_test)
        self.max_value = self.calc_attack(path, heads, moves, supports, maximal_test, minimal_test)
        #print 'Attack values: "%s" / "%s"' % (self.min_value, self.max_value)
        #print '  from (%s, %s, %s, %s)' % (path, heads, moves, supports)
        return self.decided()
    def calc_attack(self, path, heads, moves, supports, valid, valid_head):
        if valid(path):
            valid_supports = filter(valid, supports)
            powers = set([choice.order.unit.nation.key
                for choice in heads if valid_head(choice)] +
                [unit.nation.key for unit, choice in moves if not valid(choice)])
            #print 'Calc attack powers: %s' % powers
            if self.order.unit.nation.key in powers: return 0
            return 1 + len([choice for choice in valid_supports
                if choice.order.unit.nation.key not in powers])
        else: return 0
class Hold_Decision(Numeric_Decision):
    # Strength of the defense
    __slots__ = ()
    type = Decision.HOLD
    def __str__(self):
        return '%s decision for %s; %s' % (
            self.names[self.type], self.order, self.state())
    def init_deps(self):
        # Todo: Make this multi-unit safe
        for unit in self.order.units:
            if unit.current_order.is_moving():
                self.depends = [unit.decisions[Decision.MOVE]]
            else: self.depends = [None] + unit.supports
    def calculate(self):
        if self.depends:
            first = self.depends[0]
            if first:
                if first.failed:   self.min_value = self.max_value = 1
                elif first.passed: self.min_value = self.max_value = 0
                else:
                    self.min_value = 0
                    self.max_value = 1
            else:
                self.min_value = self.max_value = 1
                for support in self.depends[1:]:
                    if not support.failed:
                        self.max_value += 1
                        if support.passed:
                            self.min_value += 1
        else: self.max_value = self.min_value = 0
        return self.decided()
class Prevent_Decision(Numeric_Decision):
    __slots__ = ()
    type = Decision.PREVENT
    def init_deps(self):
        unit = self.order.unit
        path = unit.decisions[Decision.PATH]
        head = unit.decisions.get(Decision.HEAD)
        moves = [other.decisions[Decision.MOVE] for other in self.battles()]
        self.depends = [path, head] + moves + unit.supports
    def calculate(self):
        path = self.depends[0]
        if path.failed: self.max_value = self.min_value = 0
        else:
            head = self.depends[1]
            moves = [choice for choice in self.depends
                if choice and choice.type == Decision.MOVE]
            supports = [choice for choice in self.depends
                if choice and choice.type == Decision.SUPPORT]
            
            self.max_value = self.min_value = 1
            for support in supports:
                if not support.failed:
                    self.max_value += 1
                    if support.passed: self.min_value += 1
            if (head and not head.failed
                    and any(not choice.failed for choice in moves)):
                self.min_value = 0
                if (head.passed and any(choice.passed for choice in moves)):
                    self.max_value = 0
            elif not path.passed: self.min_value = 0
        return self.decided()
class Defend_Decision(Numeric_Decision):
    __slots__ = ()
    type = Decision.DEFEND
    def init_deps(self):
        unit = self.order.unit
        self.depends = [unit.decisions[Decision.HEAD]] + unit.supports
    def calculate(self):
        # Significantly different from the DATC description,
        # taking the new HEAD decisions into account.
        head = self.depends[0]
        if head.failed: self.min_value = self.max_value = 0
        else:
            self.min_value = self.max_value = 1
            for support in self.depends[1:]:
                if not support.failed:
                    self.max_value += 1
                    if support.passed:
                        self.min_value += 1
            if not head.passed: self.min_value = 0
        return self.decided()
