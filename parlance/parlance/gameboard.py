r'''Parlance gameboard classes
    Copyright (C) 2004-2008  Eric Wald
    
    This module defines classes to represent parts of the Diplomacy game.
    These are intended to be general-purpose; in particular, they should not
    be tied to any one particular bot or server algorithm.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

from itertools import chain, count
from pkg_resources import split_sections

from config      import Configuration, VerboseObject, judges, parse_file
from functions   import Comparable, Immutable, Infinity, all, any, defaultdict
from language    import Message, Representation, Token, protocol
from tokens import AMY, AUT, FAL, FLT, MDF, MRT, NOW, SCO, SPR, SUM, UNO, WIN

def location_key(unit_type, loc):
    if isinstance(loc, Token): return (unit_type, loc,    None)
    else:                      return (unit_type, loc[0], loc[1])

class Variant(object):
    r'''Representation of a map or rule variant
        - name         The name of the variant itself
        - mapname      The name to send in MAP messages
        - description  Brief description for help lists
        - ownership    The initial supply center ownerships
        - position     The initial unit positions
        - seasons      The sequence of seasons in a year
        - provinces    A mapping of province names
        - borders      A mapping of province borders
        - powers       A mapping of power names
        - judge        The Judge class used for adjudication
        - rep          The representation dictionary
    '''#"""#'''
    
    def __init__(self, name, rep=None, filename=None):
        self.name = name
        self.mapname = name
        self.description = ""
        self.provinces = {}
        self.ownership = {}
        self.position = {}
        self.borders = {}
        self.powers = {}
        self.homes = {}
        self.judge = "standard"
        self.start = (SPR, 0)
        self.seasons = (SPR, SUM, FAL, AUT, WIN)
        self.rep = rep or protocol.default_rep
        
        if filename:
            parse_file(filename, self.parse)
    
    def mdf(self):
        centers = []
        powers = []
        seen = []
        for name in self.homes:
            power = self.rep[name]
            if power is not UNO:
                powers.append(power)
            
            homes = [self.rep[prov] for prov in self.homes[name]]
            centers.append([power] + homes)
            seen.extend(homes)
        
        provs = []
        borders = []
        for name in sorted(self.borders):
            prov = self.rep[name]
            if prov not in seen:
                provs.append(prov)
            
            boundaries = [prov]
            adjacencies = self.borders[name]
            for item in adjacencies:
                boundary = self.rep.translate(adjacencies[item])
                boundaries.append([item] + boundary)
            borders.append(boundaries)
        
        return MDF (powers) (centers, provs) (borders)
    
    def sco(self):
        msg = +SCO
        for name in sorted(self.ownership):
            power = self.rep[name]
            centers = [self.rep[prov] for prov in self.ownership[name]]
            msg = msg(power, *centers)
        return msg
    
    def now(self):
        msg = NOW(self.start)
        for name in sorted(self.position):
            power = self.rep[name]
            for unit in self.position[name]:
                bits = [self.rep[prov] for prov in unit.split()]
                if len(bits) == 2:
                    site = bits[1]
                elif len(bits) == 3:
                    site = (bits[1], bits[2])
                else:
                    raise ValueError("Invalid unit spec: %r" % unit)
                msg = msg(power, bits[0], site)
        return msg
    
    def tokens(self):
        cats = defaultdict(list)
        for prov in sorted(self.borders):
            # Inland_non-SC = 0x50
            # Inland_SC = 0x51
            # Sea_non-SC = 0x52
            # Sea_SC = 0x53
            # Coastal_non-SC = 0x54
            # Coastal_SC = 0x55
            # Bicoastal_non-SC = 0x56
            # Bicoastal_SC = 0x57
            num = 0x5000
            keys = list(self.borders[prov])
            if len(keys) > 2:
                # Yes, we should probably look for coastline specs,
                # but this works for anything in the current variants.
                num += 0x0600
            elif AMY not in keys:
                num += 0x0200
            elif FLT in keys:
                num += 0x0400
            
            if any(prov in self.homes[power] for power in self.homes):
                num += 0x0100
            cats[num].append(prov)
        
        numbers = {}
        index = count()
        for cat in sorted(cats):
            for prov in cats[cat]:
                numbers[cat + index.next()] = prov
        
        for index, power in enumerate(sorted(self.homes)):
            if power != "UNO":
                numbers[0x4100 + index] = power
        
        return Representation(numbers, protocol.default_rep)
    
    def new_judge(self, options):
        return judges[self.judge](self, options)
    
    def parse(self, stream):
        "Collects information file from a configuration file."
        for section, lines in split_sections(stream):
            if section:
                parse = getattr(self, "parse_"+section)
                for line in lines:
                    parse(*line.split("=", 1))
        
        if self.position and not self.ownership:
            # Base the default starting ownership on the starting position.
            # This is more often the case than starting with all home centers.
            homes = set(p for power in self.homes for p in self.homes[power])
            for name in self.position:
                owned = []
                for unit in self.position[name]:
                    province = unit.split()[1]
                    if province in homes:
                        homes.remove(province)
                        owned.append(province)
                owned.sort()
                self.ownership[name] = owned
            self.ownership["UNO"] = list(sorted(homes))
    
    def parse_variant(self, key, value):
        if key in ("name", "mapname", "description", "judge"):
            setattr(self, key, value)
        elif key == "start":
            self.start = tuple(self.rep.translate(value))
    
    def parse_powers(self, key, value):
        if not value:
            self.powers[key] = (key, key)
        elif ',' in value:
            self.powers[key] = tuple(name.strip()
                for name in value.split(',', 1))
        else:
            self.powers[key] = (value, value)
    
    def parse_provinces(self, key, value):
        self.provinces[key] = value or key
    
    def parse_homes(self, key, value):
        self.homes[key] = [s.strip() for s in value.split(',') if s.strip()]
    
    def parse_ownership(self, key, value):
        self.ownership[key] = [s.strip() for s in value.split(',') if s.strip()]
    
    def parse_positions(self, key, value):
        self.position[key] = [s.strip() for s in value.split(',') if s.strip()]
    
    def parse_borders(self, key, value):
        sites = {}
        for spec in value.split(","):
            items = spec.split()
            if items:
                bits = iter(items)
                first = bits.next()
                try:
                    site = self.rep[first]
                except KeyError:
                    if first[0] == "(":
                        second = bits.next()
                        site = (self.rep[first[1:]], self.rep[second[:-1]])
                
                provs = str.join(" ", bits)
                sites[site] = provs
        self.borders[key] = sites


