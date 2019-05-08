r'''Parlance unit orders
    Copyright (C) 2004-2008  Eric Wald
    
    This module contains representations of the types of orders that can be
    sent by a player.  Note that these classes actually contain quite a bit of
    the functionality that you might expect to find in the Judge.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

from itertools   import chain
from operator    import lt, gt

from functions   import Comparable, all, any, autosuper, defaultdict
from gameboard   import Coast, Power, Turn, Unit
from language    import Message
from tokens      import *

__all__ = [
    'createUnitOrder',
    'UnitOrder',
    'MovementPhaseOrder',
    'HoldOrder',
    'MoveOrder',
    'ConvoyingOrder',
    'ConvoyedOrder',
    'SupportOrder',
    'SupportHoldOrder',
    'SupportMoveOrder',
    'RetreatPhaseOrder',
    'DisbandOrder',
    'RetreatOrder',
    'BuildPhaseOrder',
    'WaiveOrder',
    'BuildOrder',
    'RemoveOrder',
    'OrderSet',
]

class UnitOrder(Comparable):
    ''' Abstract base class for all types of orders.'''
    __metaclass__ = autosuper
    order_type = None
    destination = None   # Coast where the unit expects to end up
    order = None         # The order as originally issued
    unit = None          # The Unit being ordered
    key = None           # The order's essential parts
    
    def __str__(self): raise NotImplementedError
    def tokenize(self): return self.order or Message(self.key)
    def __cmp__(self, other): return cmp(self.key, other.key)
    @classmethod
    def create(klass, order, nation, board, datc):
        result = klass(board.ordered_unit(nation, order[0], datc))
        result.order = order
        return result
    
    # Order queries
    def is_moving(self):     return self.order_type in (MTO, CTO, RTO)
    def is_holding(self):    return self.order_type == HLD
    def is_supporting(self): return self.order_type == SUP
    def is_convoying(self):  return self.order_type == CVY
    def is_convoyed(self):   return self.order_type == CTO
    def is_leaving(self):    return self.order_type in (MTO, CTO, RTO, DSB, REM)
    def moving_to(self, province):
        return self.is_moving() and province == self.destination.province
    def matches(self, order_set): return True
    def maybe_overland(self): return False
    def order_note(self, power, phase, past_orders=None):
        ''' Returns a Token representing the legality of the order.
            - MBV: Order is OK
            - FAR: Not adjacent
            - NSP: No such province
            - NSU: No such unit
            - NAS: Not at sea (for a convoying fleet)
            - NSF: No such fleet (in VIA section of CTO
                   or the unit performing a CVY)
            - NSA: No such army (for unit being ordered to CTO
                   or for unit being CVYed)
            - NYU: Not your unit
            - NRN: No retreat needed for this unit
            - NVR: Not a valid retreat space
            - YSC: Not your supply centre
            - ESC: Not an empty supply centre
            - HSC: Not a home supply centre
            - NSC: Not a supply centre
            - CST: No coast specified for fleet build in bicoastal province,
                   or an attempt to build a fleet inland, or an army at sea.
            - NMB: No more builds allowed
            - NMR: No more removals allowed
            - NRS: Not the right season
        '''#'''
        note = MBV
        if not (self.order_type.value() & phase):   note = NRS
        elif self.unit.nation != power:             note = NYU
        elif not self.unit.coast.province.exists(): note = NSP
        elif not self.unit.exists():                note = NSU
        elif self.destination:
            if not self.destination.province.exists(): note = NSP
            elif not self.unit.exists(): note = NSU
        return note
    @property
    def strict(self): return Message(self.key)