class Map(VerboseObject):
    ''' The map for the game, with various notes.
        Variables:
            - name:     The name used to request this map
            - valid:    Whether the map has been correctly loaded
            - powers:   A map of Powers in the game (Token -> Power)
            - spaces:   A map of Provinces (Token -> Province)
            - coasts:   A map of Coasts ((unit,province,coast) -> Coast)
            - neutral:  A Power representing the neutral supply centers
    '''#'''
    
    def __init__(self, variant):
        ''' Initializes the map from a Variant instance.'''
        self.__super.__init__()
        self.powers  = {}
        self.variant = variant
        self.name    = variant.mapname
        self.prefix  = variant.name + ' map'
        season, year = variant.start
        self.current_turn = Turn(season, year, variant.seasons)
        self.valid = variant.borders and not self.define(variant.mdf())
        if self.valid: self.restart()
    def __str__(self): return "Map(%r)" % self.name
    
    def define(self, message):
        ''' Attempts to create a map from an MDF message.
            Returns a string indicating a failure reason,
            which is empty if creation succeeded.
            Note: This routine does not set self.valid.
        '''#'''
        power_names = self.variant.powers
        province_names = self.variant.provinces
        
        (mdf, powers, provinces, adjacencies) = message.fold()
        (centres, non_centres) = provinces
        pow_homes = {}
        prov_homes = {}
        for dist in centres:
            pow_list = dist.pop(0)
            if pow_list == UNO:
                for prov in dist:
                    if prov_homes.has_key(prov):
                        return 'Supply center %s listed as both owned and unowned' % str(prov)
                    prov_homes[prov] = []
            else:
                if not isinstance(pow_list, list): pow_list = [pow_list]
                for country in pow_list:
                    pow_homes.setdefault(country, []).extend(dist)
                for prov in dist:
                    prov_homes.setdefault(prov, []).extend(pow_list)
        
        pows = {}
        for country, homes in pow_homes.iteritems():
            pows[country] = Power(country, homes,
                *power_names.get(country.text, ()))
        self.powers = pows
        self.neutral = Power(UNO, (),
            *power_names.get("UNO", ("Nobody", "Neutral")))
        
        provs = {}
        coasts = {}
        for adj in adjacencies:
            prov = adj.pop(0)
            is_sc = prov_homes.has_key(prov)
            non_sc = prov in non_centres
            if is_sc == non_sc:
                return 'Conflicting supply center designation for ' + str(prov)
            elif is_sc: home = prov_homes[prov]
            else:       home = None
            
            province = Province(prov, adj, home, province_names.get(prov.text))
            provs[prov] = province
            for coast in province.coasts: coasts[coast.key] = coast
        for key,coast in coasts.iteritems():
            for other in coast.borders_out:
                coasts[other].borders_in.add(key)
                provs[other[1]].borders_in.add(key[1])
        self.spaces = provs
        self.coasts = coasts
        
        for prov in provs.itervalues():
            if not prov.is_valid(): return 'Invalid province: ' + str(prov)
        else: return ''
    def restart(self):
        if self.variant.ownership: self.handle_SCO(self.variant.sco())
        if self.variant.position: self.handle_NOW(self.variant.now())
    
    # Information gathering
    def current_powers(self):
        ''' Returns a list of non-eliminated powers.
            >>> standard_map.powers[ITA].centers = []
            >>> current = standard_map.current_powers(); current.sort()
            >>> for country in current: print country,
            ... 
            AUS ENG FRA GER RUS TUR
        '''#'''
        return [token for token,power in self.powers.iteritems() if power.centers]
    def create_SCO(self):
        ''' Creates a supply center ownership message.
            >>> standard_map.handle_SCO(standard_sco)
            >>> old = standard_sco.fold()
            >>> new = standard_map.create_SCO().fold()
            >>> for item in old:
            ...     if item not in new: print Message(item)
            ... 
            >>> for item in new:
            ...     if item not in old: print Message(item)
            ... 
        '''#'''
        msg = +SCO
        powers = self.powers.values()
        powers.sort()
        for power in powers + [self.neutral]:
            if power.centers: msg = msg(power.key, *power.centers)
        return msg
    def create_NOW(self):
        ''' Creates a unit position message.
            >>> now = standard_now.fold()
            >>> then = standard_map.create_NOW().fold()
            >>> for item in then:
            ...     if item not in now: print Message(item)
            ... 
            >>> for item in now:
            ...     if item not in then: print Message(item)
            ... 
            >>> france = standard_map.powers[FRA]
            >>> kiel = standard_map.coasts[(AMY, KIE, None)]
            >>> fk = Unit(france, kiel)
            >>> fk.build()
            >>> fk.retreat([])
            >>> then = standard_map.create_NOW()
            >>> then = then.fold()
            >>> for item in then:
            ...     if item not in now: print Message(item)
            ... 
            FRA AMY KIE MRT ( )
            >>> for item in now:
            ...     if item not in then: print Message(item)
            ... 
            >>> fk.die()
        '''#'''
        units = sum([power.units for power in self.powers.values()], [])
        units.sort()
        return NOW(self.current_turn) % units
    def ordered_unit(self, nation, unit_spec, datc=None):
        ''' Finds a unit from its token representation.
            If the specified unit doesn't exist, returns a fake one.
            Accepts any combination of country, unit type, province,
            and coast tokens (even illegal ones); last takes precedence.
            
            >>> Russia = standard_map.powers[RUS]
            >>> print standard_map.ordered_unit(Russia, [RUS, FLT, SEV])
            RUS FLT SEV
            
            # Finds an existing unit, if possible
            >>> print standard_map.ordered_unit(Russia, [RUS, STP])
            RUS FLT ( STP SCS )
            >>> unit = standard_map.ordered_unit(Russia, [MOS])
            >>> print unit
            RUS AMY MOS
            >>> unit.exists()
            True
            >>> print standard_map.ordered_unit(Russia, [BUD])
            AUS AMY BUD
            
            # Country and unit type can be guessed, but only if unambiguous 
            >>> unit = standard_map.ordered_unit(Russia, [AMY, UKR])
            >>> print unit
            RUS AMY UKR
            >>> unit.exists()
            False
            >>> print standard_map.ordered_unit(Russia, [BLA])
            RUS FLT BLA
            >>> unit = standard_map.ordered_unit(Russia, [ARM])
            >>> print unit.coast.unit_type
            None
            >>> unit.exists()
            False
            
            # Will not correct unambiguously wrong orders unless asked
            >>> unit = standard_map.ordered_unit(Russia, [RUS, (STP, NCS)])
            >>> print unit
            RUS FLT ( STP NCS )
            >>> unit.exists()
            False
            >>> class datc(object):
            ...     datc_4b5 = 'b'
            >>> unit = standard_map.ordered_unit(Russia, [RUS, (STP, NCS)], datc)
            >>> print unit
            RUS FLT ( STP SCS )
            >>> unit.exists()
            True
        '''#'''
        # Collect specifications
        country = unit_type = coastline = province = None
        for token in Message(unit_spec):
            if token.is_power():
                country = self.powers.get(token) or Power(token, [])
            elif token.is_province():
                province = self.spaces.get(token) or Province(token, [], None)
            elif token.is_coastline(): coastline = token
            elif token.is_unit_type(): unit_type = token
        if not province:
            raise ValueError, 'Missing province in unit spec: %s' % Message(unit_spec)
        
        # Try to match all specs, but without ambiguity
        unit = None
        for item in province.units:
            if unit_type and item.coast.unit_type != unit_type: continue
            if country and item.nation != country: continue
            if (coastline and item.coast.coastline != coastline
                    and not (datc and datc.datc_4b5 == 'b')):
                continue
            
            if unit:
                if item.dislodged == unit.dislodged:
                    if item.nation == unit.nation:
                        unit = country = nation = None
                        break
                    elif item.nation == nation: unit = item
                    elif unit.nation != nation:
                        unit = country = nation = None
                        break
                elif item.dislodged: unit = item
            else: unit = item
        if not unit:
            coast = self.coasts.get((unit_type, province.key, coastline))
            if not coast:
                for item in province.coasts:
                    if unit_type and item.unit_type != unit_type: continue
                    if item.coastline != coastline: continue
                    if coast:
                        coast = Coast(None, province, coastline, [])
                        break
                    coast = item
                if not coast: coast = Coast(unit_type, province, coastline, [])
            unit = Unit(country or nation, coast)
        self.log_debug(20, 'ordered_unit(%s, %s) -> %s',
            nation, unit_spec, unit)
        return unit
    def ordered_coast(self, unit, coast_spec, datc):
        ''' Finds a coast from its maybe_coast representation.
            If the specified coast doesn't exist, returns a fake one.
            Uses the unit's unit_type, and (depending on options)
            its location to disambiguate bicoastal destinations.
        '''#'''
        # Collect specifications
        unit_type = unit.coast.unit_type
        coastline = province = None
        for token in Message(coast_spec):
            if token.is_province():
                province = self.spaces.get(token) or Province(token, [], None)
            elif token.is_coastline(): coastline = token
        if not province:
            raise ValueError('Missing province in coast spec: %s'
                % Message(coast_spec))
        
        # Try to match all specs, but without ambiguity
        coast = self.coasts.get((unit_type, province.key, coastline))
        if coast:
            if datc.datc_4b3 == 'a' and not unit.can_move_to(coast):
                # Wrong coast specified; change it to the right one.
                possible = [c for c in province.coasts
                        if c.key in unit.coast.borders_out
                        and c.unit_type == unit_type]
                if len(possible) == 1: coast = possible[0]
        else:
            possible = []
            for item in province.coasts:
                if unit_type and item.unit_type != unit_type: continue
                if coastline and item.coastline != coastline: continue
                possible.append(item)
            if unit_type and datc.datc_4b6 == 'b' and not possible:
                possible = [place for place in province.coasts
                    if place.unit_type == unit_type]
            self.log_debug(20, 'Possible coasts for %s: %r of %r',
                unit_type, possible, province.coasts)
            if len(possible) == 1: coast = possible[0]
            elif possible:
                # Multiple coasts; see whether our location disambiguates.
                # Note that my 4.B.2 "default" coast is the possible one.
                nearby = [c for c in possible if c.key in unit.coast.borders_out]
                if len(nearby) == 1 and datc.datc_4b2 != 'c': coast = nearby[0]
                elif nearby and datc.datc_4b1 == 'b': coast = nearby[0]
            if not coast:
                coast = Coast(None, province, coastline, [])
        self.log_debug(20, 'ordered_coast(%s, %s) -> %s (%s, %s, %s, %s)',
            unit, coast_spec, coast, datc.datc_4b1,
            datc.datc_4b2, datc.datc_4b3, datc.datc_4b6)
        return coast
    #@Memoize  # Cache results; doesn't work for list args
    def distance(self, coast, provs):
        ''' Returns the coast's distance from the nearest of the provinces,
            particularly for use in determining civil disorder retreats.
        '''#'''
        # Todo: Count army and fleet movements differently?
        result = 0
        rank = seen = [coast.province.key]
        while rank:
            if any(place in provs for place in rank): return result
            new_rank = []
            for here in rank:
                new_rank.extend([key
                    for key in self.spaces[here].borders_out
                    if key not in seen and key not in new_rank
                ])
            seen.extend(new_rank)
            rank = new_rank
            result += 1
        # Inaccessible island
        return Infinity
    def units(self):
        return chain(*[country.units for country in self.powers.values()])
    units = property(fget=units)
    
    # Message handlers
    def handle_MDF(self, message):
        ''' Handles the MDF command, loading province information.'''
        self.valid = not self.define(message)
    def handle_SCO(self, message):
        ''' Handles the SCO command, loading center ownership information.
            >>> standard_map.handle_SCO(standard_sco)
            >>> for sc in standard_map.neutral.centers: print sc,
            ... 
            BEL BUL DEN GRE HOL NWY POR RUM SER SPA SWE TUN
            >>> for sc in standard_map.powers[ENG].centers: print sc,
            ... 
            EDI LON LVP
            >>> print standard_map.spaces[NWY].owner
            Nobody
            >>> print standard_map.spaces[EDI].owner
            England
        '''#'''
        if self.valid:
            sc_dist = message.fold()[1:]
            on_board = set(self.current_powers())
            for country in [self.neutral] + self.powers.values():
                country.centers = []
            for dist in sc_dist:
                country = dist.pop(0)
                on_board.discard(country)
                power = self.powers.get(country, self.neutral)
                power.centers = dist
                for prov in dist: self.spaces[prov].owner = power
            
            year = self.current_turn.year
            for country in on_board:
                power = self.powers[country]
                if not power.centers: power.eliminated = year
    def handle_NOW(self, message):
        ''' Handles the NOW command, loading turn and unit information.
            May complain about unexpected units.
            
            >>> standard_map.handle_NOW(standard_now)
            >>> English = standard_map.powers[ENG].units; English.sort()
            >>> print ' '.join(['( %s )' % unit for unit in English])
            ( ENG AMY LVP ) ( ENG FLT EDI ) ( ENG FLT LON )
        '''#'''
        folded = message.fold()
        if self.valid:
            try: self.current_turn = self.current_turn.next(*folded[1])
            except ValueError, err:
                self.log_debug(7, 'Turn (%s) complained about %s: %s',
                        self.current_turn, folded[1], err.args)
                season, year = folded[1]
                seasons = self.current_turn.seasons
                if seasons and season in seasons:
                    self.current_turn = Turn(season, year, seasons,
                            list(seasons).index(season))
                else: self.current_turn = Turn(season, year)
            for prov in self.spaces.itervalues(): prov.units = []
            for country in self.powers.itervalues(): country.units = []
            for unit_spec in folded[2:]:
                (nation,unit_type,loc) = unit_spec[0:3]
                key = location_key(unit_type,loc)
                coast = self.coasts[key]
                power = self.powers[nation]
                unit = Unit(power, coast)
                unit.build()
                if len(unit_spec) > 3: unit.retreat(unit_spec[4])
    def advance(self):
        self.current_turn = self.current_turn.next()
        return self.current_turn
    def adjust_ownership(self):
        ''' Lets units take over supply centers they occupy.
            Returns a list of countries that gained supply centers.
            
            >>> then = Message(standard_now[:])
            >>> then[then.index(LON) - 2] = RUS
            >>> then[then.index(STP) - 3] = ENG
            >>> standard_map.handle_NOW(then)
            >>> countries = standard_map.adjust_ownership()
            >>> ENG == standard_map.spaces[STP].owner
            True
            >>> RUS == standard_map.spaces[LON].owner
            True
            
            # Restore original map
            >>> standard_map.restart()
        '''#'''
        net_growth = defaultdict(int)
        for unit in self.units:
            power = unit.nation
            loser = unit.takeover()
            if loser:
                power.eliminated = False
                net_growth[power.key] += 1
                net_growth[loser.key] -= 1
                if not loser.centers:
                    loser.eliminated = self.current_turn.year
        return [token for token,net in net_growth.iteritems() if net > 0]


class Turn(Comparable, Immutable):
    ''' Represents a single turn, consisting of season and year.
        Turns are immutable and hashable, so they can be used as keys.
        Caveat:  When using custom season lists, do not try to compare
        or hash Turns made without a seasons parameter; results will
        probably look fine, but may be subtly wrong.
        
        The following are also available, and may be ANDed with an order token
        to see whether it is valid in the current phase:
            - Turn.move_phase
            - Turn.retreat_phase
            - Turn.build_phase
    '''#'''
    class TurnOptions(Configuration):
        __section__ = 'syntax'
        __options__ = (
            # It would be nice if the tokens themselves contained this info.
            ('move_phases', list, ('SPR','FAL'), 'move phases',
                'Tokens that indicate movement phases'),
            ('retreat_phases', list, ('SUM','AUT'), 'retreat phases',
                'Tokens that indicate retreat phases'),
            ('build_phases', list, ('WIN',), 'build phases',
                'Tokens that indicate build phases'),
            
            # Todo: Check that these are powers of two
            ('move_phase_bit', int, 0x20, 'move order mask',
                'Bit that indicates movement phase in order token numbers.'),
            ('retreat_phase_bit', int, 0x40, 'retreat order mask',
                'Bit that indicates retreat phase in order token numbers.'),
            ('build_phase_bit', int, 0x80, 'build order mask',
                'Bit that indicates build phase in order token numbers.'),
        )
        
        def __init__(self):
            self.__super.__init__()
            
            # Masks to determine whether an order is valid during a given phase
            self.phase_mask = (self.move_phase_bit |
                    self.retreat_phase_bit | self.build_phase_bit)
            self.index_mask = 0xFF ^ self.phase_mask
            
            self.phases = {}
            for name in self.move_phases:
                self.phases[protocol.base_rep[name]] = self.move_phase_bit
            for name in self.retreat_phases:
                self.phases[protocol.base_rep[name]] = self.retreat_phase_bit
            for name in self.build_phases:
                self.phases[protocol.base_rep[name]] = self.build_phase_bit
    
    options = TurnOptions()
    move_phase    = options.move_phase_bit
    retreat_phase = options.retreat_phase_bit
    build_phase   = options.build_phase_bit
    
    # Required by the Immutable interface
    __slots__ = ('season', 'year', 'seasons', 'index', 'key')
    
    def __init__(self, season, year, seasons=None, index=None):
        self.season = season
        self.year = int(year)
        
        if seasons is None:
            self.seasons = None
            self.index = season.number & self.options.index_mask
        else:
            self.seasons = tuple(seasons)
            if index is None:
                l = list(self.seasons)
                count = l.count(season)
                if count == 1: self.index = l.index(season)
                elif count:
                    raise ValueError("Turn index required for ambiguous season")
                else: raise ValueError("Turn season not in the list of seasons")
            elif season is self.seasons[index]:
                self.index = int(index)
            else: raise ValueError("Turn season and index don't match")
        self.key = (self.year, self.index)
    
    def next(self, season=None, year=None):
        ''' Creates a Turn for the next phase, or the next specified phase.
            Refuses to return this or past phases, if it can tell,
            but tries to work correctly in the face of multiple identical
            seasons per year (such as in the baseball variant).
        '''#'''
        if season:
            if self.seasons:
                index = self.index + 1
                if year is None:
                    cycle = self.seasons[index:] + self.seasons[:index]
                    index += list(cycle).index(season)
                    if index >= len(cycle):
                        index %= len(cycle)
                        year = self.year + 1
                    else: year = self.year
                elif year == self.year:
                    try: index += list(self.seasons[index:]).index(season)
                    except ValueError:
                        if season in self.seasons:
                            raise ValueError('Trying to go back in time')
                        else: raise ValueError('Season not in season list')
                elif year > self.year:
                    index = list(self.seasons).index(season)
                else: raise ValueError('Trying to go back in time')
            elif year is not None:
                # We could try to check for going back within the current year,
                # but I'm not willing to make assumptions on this index.
                index = season.number & self.options.index_mask
                if year < self.year:
                    raise ValueError('Trying to go back in time')
            else:
                # Hope the season tokens are at least numbered in order
                index = season.number & self.options.index_mask
                if index > self.index: year = self.year
                else: year = self.year + 1
        elif year is not None:
            if year == self.year:
                if self.seasons:
                    index = self.index + 1
                    season = self.seasons[index]
                else: raise ValueError('Unknown next season')
            elif year > self.year:
                season = self.season
                index = self.index
            else: raise ValueError('Trying to go back in time')
        elif self.seasons:
            index = self.index + 1
            if index == len(self.seasons):
                index = 0
                year = self.year + 1
            else: year = self.year
            season = self.seasons[index]
        else: raise ValueError('Unknown next season')
        return Turn(season, year, self.seasons, index)
    
    def __str__(self):
        names = {
            AUT: 'Autumn',
            FAL: 'Fall',
            SPR: 'Spring',
            SUM: 'Summer',
            WIN: 'Winter',
        }
        season = names.get(self.season, self.season.text)
        return '%s %s' % (season, self.year)
    def tokenize(self): return Message(self.season, self.year)
    
    def phase(self, season=None):
        ''' Returns the phase bit of the season, or of the turn,
            as one of the values move_phase, retreat_phase, or build_phase.
            
            >>> t = Turn(SUM, 1901); print t, hex(t.phase())
            Summer 1901 0x40
            >>> t.phase() == Turn.retreat_phase
            True
        '''#'''
        if not season: season = self.season
        default = season.number & self.options.phase_mask
        return self.options.phases.get(season, default)
    def __cmp__(self, other):
        ''' Compares Turns with each other, or with their keys.
            >>> ts = Turn(SPR, 1901)
            >>> tf = Turn(FAL, 1901)
            >>> cmp(ts, tf)
            -1
            >>> cmp(tf, ts.key)
            1
            >>> cmp(tf, tf.key)
            0
        '''#'''
        return cmp(self.key, other)
    def __hash__(self): return hash(self.key)