class MovementPhaseOrder(UnitOrder):
    routes = []
    @staticmethod
    def convoy_note(convoyed, destination, routes, route_valid=bool):
        result = FAR
        if not (convoyed.exists() and convoyed.can_be_convoyed()): result = NSA
        elif not destination.exists(): result = CST
        elif destination.province.is_coastal():
            if any(route_valid(route) for route in routes): result = MBV
        #print 'convoy_note(%s, %s) => %s' % (convoyed, destination, result)
        return result
    def get_routes(self, convoyers, ignore_foreign):
        if self.unit.can_be_convoyed():
            if self.path:
                path_list = [[fleet.coast.province for fleet in self.path]]
            else: path_list = self.routes
            if path_list:
                key = self.unit.key
                def available(prov):
                    return convoyers.get(prov.key, (None, None))[0] == key
                all_routes = [path for path in path_list
                        if all(available(place) for place in path)]
                
                if ignore_foreign:
                    # DPTG craziness: ignore foreign convoyers if we can go alone.
                    nation = self.unit.nation
                    def countryman(prov):
                        return convoyers.get(prov.key, (None, None))[1] == nation
                    solo_routes = [path for path in all_routes
                            if all(countryman(place) for place in path)]
                else: solo_routes = None
                return (solo_routes or all_routes)
        return []
    def supported_name(self):
        name = self.supported.coast.prefix
        power = self.supported.nation
        if self.unit.nation == power: return name
        else: return '%s %s' % (power.adjective, name)
class HoldOrder(MovementPhaseOrder):
    order_type = HLD
    def __init__(self, unit):
        self.key = (unit.key, HLD)
        self.unit = unit
        self.destination = unit.coast
    def __repr__(self): return 'HoldOrder(%r)' % self.unit
    def __str__(self): return self.unit.coast.prefix + ' HOLD'
class MoveOrder(MovementPhaseOrder):
    order_type = MTO
    path = None
    def __init__(self, unit, destination_coast, maybe_convoy=False):
        self.key = (unit.key, MTO, destination_coast.maybe_coast)
        self.unit = unit
        self.destination = destination_coast
        self.maybe_convoy = maybe_convoy
    def __str__(self):
        return '%s -> %s' % (self.unit.coast.prefix, self.destination.name)
    def is_convoyed(self):    return self.maybe_convoy
    def maybe_overland(self): return self.maybe_convoy
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV:
            if not self.unit.can_move_to(self.destination): note = FAR
            elif not self.destination.exists():             note = CST
        return note
    @classmethod
    def create(klass, order, nation, board, datc):
        unit = board.ordered_unit(nation, order[0], datc)
        dest = board.ordered_coast(unit, order[2], datc)
        if unit.can_be_convoyed() and datc.datc_4a3 != 'f':
            # Implicit convoys are allowed; check for them
            routes = unit.coast.convoy_routes(dest.province, board)
            if not routes: result = klass(unit, dest)
            elif not unit.can_move_to(dest):
                # Can't move directly; attempt to convoy
                result = ConvoyedOrder(unit, dest)
            elif datc.datc_4a3 == 'e' or klass.convoy_note(unit, dest, routes) != MBV:
                # DPTG: Only convoy adjacent if it's explicit
                # For other options, consider possible adjacent convoys
                result = klass(unit, dest)
            else: result = klass(unit, dest, True)
            result.routes = routes
        else: result = klass(unit, dest)
        result.order = order
        return result
    def set_path(self, path):
        # Allows the server to send path specifications
        # even on orders that didn't originally have any.
        self.path = path
        self.path_key = tuple([fleet.coast.province.key for fleet in path])
        self.key = (self.unit.key, CTO, self.destination.province.key, VIA, self.path_key)
class ConvoyingOrder(MovementPhaseOrder):
    order_type = CVY
    def __init__(self, unit, mover, destination):
        self.key = (unit.key, CVY, mover.key, CTO, destination.province.key)
        self.unit = unit
        self.supported = mover
        self.destination = destination
    def __str__(self):
        return '%s CONVOY %s -> %s' % (self.unit.coast.prefix,
                self.supported_name(), self.destination.name)
    def matches(self, order_set):
        ''' Whether the order is matched by the convoyed unit. '''
        counterpart = order_set.get_order(self.supported)
        return (self.supported.exists() and counterpart and counterpart.is_convoyed()
            and self.destination.matches(counterpart.destination.key))
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV:
            if not self.unit.coast.province.can_convoy(): note = NAS
            elif not self.unit.can_convoy():              note = NSF
            else:
                def has_this_fleet(route, fleet=self.unit.coast.province.key):
                    return fleet in route
                note = self.convoy_note(self.supported, self.destination, self.routes, has_this_fleet)
        return note
    @classmethod
    def create(klass, order, nation, board, datc):
        unit = board.ordered_unit(nation, order[0], datc)
        mover = board.ordered_unit(nation, order[2], datc)
        dest = board.ordered_coast(mover, order[4], datc)
        result = klass(unit, mover, dest)
        result.routes = mover.coast.convoy_routes(dest.province, board)
        result.order = order
        return result