class Power(Comparable):
    ''' Represents a country in the game.
        Variables:
            - key        the Token that represents this power
            - homes      list of Tokens for home supply centers
            - centers    list of Tokens for supply centers controlled
            - units      list of Units owned
            - eliminated year of elimination, or False if still on the board
    '''#'''
    def __init__(self, token, home_scs, name=None, adjective=None):
        self.key        = token
        self.name       = name or token.text
        self.homes      = home_scs
        self.units      = []
        self.centers    = []
        self.adjective  = adjective or self.name
        self.eliminated = False
    def __cmp__(self, other):
        ''' Allows direct comparison of Powers and tokens.
            >>> country = Power(ENG, [])
            >>> country == ENG
            True
            >>> country == Power(ENG, [NWY])
            True
            >>> pows = [Power(UNO, []), Power(FRA, [PAR]), None, country]
            >>> pows.sort()
            >>> print ' '.join([str(item) for item in pows])
            ENG FRA UNO None
            
            # Changed by making Token a subclass of int:
            >>> country == Token('Eng', 0x4101)
            True
        '''#'''
        if other is None:              return -1
        elif isinstance(other, Token): return cmp(self.key, other)
        elif isinstance(other, Power): return cmp(self.key, other.key)
        else: return NotImplemented 
    def tokenize(self): return [self.key]
    def __str__(self): return self.name
    def __repr__(self): return 'Power(%s, %s)' % (self.key, self.homes)
    
    def surplus(self):
        ''' Returns the number of unsupplied units owned by the power.
            Usually, this is the number of units that must be removed.
            Negative numbers indicate that builds are in order.
            
            >>> italy = standard_map.powers[ITA]
            >>> print italy.surplus()
            0
            >>> italy.centers = [ROM]; print italy.surplus()
            2
            >>> italy.centers = [ROM, TUN, VEN, NAP, GRE]; print italy.surplus()
            -2
            >>> italy.centers = [ROM, VEN, NAP]
        '''#'''
        return len(self.units) - len(self.centers)
    def farthest_units(self, distance):
        ''' Returns a list of units in order of removal preference,
            for a power that hasn't ordered enough removals.
        '''#'''
        # Todo: the Chaos variant should use self.centers instead of self.homes
        dist_list = [(
            -distance(unit.coast, self.homes), # Farthest unit
            -unit.coast.unit_type.number,      # Fleets before armies
            unit.coast.province.key.text,      # First alphabetically
            unit
        ) for unit in self.units]
        dist_list.sort()
        return [item[3] for item in dist_list]


class Province(Comparable):
    ''' Represents a space of the board.
        Variables:
            - key          The Token representing this province
            - homes        A list of powers for which this is a Home Supply Center
            - coasts       A list of Coasts
            - owner        The power that controls this supply center
            - borders_in   The provinces that can reach this one
            - borders_out  The provinces that can be reached from here
            - units        A list of Units here
    '''#'''
    def __init__(self, token, adjacencies, owners, name=None):
        self.key         = token
        self.name        = name or token.text
        self.homes       = owners
        self.coasts      = []
        self.units       = []
        self.owner       = None
        self.borders_in  = set()
        self.borders_out = set()
        for unit_adjacency in adjacencies:
            unit = unit_adjacency.pop(0)
            if isinstance(unit, list):
                coast = unit[1]
                unit_type = unit[0]
            else:
                coast = None
                unit_type = unit
            new_coast = Coast(unit_type, self, coast, unit_adjacency)
            self.coasts.append(new_coast)
            self.borders_out.update([key[1] for key in new_coast.borders_out])
    
    def is_supply(self): return self.homes is not None
    def is_valid(self):
        if self.homes and not self.key.is_supply(): return False
        if not self.coasts: return False
        return all(coast.is_valid() for coast in self.coasts)
    def is_coastal(self):
        if self.key.is_coastal(): return location_key(AMY, self.key)
        else: return None
    def can_convoy(self): return self.key.category_name() in ('Sea SC', 'Sea non-SC')
    def __str__(self): return self.name
    def __repr__(self): return "Province('%s')" % self.name
    def tokenize(self): return [self.key]
    def __cmp__(self, other):
        ''' Compares Provinces with each other, or with their tokens.
            >>> LVP == standard_map.spaces[LVP]
            True
        '''#'''
        if isinstance(other, Token):      return cmp(self.key, other)
        elif isinstance(other, Province): return cmp(self.key, other.key)
        else: return NotImplemented 
    def exists(self): return bool(self.coasts)
    
    @property
    def unit(self): return self.units and self.units[0] or None