class ConvoyedOrder(MovementPhaseOrder):
    order_type = CTO
    def __init__(self, unit, destination, path=None):
        # The path should be a list of Units (fleets), not provinces.
        # If the server supports pathless convoys, it may be omitted.
        self.unit = unit
        self.destination = destination
        self.path = None
        self.path_key = None
        if path: self.set_path(path)
        else: self.key = (unit.key, CTO, destination.province.key)
    def set_path(self, path):
        # Allows the server to send path specifications
        # even on orders that didn't originally have any.
        self.path = path
        self.path_key = tuple([fleet.coast.province.key for fleet in path])
        self.key = (self.unit.key, CTO, self.destination.province.key, VIA, self.path_key)
    def __str__(self):
        return '%s -> %s -> %s' % (self.unit.coast.prefix,
                self.path and ' -> '.join([str(u.coast.province) for u in self.path]) or '...',
                self.destination.name)
    def matches(self, order_set):
        ''' Whether the order is matched by the convoying unit(s). '''
        def matching(fleet):
            counterpart = order_set.get_order(fleet)
            if counterpart:
                return (counterpart.is_convoying()
                        and counterpart.supported == self.unit
                        and counterpart.destination.matches(self.destination.key))
            return False
        if self.path: return all(matching(unit) for unit in self.path)
        else: return True
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV:
            note = self.convoy_note(self.unit, self.destination, self.routes)
            if note == MBV and self.path:
                def real_prov(fleet): return fleet.coast.province.exists()
                def at_sea(fleet): return fleet.coast.province.can_convoy()
                def check(f): return not all(f(unit) for unit in self.path)
                if   check(real_prov):                 note = NSP
                elif check(Unit.exists):               note = NSF
                elif check(at_sea):                    note = NAS
                elif check(Unit.can_convoy):           note = NSF
                elif self.path_key not in self.routes: note = FAR
        return note
    @classmethod
    def create(klass, order, nation, board, datc):
        unit = board.ordered_unit(nation, order[0], datc)
        dest = board.ordered_coast(unit, order[2], datc)
        if len(order) > 4 and datc.datc_4a6 != 'a':
            path = [board.ordered_unit(nation, prov, datc)
                for prov in order[4]]
            #for prov in path: print 'Convoying unit: %s' % prov
        else: path = None
        result = klass(unit, dest, path)
        if datc.datc_4a6 == 'c' and path is None:
            result.routes = []
        else: result.routes = unit.coast.convoy_routes(dest.province, board)
        result.order = order
        return result

class SupportOrder(MovementPhaseOrder):
    order_type = SUP
    supported = None
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV:
            if not self.supported.coast.province.exists():    note = NSP
            elif not self.supported.exists():                 note = NSU
            elif not self.unit.can_move_to(self.destination.province):
                note = FAR
        return note
    @classmethod  # This one could be staticmethod, but pychecker complains.
    def create(klass, order, nation, board, datc):
        # Note that we don't care about order[3], so it could be MTO or CTO.
        unit = board.ordered_unit(nation, order[0], datc)
        supported = board.ordered_unit(nation, order[2], datc)
        if len(order) > 4:
            dest = board.ordered_coast(supported, order[4], datc)
            legal_dest = True
            if supported.can_move_to(dest):
                if datc.datc_4b4 in 'abc' and not dest.exists():
                    # Coastline specifications are required due to ambiguity
                    legal_dest = False
                elif dest.coastline:
                    if dest.coastline not in Message(order[4]):
                        # Coastline specifications might be required anyway
                        legal_dest = datc.datc_4b4 != 'a'
                    elif datc.datc_4b4 == 'e':
                        # Coastline specifications are ignored
                        dest = Coast(dest.unit_type, dest.province, None, [])
                routes = []
            else: routes = supported.coast.convoy_routes(dest.province, board)
            result = SupportMoveOrder(unit, supported, dest, legal_dest)
            result.routes = routes
        else: result = SupportHoldOrder(unit, supported)
        result.order = order
        return result