# Todo: Consider "Site" for this.
class Coast(Comparable, VerboseObject):
    ''' A place where a unit can be.
        Each Province has one per unit type allowed there,
        with extra fleet Coasts for multi-coastal provinces.
        
        Variables:
            - unit_type    The type of unit (AMY or FLT)
            - province     The Province
            - coastline    The coast represented (SCS, etc.), or None
            - borders_in   A list of keys for coasts which could move to this one
            - borders_out  A list of keys for coasts to which this unit could move
            - key          A tuple that uniquely specifies this coast
            - maybe_coast  (province, coast) for bicoastal provinces, province for others
    '''#'''
    def __init__(self, unit_type, province, coastline, adjacencies):
        # Warning: a fake Coast can have a unit_type of None.
        self.__super.__init__()
        self.unit_type   = unit_type
        self.coastline   = coastline
        self.province    = province
        self.key         = (unit_type, province.key, coastline)
        self.borders_in  = set()
        self.borders_out = [location_key(unit_type, adj) for adj in adjacencies]
        if coastline:
            self.maybe_coast = (province.key, coastline)
            self.text = '(%s (%s %s))' % (unit_type, province.key, coastline)
            self.name = province.name + self.coast_suffix()
        else:
            self.maybe_coast = province.key
            self.text = '(%s %s)' % (unit_type, province.key)
            self.name = province.name
        self.prefix = '%s %s' % (self.type_name(), self.name)
    
    def tokenize(self):
        return Message([self.unit_type, self.maybe_coast])
    def __cmp__(self, other):
        if isinstance(other, Coast): return cmp(self.key, other.key)
        else: return NotImplemented
    def __str__(self): return self.text
    def __repr__(self): return 'Coast(%s, %s, %s)' % self.key
    
    def coast_suffix(self):
        if self.coastline:
            abbr = self.coastline.text.lower().rstrip('s')
            vert = horiz = ''
            if 'n' in abbr: vert = 'north'
            if 's' in abbr: vert = 'south'
            if 'e' in abbr: horiz = 'east'
            if 'w' in abbr: horiz = 'west'
            #coast = ' (%s)' % abbr
            coast = ' (%s%s coast)' % (vert, horiz)
        else: coast = ''
        return coast
    def type_name(self):
        "Text representation of the unit type"
        token = self.unit_type
        if   token is AMY: return 'Army'
        elif token is FLT: return 'Fleet'
        elif token:        return token.text
        else:              return ''
    
    # Confirmation queries
    def is_valid(self):
        category = self.province.key.category_name().split()[0]
        if self.coastline:
            return (category == 'Bicoastal' and self.unit_type == FLT
                and self.coastline.category_name() == 'Coasts')
        elif category == 'Sea':       return self.unit_type == FLT
        elif category == 'Inland':    return self.unit_type == AMY
        elif category == 'Bicoastal': return self.unit_type == AMY
        elif category == 'Coastal':   return self.unit_type in (AMY, FLT)
        else:                         return False
    def exists(self): return self.unit_type and self in self.province.coasts
    def convoy_routes(self, dest, board):
        ''' Collects possible convoy routes.
            dest must be a Province.
            Each route is a tuple of Province instances.
            Now collects only routes that currently have fleets.
        '''#'''
        self.log_debug(11, 'Collecting convoy routes to %s', dest.name)
        path_list = []
        if self.province != dest and dest.is_coastal():
            possible = [(p,)
                for p in [board.spaces[key] for key in self.province.borders_out]
                if p.can_convoy() and len(p.units) > 0
            ]
            while possible:
                route = possible.pop()
                self.log_debug(12, 'Considering %s',
                        ' -> '.join([prov.name for prov in route]))
                here = route[-1]
                if dest.key in here.borders_out: path_list.append(route)
                seen = [p.key for p in route]
                possible.extend([route + (p,)
                    for p in [board.spaces[key]
                        for key in here.borders_out
                        if key not in seen]
                    if p.can_convoy() and len(p.units) > 0
                ])
            # Sort shorter paths to the front, to speed up checking
            path_list.sort(key=len)
        self.log_debug(11, 'Routes found: %s', path_list)
        return path_list
    def matches(self, key):
        self.log_debug(20, 'matches(%s, %s)', self.key, key)
        return (self.key == key) or (self.unit_type is None
                and self.key[1] == key[1])