class SupportHoldOrder(SupportOrder):
    def __init__(self, unit, holder):
        self.key = (unit.key, SUP, holder.key)
        self.unit = unit
        self.supported = holder
        self.destination = holder.coast
    def __str__(self):
        return '%s SUPPORT %s' % (self.unit.coast.prefix, self.supported_name())
    def matches(self, order_set):
        ''' Whether the order is matched by the supported unit.'''
        return (self.supported.exists()
                and not order_set.is_moving(self.supported)
                and self.supported.coast.province != self.unit.coast.province)
class SupportMoveOrder(SupportOrder):
    def __init__(self, unit, mover, destination, legal_coast=True):
        # Note: destination.maybe_coast would be better,
        # but is disallowed by the language.
        self.key = (unit.key, SUP, mover.key, MTO, destination.province.key)
        self.unit = unit
        self.supported = mover
        self.destination = destination
        self.legal = legal_coast
    def __str__(self):
        return '%s SUPPORT %s -> %s' % (self.unit.coast.prefix,
                self.supported_name(), self.destination.name)
    def matches(self, order_set):
        ''' Whether the order is matched by the supported unit.'''
        counterpart = order_set.get_order(self.supported)
        return (self.supported.nation and counterpart.is_moving()
            and self.destination.matches(counterpart.destination.key))
    def order_note(self, power, phase, past_orders=None):
        # Note that the mover's destination need not exist: it could have
        # a coastline of None for a fleet moving to bicoastal.  However,
        # the province must exist, and both units must be able to move there.
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV:
            if self.supported.can_move_to(self.destination):
                if not self.legal: note = CST
            else:
                def has_not(route, prov=self.unit.coast.province.key):
                    return prov not in route
                result = self.convoy_note(self.supported, self.destination, self.routes, has_not)
                if result != MBV: note = FAR
        return note

class RetreatPhaseOrder(UnitOrder):
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV and not self.unit.dislodged: note = NRN
        return note
class DisbandOrder(RetreatPhaseOrder):
    order_type = DSB
    def __init__(self, unit):
        self.key = (unit.key, DSB)
        self.unit = unit
        self.destination = None
    def __str__(self): return self.unit.coast.prefix + ' DISBAND'
class RetreatOrder(RetreatPhaseOrder):
    order_type = RTO
    def __init__(self, unit, destination_coast):
        self.key = (unit.key, RTO, destination_coast.maybe_coast)
        self.unit = unit
        self.destination = destination_coast
    def __str__(self):
        return '%s -> %s' % (self.unit.coast.prefix, self.destination.name)
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV and self.destination.maybe_coast not in self.unit.retreats:
            note = NVR
        return note
    @classmethod
    def create(klass, order, nation, board, datc):
        unit = board.ordered_unit(nation, order[0], datc)
        dest = board.ordered_coast(unit, order[2], datc)
        result = klass(unit, dest)
        result.order = order
        return result

class BuildPhaseOrder(UnitOrder):
    op = NotImplemented
    def required(self, power, past_orders):
        if past_orders: surplus = -past_orders.builds_remaining(power)
        else: surplus = power.surplus()
        return self.op(surplus, 0)
class WaiveOrder(BuildPhaseOrder):
    order_type = WVE
    op = lt
    def __init__(self, power):
        if power: self.key = (power.key, WVE)
        else: self.key = WVE
        self.nation = power
    def __str__(self): return 'Waives a build'
    def order_note(self, power, phase, past_orders=None):
        note = MBV
        if not (self.order_type.value() & phase):   note = NRS
        elif self.nation != power:                  note = NYU
        elif not self.required(power, past_orders): note = NMB
        return note
    @classmethod
    def create(klass, order, nation, board, datc):
        for token in Message(order):
            if token.is_power():
                power = board.powers.get(token) or Power(token, [])
                break
        else: power = board.powers[nation.key]
        result = klass(power)
        result.order = order
        return result
class BuildOrder(BuildPhaseOrder):
    order_type = BLD
    op = lt
    def __init__(self, unit):
        self.key = (unit.key, BLD)
        self.unit = unit
        self.destination = unit.coast
    def __str__(self):
        # Todo: This should specify the unit's nation, if different.
        def an(text):
            if text[0] in 'aeiouAEIOU': return 'an %s' % text
            else: return 'a %s' % text
        coast = self.unit.coast
        return 'Builds %s in %s' % (an(coast.type_name().lower()), coast.name)
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == NSU:
            coast = self.unit.coast
            old_order = past_orders and past_orders.has_order(coast.province)
            if not coast.exists():                                 note = CST
            elif not coast.province.is_supply():                   note = NSC
            elif self.unit.nation != coast.province.owner:         note = YSC
            elif self.unit.nation.key not in coast.province.homes: note = HSC
            elif coast.province.units:                             note = ESC
            elif old_order:                                        note = ESC
            elif not self.required(power, past_orders):            note = NMB
            else:                                                  note = MBV
        elif note == MBV:                                          note = ESC
        return note
class RemoveOrder(BuildPhaseOrder):
    order_type = REM
    op = gt
    def __init__(self, unit):
        self.key = (unit.key, REM)
        self.unit = unit
    def __str__(self):
        # Todo: This should specify the unit's nation, if different.
        coast = self.unit.coast
        return 'Removes the %s in %s' % (coast.type_name().lower(), coast.name)
    def order_note(self, power, phase, past_orders=None):
        note = self.__super.order_note(power, phase, past_orders)
        if note == MBV and not self.required(power, past_orders): note = NMR
        return note

_class_types = {
    HLD: HoldOrder,
    MTO: MoveOrder,
    SUP: SupportOrder,
    CVY: ConvoyingOrder,
    CTO: ConvoyedOrder,
    RTO: RetreatOrder,
    DSB: DisbandOrder,
    BLD: BuildOrder,
    REM: RemoveOrder,
    WVE: WaiveOrder,
}
def createUnitOrder(order, nation, board, datc):
    ''' Determine the class of the order, and create one of that type.
        This would have been nice as UnitOrder.__new__(),
        but that causes headaches in the child classes.
        
        order is a folded message, part of a SUB command;
        nation is the country making the order;
        board is a Map object.
    '''#'''
    key = len(order) > 1 and 1 or 0
    return _class_types[order[key]].create(order, nation, board, datc)