class Unit(Comparable):
    ''' A unit on the board.
        Technically, units don't track past state, but these can.
    '''#'''
    def __init__(self, nation, coast):
        # Warning: a fake Unit can have a nation of None.
        self.coast       = coast
        self.nation      = nation
        self.dislodged   = False
        self.retreats    = None
    
    # Representations
    def tokenize(self):
        result = Message(self.key)
        if self.dislodged: result.extend(MRT(self.retreats))
        return result
    def __str__(self): return str(Message(self))
    def __repr__(self): return 'Unit(%s, %r)' % (self.nation, self.coast)
    def __cmp__(self, other):
        if isinstance(other, Unit):
            return (cmp(self.nation, other.nation)
                    or cmp(self.coast, other.coast))
        else: return NotImplemented
    def key(self):
        return (self.nation and self.nation.key,
                self.coast and self.coast.unit_type,
                self.coast and self.coast.maybe_coast)
    key = property(fget=key)
    
    # Actions
    def move_to(self, coast):
        # Update the Provinces
        self.coast.province.units.remove(self)
        coast.province.units.append(self)
        
        # Update the Unit
        self.coast     = coast
        self.dislodged = False
        self.retreats  = None
    def retreat(self, retreats):
        self.dislodged   = True
        self.retreats    = retreats
    def build(self):
        self.nation.units.append(self)
        self.coast.province.units.append(self)
    def die(self):
        self.nation.units.remove(self)
        self.coast.province.units.remove(self)
    def takeover(self):
        ''' Takes control of the current space.
            If control of a supply center changes,
            returns the former controller.
        '''#'''
        prov = self.coast.province
        if prov.is_supply():
            former = prov.owner
            if former != self.nation:
                prov.owner = self.nation
                self.nation.centers.append(prov.key)
                former.centers.remove(prov.key)
                return former
        return None
    
    # Confirmation queries
    def can_move_to(self, place):
        #print '\tQuery: %s -> %s' % (self, place)
        if isinstance(place, Coast):
            # Check whether it can move to any coastline
            return any(place.matches(prov) for prov in self.coast.borders_out)
        else:
            # Assume a Province or province token
            return place.key in [key[1] for key in self.coast.borders_out]
        return False
    def can_convoy(self):
        return self.coast.unit_type == FLT and self.coast.province.can_convoy()
    def can_be_convoyed(self):
        return self.coast.unit_type == AMY and self.coast.province.is_coastal()
    def exists(self): return self in self.coast.province.units