class OrderSet(defaultdict):
    ''' A mapping of Coast key -> UnitOrder, with special provisions for Waives.
        >>> Moscow = standard_map.spaces[MOS].unit
        >>> Warsaw = standard_map.spaces[WAR].unit.coast
        >>> Russia = standard_map.powers[RUS]
        >>> France = standard_map.powers[FRA]
        >>> russian = OrderSet(Russia)
        >>> russian.add(HoldOrder(Moscow))
        >>> russian.add(WaiveOrder(Russia))
        >>> russian.add(MoveOrder(Moscow, Warsaw))
        >>> russian.add(WaiveOrder(France))
        >>> print russian.create_SUB()
        SUB ( FRA WVE ) ( RUS WVE ) ( ( RUS AMY MOS ) HLD ) ( ( RUS AMY MOS ) MTO WAR )
    '''#'''
    def __init__(self, default_nation=None):
        super(OrderSet, self).__init__(list)
        self.default = default_nation
    def __len__(self):
        ''' Primarily to allow "if order_set:" to work as expected,
            but also makes iteration slightly more efficient.
        '''#'''
        return sum([len(orders) for orders in self.itervalues()])
    def __iter__(self):
        ''' Allows the construction "for order in order_set:" '''
        return chain(*self.values())
    def __str__(self):
        nations = {}
        for order in self:
            key = order.__author and order.__author.key
            nations.setdefault(key, []).append(order)
        return '{ %s }' % '; '.join(['%s: %s' %
                (nation, ', '.join(map(str, orders)))
            for nation, orders in nations.iteritems()])
    def __copy__(self):
        # Inefficient, but it works much better than straight copy() does.
        result = OrderSet(self.default)
        for order in self:
            item = order.unit or order.nation
            result[item.key].append(order)
        return result
    
    def add(self, order, nation=None):
        order.__author = nation or self.default or (order.unit or order).nation
        item = order.unit or order.nation
        self[item.key].append(order)
    def remove(self, order, nation=None):
        ''' Attempt to remove a specific order.
            Returns the actual order removed, or None if it wasn't found.
            
            >>> english = OrderSet(); print english
            {  }
            >>> London = standard_map.spaces[LON].units[0]
            >>> NorthSea = standard_map.coasts[(FLT, NTH, None)]
            >>> EngChannel = standard_map.coasts[(FLT, ECH, None)]
            >>> english.add(MoveOrder(London, NorthSea), ENG); print english
            { ENG: Fleet London -> North Sea }
            >>> english.add(MoveOrder(London, EngChannel), ENG); print english
            { ENG: Fleet London -> North Sea, Fleet London -> English Channel }
            >>> print english.remove(MoveOrder(London, NorthSea), ENG)
            Fleet London -> North Sea
            >>> print english.remove(MoveOrder(London, EngChannel), GER)
            None
            >>> print english
            { ENG: Fleet London -> English Channel }
        '''#'''
        author = nation or self.default
        order_list = self[(order.unit or order.nation).key]
        for index, item in enumerate(order_list):
            if item == order and (item.__author == author or not author):
                return order_list.pop(index)
        return None
    def waive(self, number, nation=None):
        for dummy in range(number):
            self.add(WaiveOrder(nation or self.default), nation)
    def create_SUB(self, nation=None):
        ''' Returns a Message for submitting these orders to the server,
            or None if no orders need to be sent.
            Use the nation argument to submit only that nation's orders.
        '''#'''
        result = self.order_list(nation)
        if result: return SUB % sorted(result)
        return None
    def order_list(self, nation=None):
        if nation: return [o for o in self if o.__author == nation]
        else: return list(self)
    def clear(self, nation=None):
        if nation:
            for key, orders in self.items():
                self[key] = [o for o in orders if o.__author != nation]
        else: dict.clear(self)
    
    def holding(self): return [o for o in self if o.is_holding()]
    def moving_into(self, province):
        return [order for order in self if order.is_moving()
            and order.destination.province.key == province.key]
    def is_moving(self, unit):
        result = self.get_order(unit)
        return result and result.is_moving()
    def has_order(self, province):
        for order in self:
            if order.unit and order.unit.coast.province == province:
                return True
        else: return False
    def get_order(self, unit):
        ''' Find the "best" order for a given unit.
            Currently returns the last order given by the unit's owner.
        '''#'''
        result = None
        for order in self[unit.key]:
            if order.__author == unit.nation: result = order
        return result
    
    def builds_remaining(self, power):
        ''' Counts the number of builds the power still needs to order,
            taking orders in the set into account.
            Returns a negative number if more removals are required.
            
            >>> germany = standard_map.powers[GER]
            >>> saved = list(germany.centers)
            >>> orders = OrderSet()
            
            >>> orders.builds_remaining(germany)
            0
            >>> germany.centers.append(DEN)
            >>> orders.builds_remaining(germany)
            1
            >>> orders.add(WaiveOrder(germany))
            >>> orders.builds_remaining(germany)
            0
            >>> orders.add(BuildOrder(Unit(germany,
            ...     standard_map.coasts[(FLT, DEN, None)])))
            >>> orders.builds_remaining(germany)
            0
            >>> orders.remove(WaiveOrder(germany)) and None
            >>> orders.builds_remaining(germany)
            0
            
            >>> orders.clear(); germany.centers = [DEN]
            >>> orders.builds_remaining(germany)
            -2
            >>> orders.add(RemoveOrder(standard_map.spaces[BER].unit))
            >>> orders.builds_remaining(germany)
            -1
            >>> orders.add(RemoveOrder(standard_map.spaces[BER].unit))
            >>> orders.builds_remaining(germany)
            -1
            >>> orders.add(RemoveOrder(standard_map.spaces[MUN].unit))
            >>> orders.builds_remaining(germany)
            0
            >>> orders.add(RemoveOrder(standard_map.spaces[KIE].unit))
            >>> orders.builds_remaining(germany)
            0
            
            # Restore original map
            >>> germany.centers = saved
        '''#'''
        surplus = power.surplus()
        waives = 0
        builds = set()
        removes = set()
        for order in self.order_list(power):
            if order.order_type is WVE: waives += 1
            elif order.order_type is BLD:
                builds.add(order.unit.coast.province.key)
            elif order.order_type is REM:
                removes.add(order.unit.key)
        if   surplus > 0: return -max(0, surplus - len(removes))
        elif surplus < 0: return -min(0, surplus + len(builds) + waives)
        return 0
    def missing_orders(self, phase, nation=None):
        ''' Returns the MIS message for the power,
            or None if no orders are required.
            Either nation or the default nation must be a Power object.
            
            # Basic check
            >>> italy = standard_map.powers[ITA]
            >>> orders = OrderSet(italy)
            >>> print orders.missing_orders(Turn.build_phase)
            None
            
            # Crazy setup:
            # Venice is already holding,
            # Rome is dislodged and must retreat to either Tuscany or Apulia,
            # and Tunis is vacant but controlled by Italy.
            >>> orders.add(HoldOrder(standard_map.spaces[VEN].unit))
            >>> standard_map.spaces[ROM].unit.retreat([APU, TUS])
            >>> italy.centers.append(TUN)
            
            # Test various phases
            >>> print orders.missing_orders(Turn.move_phase)
            MIS ( ITA FLT NAP ) ( ITA AMY ROM )
            >>> print orders.missing_orders(Turn.retreat_phase)
            MIS ( ITA AMY ROM MRT ( APU TUS ) )
            >>> print orders.missing_orders(Turn.build_phase)
            MIS ( -1 )
            
            # Restore original map
            >>> standard_map.restart()
        '''#'''
        power = nation or self.default
        if phase == Turn.move_phase:
            result = [unit.key for unit in power.units
                if not self.get_order(unit)]
            if result: return MIS % result
        elif phase == Turn.retreat_phase:
            result = [unit for unit in power.units
                if unit.dislodged and not self.get_order(unit)]
            if result: return MIS % result
        elif phase == Turn.build_phase:
            surplus = -self.builds_remaining(power)
            if surplus: return MIS(surplus)
        else: raise NotImplementedError
        return None
    def complete_set(self, board):
        ''' Fills out the order set with default orders for the phase.
            Assumes that all orders in the set are valid.
        '''#'''
        phase = board.current_turn.phase()
        if phase == Turn.move_phase:
            for unit in board.units:
                if not self.get_order(unit):
                    self.add(HoldOrder(unit), unit.nation)
        elif phase == Turn.retreat_phase:
            for unit in board.units:
                if unit.dislodged and not self.get_order(unit):
                    self.add(DisbandOrder(unit), unit.nation)
        elif phase == Turn.build_phase:
            for power in board.powers.itervalues():
                builds = self.builds_remaining(power)
                if builds > 0:   self.waive(power, builds)
                elif builds < 0: self.default_removes(-builds, power, board)
        else: raise UserWarning, 'Unknown phase %d' % phase
    def default_removes(self, surplus, power, board):
        units = power.farthest_units(board.distance)
        while surplus > 0 and units:
            unit = units.pop(0)
            if not self.has_key(unit.coast.key):
                self.add(RemoveOrder(unit), power)
                surplus -= 1
