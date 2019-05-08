r'''Parlance language classes
    Copyright (C) 2004-2008  Eric Wald
    
    This module contains classes to convert messages between a Pythonic
    representation, the DAIDE message syntax, and the network protocol.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import re
from struct    import pack

from functions import Comparable, rindex
from config    import Configurable, VerboseObject, parse_file

__all__ = [
    'Message',
    'Token',
    'StringToken',
    'IntegerToken',
    'Representation',
    'protocol',
]

class Message(list):
    ''' Representation of a Diplomacy Message, as a list of Tokens.
        >>> m = Message(NOT, BRA, GOF, KET)
        >>> print m
        NOT ( GOF )
        >>> m[0]
        NOT
        >>> m[-5]
        Traceback (most recent call last):
            ...
        IndexError: list index out of range
    '''#'''
    
    def __init__(self, *message):
        ''' Creates a new message from a string or series.
            Mostly, this will be called by calling a token;
            for best results, don't use it directly.
            
            >>> str(Message(NOT, [GOF]))
            'NOT GOF'
            >>> str(Message((NOT, [GOF])))
            'NOT ( GOF )'
        '''#'''
        for item in message: list.extend(self, self.to_tokens(item))
    
    def fold(self):
        ''' Folds the token into a list, with bracketed sublists as lists.
            Also converts text and number tokens to strings and integers.
            This version takes about half the time for a map definition,
            but probably a bit longer than old_fold() for simple messages.
            
            >>> NOT(GOF).fold()
            [NOT, [GOF]]
            >>> Message().fold()
            []
            >>> NME('name')(-3).fold()
            [NME, ['name'], [-3]]
            >>> base_rep.translate('(()(()()))()').fold()
            [[[], [[], []]], []]
            >>> base_rep.translate('(()()))()(()').fold()
            Traceback (most recent call last):
                ...
            ValueError: unbalanced parentheses in folded Message
            >>> base_rep.translate('NOT ( GOF').fold()
            Traceback (most recent call last):
                ...
            ValueError: unbalanced parentheses in folded Message
        '''#'''
        complaint = 'unbalanced parentheses in folded Message'
        if self.count(BRA) != self.count(KET): raise ValueError, complaint
        series = self.convert()
        while BRA in series:
            k = series.index(KET)
            try: b = rindex(series[:k], BRA)
            except ValueError: raise ValueError, complaint
            series[b:k+1] = [series[b+1:k]]
        return series
    def convert(self):
        ''' Converts a Message into a list,
            with embedded strings and tokens converted into Python values.
            
            >>> NME('version')(-3).convert()
            [NME, BRA, 'version', KET, BRA, -3, KET]
        '''#'''
        result = []
        text = ''
        append = result.append
        for token in self:
            if token.is_text(): text += token.text
            else:
                if text: append(text); text = ''
                if token.is_integer(): append(token.value())
                else: append(token)
        if text: append(text)
        return result
    
    def __str__(self):
        ''' Returns a string representation of the message.
            >>> str(NOT(GOF))
            'NOT ( GOF )'
            >>> print Message((NME, ["I'm Me"]), '"Missing" field "name"')
            NME ( "I'm Me" ) """Missing"" field ""name"""
            >>> str(Message('name'))
            '"name"'
        '''#'''
        opts = protocol.base_rep.options
        quot = opts.quot_char
        escape = opts.output_escape
        squeeze = opts.squeeze_parens
        
        result = []
        in_text = False
        use_space = False
        
        for token in self:
            if token.is_text():
                if not in_text:
                    if use_space: result.append(' ')
                    else: use_space = True
                    result.append(quot)
                    in_text = True
                
                if token.text in (escape, quot): result.append(escape)
                result.append(token.text)
            else:
                if in_text:
                    result.append(quot)
                    in_text = False
                if use_space and not (squeeze and token is KET):
                    result.append(' ')
                use_space = not (squeeze and token is BRA)
                result.append(token.text)
        if in_text: result.append(quot)
        
        return str.join('', result)
    def __repr__(self):
        ''' Returns a string which can be used to reproduce the message.
            Note: Can get long, if used improperly.
            
            >>> eval(repr(NOT(GOF)))
            Message([NOT, [GOF]])
            >>> eval(repr(IAM(Token('STH', 0x4101))(42)))
            Message([IAM, [Token('STH', 0x4101)], [42]])
        '''#'''
        return 'Message(' + repr(self.fold()) + ')'
    def pack(self):
        ''' Produces a string of token numbers from a Message.
            >>> print map(lambda x: hex(ord(x)), NOT(GOF).pack())
            ['0x48', '0xd', '0x40', '0x0', '0x48', '0x3', '0x40', '0x1']
        '''#'''
        return pack('!' + 'H'*len(self), *map(int, self))
    def tokenize(self): return self
    
    # Formerly module methods, but only used in this class.
    @staticmethod
    def to_tokens(value, wrap=False):
        ''' Returns a list of Token instances based on a value.
            If wrap is true, lists and tuples will be wrapped in parentheses.
            (But that's meant to be used only by this method.)
            
            >>> Message.to_tokens(3)
            [IntegerToken(3)]
            >>> Message.to_tokens('YES')
            [StringToken('Y'), StringToken('E'), StringToken('S')]
            >>> Message.to_tokens('name')
            [StringToken('n'), StringToken('a'), StringToken('m'), StringToken('e')]
            >>> Message.to_tokens([3, 0, -3])
            [IntegerToken(3), IntegerToken(0), IntegerToken(-3)]
            >>> Message.to_tokens([3, 0, -3], True)
            [BRA, IntegerToken(3), IntegerToken(0), IntegerToken(-3), KET]
            >>> Message.to_tokens([+NOT, (GOF,)])
            [NOT, BRA, GOF, KET]
        '''#'''
        if hasattr(value, 'tokenize'):
            result = value.tokenize()
            if isinstance(result, list): return result
            else:
                raise TypeError('tokenize for %s returned non-list (type %s)' %
                        (value, result.__class__.__name__))
        elif isinstance(value, (int, float, long)): return [IntegerToken(value)]
        elif isinstance(value, str):
            return [StringToken(c) for c in value]
        elif wrap: return Message.wrap(value)
        else:
            try: return sum([Message.to_tokens(item, True) for item in value], [])
            except TypeError: raise TypeError, 'Cannot tokenize ' + str(value)
    @staticmethod
    def wrap(value):
        ''' Tokenizes the list and wraps it in a pair of brackets.
            >>> Message.wrap(GOF)
            [BRA, GOF, KET]
            >>> Message.wrap(NOT(GOF))
            [BRA, NOT, BRA, GOF, KET, KET]
            >>> Message.wrap('name')
            [BRA, StringToken('n'), StringToken('a'), StringToken('m'), StringToken('e'), KET]
        '''#'''
        return [BRA] + Message.to_tokens(value) + [KET]
    
    # Automatically translate new items into Tokens
    def append(self, value):
        ''' Adds a new token to the Message.
            >>> m = Message(NOT)
            >>> m.append(GOF)
            >>> m
            Message([NOT, GOF])
            >>> m.append('name')
            Traceback (most recent call last):
                ...
            KeyError: "unknown token 'name'"
            >>> m.append([3])
            Traceback (most recent call last):
                ...
            TypeError: list objects are unhashable
        '''#'''
        list.append(self, protocol.base_rep[value])
    def extend(self, value):
        ''' Adds a list of new tokens to the Message, without parentheses.
            >>> m = Message(NOT)
            >>> m.extend(GOF)
            >>> str(m)
            'NOT GOF'
            >>> m.extend('name')
            >>> str(m)
            'NOT GOF "name"'
            >>> m.extend([3])
            >>> str(m)
            'NOT GOF "name" 3'
        '''#'''
        list.extend(self, self.to_tokens(value))
    def __add__(self, other):
        ''' Adds the given Message or list at the end of this Message,
            translating list items into Tokens if necessary.
            Note: To add a single token, use "++".
            
            >>> print ((ALY(ENG, FRA) ++ VSS) + [[GER, ITA]])
            ALY ( ENG FRA ) VSS ( GER ITA )
        '''#'''
        return Message(list.__add__(self, other))
    def __iadd__(self, other): self.extend(other); return self
    
    def __call__(self, *args):
        ''' Makes the standard bracketing patterns legal Python.
            Unfortunately, multiple values in a single bracket need commas.
            
            >>> print NME ('name') ('version')
            NME ( "name" ) ( "version" )
            >>> print CCD (ENG) (SPR, 1901)
            CCD ( ENG ) ( SPR 1901 )
        '''#'''
        if len(args) == 1: return self + self.wrap(*args)
        else: return self + self.wrap(args)
    __and__ = __call__
    def __iand__(self, other):
        try:
            if len(other) == 1: other = other[0]
        except TypeError: pass
        list.extend(self, self.wrap(other)); return self
    def __mod__(self, other):
        ''' Wraps each element of a list individually,
            appending them to a copy of the message.
            
            >>> units = standard_now.fold()[5:8]
            >>> print NOW (FAL, 1901) % units
            NOW ( FAL 1901 ) ( ENG FLT EDI ) ( ENG FLT LON ) ( ENG AMY LVP )
        '''#'''
        return reduce(apply, [(item,) for item in other], self)
    
    def __setslice__(self, from_index, to_index, value):
        ''' Replaces a portion of the Message, with Tokens.
            >>> m = base_rep.translate('NOT ( GOF )')
            >>> m[1:3] = [YES, 34, 'name']
            >>> str(m)
            'NOT YES 34 "name" )'
            >>> m[-3:] = REJ
            >>> str(m)
            'NOT YES 34 "na" REJ'
        '''#'''
        try: list.__setslice__(self, from_index, to_index, self.to_tokens(value))
        except TypeError: raise TypeError, 'must assign list (not "%s") to slice' % type(value).__name__
    def __setitem__(self, index, value):
        ''' Replaces a single Token of the Message with another Token.
            >>> m = NOT(GOF)
            >>> m[2] = DRW; print m
            NOT ( DRW )
            >>> m[-1] = 42; print m
            NOT ( DRW 42
            >>> m[3]
            IntegerToken(42)
            >>> m[-2] = [YES, KET]
            Traceback (most recent call last):
                ...
            TypeError: list objects are unhashable
        '''#'''
        list.__setitem__(self, index, protocol.base_rep[value])
    def insert(self, index, value):
        ''' Inserts a single token into the Message.
            >>> m = HUH(WHT)
            >>> m.insert(2, ERR)
            >>> str(m)
            'HUH ( ERR WHT )'
            >>> m.insert(3, [Token('ENG', 0x4101), Token('FRA', 0x4102)])
            Traceback (most recent call last):
                ...
            TypeError: list objects are unhashable
        '''#'''
        list.insert(self, index, protocol.base_rep[value])


class _integer_Token(int):
    ''' Core for the Token class, based on an integer.
        Advantages over the tuple-based class:
            - Doesn't confuse string interpolation
            - Slightly faster
        Possible disadvantages:
            - Easier to use improperly in arithmetic
            - Compares equal to integers and tokens with different names
            - Sorts by number, not text; particularly relevant for provinces
            - Token 0x0000 is a false value
    '''#'''
    
    # Use __slots__ to save memory, and to maintain immutability
    __slots__ = ('text')
    
    def __new__(klass, key):
        ''' Converts the token to an integer,
            resulting in the numerical DCSP value.
            
            # Moved here from the old __int__() method
            >>> int(YES)
            18460
            >>> int(Token('PAR', 0x510A))
            20746
            >>> int(IntegerToken(0x1980))
            6528
            >>> int(IntegerToken(-3))
            16381
        '''#'''
        name, number = key
        result = super(_integer_Token, klass).__new__(klass, number)
        result.text = name
        return result
    
    # Basic token properties
    def __str__(self):
        ''' Returns the text given to the token when initialized.
            May or may not be the standard DCSP name.
            
            >>> str(YES)
            'YES'
            >>> str(IntegerToken(3))
            '3'
            >>> str(IntegerToken(-3))
            '-3'
            >>> South = Token("STH", 0x4101)
            >>> South
            Token('STH', 0x4101)
            >>> str(South)
            'STH'
        '''#'''
        return self.text
    number = property(fget=int)
    
    # Avoid changing the text
    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("'%s' object attribute '%s' is read-only" %
                    (self.__class__.__name__, name))
        else: super(_integer_Token, self).__setattr__(name, value)

class Token(_integer_Token):
    ''' Embodies a single token, with both text and integer components.
        Instances are (mostly) immutable, and may be used as dictionary keys.
        However, as keys they are not interchangable with numbers or strings.
    '''#'''
    
    # Use __slots__ to save memory, and to maintain immutability
    __slots__ = ('category')
    cache = {}
    
    def __new__(klass, name, number):
        ''' Returns a Token instance from its name and number.
            If you only have one, use "config.protocol.base_rep[key]".
            
            # Moved here from the old category() method
            >>> YES.category
            72
            >>> StringToken('A').category == protocol.token_cats['Text']
            True
        '''#'''
        # Fiddle with parentheses
        if name == 'BRA': name = '('
        elif name == 'KET': name = ')'
        
        key = (name, number)
        result = Token.cache.get(key)
        if result is None:
            result = super(Token, klass).__new__(klass, key)
            result.category = (number & 0xFF00) >> 8
            Token.cache[key] = result
        return result
    
    # Components
    def category_name(self):
        ''' Returns a string representing the type of token.
            >>> YES.category_name()
            'Commands'
            >>> IntegerToken(-3).category_name()
            'Integers'
        '''#'''
        return protocol.token_cats.get(self.category, 'Unknown')
    def value(self):
        ''' Returns a numerical value for the token.
            For integers, this is the value of the number;
            for other tokens, the second byte of the DCSP token.
            May be used as an array prefix for powers and provinces.
            
            >>> YES.value()
            28
            >>> Token('PAR', 0x510A).value()
            10
            >>> IntegerToken(0x1980).value()
            6528
            >>> IntegerToken(-3).value()
            -3
        '''#'''
        if   self.is_positive(): return self.number
        elif self.is_negative(): return self.number - protocol.max_neg_int
        else:                    return self.number & 0x00FF
    
    # Types
    def is_text(self):
        ''' Whether the token represents an ASCII character.
            >>> YES.is_text()
            False
            >>> StringToken('A').is_text()
            True
        '''#'''
        return self.category == protocol.token_cats['Text']
    def is_power(self):
        ''' Whether the token represents a power (country) of the game.
            >>> YES.is_power()
            False
            >>> UNO.is_power()
            False
            >>> Token('ENG', 0x4101).is_power()
            True
        '''#'''
        return self.category == protocol.token_cats['Powers']
    def is_unit_type(self):
        ''' Whether the token represents a type of unit.'''
        return self.category == protocol.token_cats['Unit_Types']
    def is_coastline(self):
        ''' Whether the token represents a specific coastline of a province.'''
        return self.category == protocol.token_cats['Coasts']
    def is_supply(self):
        ''' Whether the token represents a province with a supply centre.
            >>> YES.is_supply()
            False
            >>> Token('FIN', 0x5425).is_supply()
            False
            >>> Token('NWY', 0x553E).is_supply()
            True
        '''#'''
        return self.is_province() and self.category & 1 == 1
    def is_coastal(self):
        ''' Whether the token represents a coastal province;
            that is, one to or from which an army can be convoyed.
        '''#'''
        return self.category_name() in (
            'Coastal SC',
            'Coastal non-SC',
            'Bicoastal SC',
            'Bicoastal non-SC',
        )
    def is_province(self):
        ''' Whether the token represents a province.
            >>> YES.is_province()
            False
            >>> Token('FIN', 0x5425).is_province()
            True
            >>> Token('NWY', 0x553E).is_province()
            True
        '''#'''
        p_cat = protocol.token_cats['Provinces']
        return p_cat[0] <= self.category <= p_cat[1]
    def is_integer(self):
        ''' Whether the token represents a number.
            >>> YES.is_integer()
            False
            >>> IntegerToken(3).is_integer()
            True
            >>> IntegerToken(-3).is_integer()
            True
        '''#'''
        return self.number < protocol.max_neg_int
    def is_positive(self):
        ''' Whether the token represents a positive number.
            >>> YES.is_positive()
            False
            >>> IntegerToken(3).is_positive()
            True
            >>> IntegerToken(-3).is_positive()
            False
            >>> IntegerToken(0).is_positive()
            False
        '''#'''
        return 0 < self.number < protocol.max_pos_int
    def is_negative(self):
        ''' Whether the token represents a negative number.
            >>> YES.is_negative()
            False
            >>> IntegerToken(3).is_negative()
            False
            >>> IntegerToken(-3).is_negative()
            True
            >>> IntegerToken(0).is_positive()
            False
        '''#'''
        return protocol.max_pos_int <= self.number < protocol.max_neg_int
    
    # Conversions
    def __hex__(self):
        ''' Returns a string representing this token in hexadecimal.
            By DAIDE convention, x is lower-case, hex digits are upper-case,
            and exactly four digits are displayed.
            >>> hex(YES)
            '0x481C'
        '''#'''
        return '0x%04X' % self.number
    def __repr__(self):
        ''' Returns code to reproduce the token.
            Uses the simplest form it can.
            >>> repr(IntegerToken(-3))
            'IntegerToken(-3)'
            >>> repr(YES)
            'YES'
            >>> repr(KET)
            'KET'
            >>> eval(repr(YES)) == base_rep['YES']
            True
            >>> repr(Token('STH', 0x4101))
            "Token('STH', 0x4101)"
        '''#'''
        name = self.__class__.__name__
        if self.is_integer() and self.text == str(self.value()):
            return name + '(' + self.text + ')'
        elif self == KET: return 'KET'
        elif self == BRA: return 'BRA'
        elif protocol.default_rep.get(self.text) == self: return self.text
        elif len(self.text) == 1 and StringToken(self.text) == self:
            return name + '(' + repr(self.text) + ')'
        else: return name+'('+repr(self.text)+', '+('0x%04X'%self.number)+')'
    def tokenize(self): return [self]
    def key(self): return self
    key = property(fget=key)
    
    # Actions
    def __call__(self, *args):
        ''' Creates a new Message, starting with the token.
            The arguments are wrapped in brackets;
            call the result to add more parameters.
            
            >>> print NOT(GOF)
            NOT ( GOF )
            >>> print YES(MAP('name'))
            YES ( MAP ( "name" ) )
            >>> print DRW (ENG, FRA, GER)
            DRW ( ENG FRA GER )
            >>> print TRY()
            TRY ( )
            >>> print NOW (standard_map.current_turn)
            NOW ( SPR 1901 )
        '''#'''
        return Message(self)(*args)
    def __add__(self, other):
        ''' A token can be added to the front of a message.
            >>> press = PRP(PCE(ENG, FRA))
            >>> print HUH(ERR + press)
            HUH ( ERR PRP ( PCE ( ENG FRA ) ) )
        '''#'''
        return Message(self) + Message(other)
    def __pos__(self):
        ''' Creates a Message containing only this token.
            >>> +OBS
            Message([OBS])
            >>> print HUH(DRW(ENG) ++ ERR)
            HUH ( DRW ( ENG ) ERR )
        '''#'''
        return Message(self)
    
    # Shortcuts for treating Tokens as Messages
    def __and__(self, other): return Message(self) & other
    def __mod__(self, other): return Message(self) % other

class StringToken(Token):
    ''' A token of a DM string, encoding a single ASCII character.
        (Or, perhaps, a UTF-8 byte.)
    '''#'''
    
    # Use __slots__ to save memory, and to maintain immutability
    __slots__ = ()
    cache = {}
    
    def __new__(klass, char):
        result = StringToken.cache.get(char)
        if result is None:
            charnum = ord(char)
            if charnum > 0xFF:
                raise OverflowError, '%s too large to convert to %s' % (type(char), klass.__name__)
            else:
                result = Token.__new__(klass, char, protocol.quot_prefix + charnum)
            StringToken.cache[char] = result
        return result

class IntegerToken(Token):
    ''' A token representing a DM integer.
        Only supports 14-bit two's-complement numbers.
    '''#'''
    
    # Use __slots__ to save memory, and to maintain immutability
    __slots__ = ()
    cache = {}
    
    def __new__(klass, number):
        pos = protocol.max_pos_int
        neg = protocol.max_neg_int
        number = int(number)
        if number < 0: key = number + neg
        else: key = number
        result = IntegerToken.cache.get(key)
        if result is None:
            if number < -pos:
                raise OverflowError, '%s too large to convert to %s' % (
                        type(number).__name__, klass.__name__)
            elif number < pos:
                name = str(number)
            elif number < neg:
                name = str(number - neg)
            else:
                raise OverflowError, '%s too large to convert to %s' % (
                        type(number).__name__, klass.__name__)
            result = Token.__new__(klass, name, key)
            IntegerToken.cache[key] = result
        return result


class Time(Comparable):
    ''' A time limit, in seconds and hours.
        Can also handle negative seconds as hours on incoming messages.
    '''#'''
    def __init__(self, seconds, hours=0):
        if isinstance(seconds, Token): seconds = seconds.value()
        if isinstance(hours, Token): hours = hours.value()
        self.seconds = self.hours = 0
        if hours >= 0 <= seconds:
            self.seconds = seconds % 3600
            self.hours = hours + (seconds // 3600)
        elif seconds < 0 and not hours:
            self.seconds = 0
            self.hours = -seconds
        else: raise ValueError("Invalid Time(%r, %r)" % (seconds, hours))
    
    # Representations
    def tokenize(self):
        seconds = int(self)
        if seconds > protocol.max_pos_int:
            result = Message((self.seconds, self.hours))
        else: result = Message(seconds)
        return result
    def __int__(self): return int(self.seconds + 3600*self.hours)
    def __str__(self): return str(Message(self))
    def __repr__(self): return 'Time(%s, %s)' % (self.seconds, self.hours)
    def __cmp__(self, other): return cmp(int(self), other)

def maybe_int(word):
    ''' Converts a string to an int if possible.
        Returns either the int, or the original string.
        >>> [(type(x), x) for x in [maybe_int('-3'), maybe_int('three')]]
        [(<type 'int'>, -3), (<type 'str'>, 'three')]
    '''#'''
    try:    n = int(word)
    except: return word
    else:   return n

def character(value):
    ''' Configuration parser for a single-character string.'''
    if len(value) != 1:
        raise ValueError('Exactly one character expected')
    return value

class Representation(Configurable):
    ''' Holds and translates all tokens for a variant.
        Warning: Abuses the traditional dict methods.
    '''#'''
    __section__ = 'tokens'
    __options__ = (
        ('squeeze_parens', bool, False, 'squeeze parentheses',
            'Whether to omit the spaces just inside parentheses when printing messages.'),
        ('ignore_unknown', bool, True, 'ignore unknown tokens',
            'Whether to allow tokens not represented in the protocol document or RM.',
            'If this is false, unknown tokens in a DM will result in an Error Message.'),
        ('input_escape', character, '\\', 'input escape character',
            'The character which escapes quotation marks when translating messages.',
            'This can be the same as the quotation mark character itself.'),
        ('output_escape', character, '\\', 'output escape character',
            'The character with which to escape quotation marks when printing messages.',
            'This can be the same as the quotation mark character itself.'),
        ('quot_char', character, '"', 'quotation mark',
            'The character to use for quoting strings when printing messages.'),
    )
    
    def __init__(self, tokens, base):
        # tokens is a number -> name mapping
        self.__super.__init__()
        self.base = base
        self.names = names = {}
        self.numbers = nums = {}
        for number, name in tokens.iteritems():
            nums[number] = names[name] = Token(name, number)
    
    def __getitem__(self, key):
        ''' Returns a Token from its name or number.'''
        result = self.get(key)
        if result is None:
            if isinstance(key, int): key = '0x%04X' % key
            raise KeyError, 'unknown token %r' % (key,)
        return result
    def get(self, key, default=None):
        ''' Returns a Token from its name or number.
            >>> default_rep.get('ITA')
            ITA
        '''#'''
        result = self.numbers.get(key) or self.names.get(key)
        if result is None:
            if isinstance(key, Token): result = key
            elif self.base: result = self.base.get(key)
            else:
                try: number = int(key)
                except ValueError: result = default
                else:
                    if number < protocol.max_neg_int:
                        result = IntegerToken(number)
                    elif (number & 0xFF00) == protocol.quot_prefix:
                        result = StringToken(chr(number & 0x00FF))
                    elif self.options.ignore_unknown:
                        result = Token('0x%04X' % number, number)
                    else: result = default
        return result
    
    def has_key(self, key):
        ''' Determines whether a given TLA is in use.'''
        return ((key in self.names) or (key in self.numbers) or
                (self.base and self.base.has_key(key)))
    
    def __len__(self):
        return len(self.numbers)
    
    def __str__(self):
        ''' Reproduces the representation as a *.rem file.'''
        result = "%d\n" % len(self)
        for name, token in self.names.iteritems():
            result += "%04X:%s\n" % (token.number, name)
        return result
    
    def __eq__(self, other):
        r'''Compares two Representations, or a Representation and a dict.
            Mostly useful for test cases, so efficiency is not important.
        '''#"""#'''
        
        return other == self.names
    
    def items(self):
        ''' Creates a name -> token mapping.'''
        return self.names.items()
    
    def keys(self):
        ''' Returns a list of token TLAs.'''
        return self.names.keys()
    
    def translate(self, text):
        ''' Translates diplomacy message strings into Messages,
            choosing an escape model based on options.
            
            # Black magic: This test exploits an implementation detail or two.
            # This test avoids backslashes because they get halved too often.
            >>> s = 'NME("name^""KET""BRA"KET""BRA" ^")'
            >>> default_rep.options.input_escape = '"'
            >>> str(default_rep.translate(s))
            'NME ( "name^""KET""BRA" ) ( " ^" )'
            >>> default_rep.options.input_escape = '^'
            >>> str(default_rep.translate(s))
            Traceback (most recent call last):
                ...
            KeyError: 'unknown token \\'"\\''
        '''#'''
        if self.options.input_escape == self.options.quot_char:
            return self.translate_doubled_quotes(text)
        else: return self.translate_backslashed(text)
    
    def translate_doubled_quotes(self, text):
        ''' Translates diplomacy message strings into Messages,
            doubling quotation marks to escape them.
            
            >>> default_rep.options.input_escape = '"'
            >>> default_rep.translate_doubled_quotes('NOT ( GOF KET')
            Message([NOT, [GOF]])
            >>> str(default_rep.translate_doubled_quotes('      REJ(NME ("Evil\\'Bot v0.3\\r"KET(""")\\n (\\\\"-3)\\r\\n'))
            'REJ ( NME ( "Evil\\'Bot v0.3\\r" ) ( """)\\n (\\\\" -3 )'
            >>> default_rep.translate_doubled_quotes('YES " NOT ')
            Traceback (most recent call last):
                ...
            ValueError: unterminated string in Diplomacy message
        '''#'''
        # initialization
        fragments = text.split(self.options.quot_char)
        message = []
        in_text = 0
        
        # aliases
        quoted = self.tokenize_quote
        normal = self.tokenize_normal
        addmsg = message.extend
        append = message.append
        
        # The first normal part might be empty (though it shouldn't),
        # so we process it here instead of inside the loop.
        addmsg(normal(fragments[0]))
        
        # Empty normal parts in the middle are really pairs of quotation marks
        for piece in fragments[1:-1]:
            in_text = not in_text
            if in_text: addmsg(quoted(piece))
            elif piece: addmsg(normal(piece))
            else: append(StringToken(self.options.quot_char))
        
        # Again, the last normal part might be empty.
        if len(fragments) > 1:
            in_text = not in_text
            if in_text: addmsg(quoted(fragments[-1]))
            else:       addmsg(normal(fragments[-1]))
        
        # Complain if the message wasn't finished
        if in_text: raise ValueError, 'unterminated string in Diplomacy message'
        else: return Message(message)
    
    def translate_backslashed(self, text):
        ''' Translates diplomacy message strings into Messages,
            using backslashes to escape quotation marks.
            
            >>> default_rep.options.input_escape = '\\\\'
            >>> default_rep.translate_backslashed('NOT ( GOF KET')
            Message([NOT, [GOF]])
            >>> str(default_rep.translate_backslashed('     REJ(NME ("Evil\\'Bot v0.3\\r"KET("\\\\")\\n (\\\\\\\\"-3)\\r\\n'))
            'REJ ( NME ( "Evil\\'Bot v0.3\\r" ) ( """)\\n (\\\\" -3 )'
            >>> default_rep.translate_backslashed('YES " NOT ')
            Traceback (most recent call last):
                ...
            ValueError: unterminated string in Diplomacy message
        '''#'''
        
        # initialization
        fragments = text.split(self.options.quot_char)
        message = []
        in_text = False
        saved = ''
        slash = self.options.input_escape
        
        # aliases
        quoted = self.tokenize_quote
        normal = self.tokenize_normal
        addmsg = message.extend
        
        # Empty normal parts in the middle are really pairs of quotation marks
        for piece in fragments:
            slashes = 0
            while piece and (piece[-1] == slash):
                piece = piece[:-1]
                slashes += 1
            piece += slash * int(slashes/2)
            
            if slashes % 2:
                # Odd number: escape the quotation mark
                saved += piece + self.options.quot_char
            else:
                if in_text: addmsg(quoted(saved + piece))
                else:       addmsg(normal(saved + piece))
                in_text = not in_text
                saved = ''
        
        # Complain if the message wasn't finished
        if saved or not in_text:
            raise ValueError, 'unterminated string in Diplomacy message'
        else: return Message(message)
    
    def tokenize_quote(self, text):
        ''' Returns a list of tokens from a string within a quotation.
            >>> default_rep.tokenize_quote('Not(Gof)')
            [StringToken('N'), StringToken('o'), StringToken('t'), StringToken('('), StringToken('G'), StringToken('o'), StringToken('f'), StringToken(')')]
            >>> default_rep.tokenize_quote('name')
            [StringToken('n'), StringToken('a'), StringToken('m'), StringToken('e')]
        '''#'''
        return [StringToken(c) for c in text]
    
    def tokenize_normal(self, text):
        ''' Returns a list of tokens from a string without quotations.
            >>> default_rep.tokenize_normal('Not(Gof)')
            [NOT, BRA, GOF, KET]
            >>> default_rep.tokenize_normal('name')
            Traceback (most recent call last):
                ...
            KeyError: "unknown token 'NAME'"
        '''#'''
        # Switch parentheses to three-character notation
        text = text.replace('(', ' BRA ')
        text = text.replace(')', ' KET ')
        
        # Pass items into Token, converting integers if necessary
        return [self[maybe_int(word.upper())] for word in text.split()]


class Protocol(VerboseObject):
    ''' Collects various constants from the Client-Server Protocol file.
        Rather dependent on precise formatting.
        
        >>> proto = Protocol()
        >>> proto.token_cats[0x42]
        'Unit Types'
        >>> proto.token_cats['Unit_Types']
        66
        >>> proto.error_strings[5]
        'Version incompatibility'
        >>> proto.default_rep[0x4101]
        ENG
        >>> proto.base_rep[0x481C]
        YES
        >>> proto.message_types['Diplomacy']
        2
    '''#'''
    __section__ = 'syntax'
    __options__ = (
        ('dcsp_file', file, 'parlance://data/protocol.html', 'protocol file',
            'Document specifying protocol information, including token names and numbers.'),
    )
    
    def __init__(self):
        ''' Initializes instance variables and calculates a few constants.
            - base_rep       Representation of the language-level tokens
            - default_rep    Representation of the tokens for the default map
            - token_cats     Token category name <-> number(s) mappings
            - error_strings  Mapping of Error Message code -> description
            - message_types  Mapping of type word -> message code
            - version        Version of the protocol document
            - magic          Magic number for the Initial Message
            
            Protocol instances may also have members with capitalized names,
            as shorthand for the error codes in the protocol document.
        '''#'''
        self.__super.__init__()
        self.base_rep = None
        self.default_rep = None
        self.token_cats = {}
        self.error_strings = {}
        self.message_types = {}
        self.version = None
        self.magic = None
        
        parse_file(self.options.dcsp_file, self.parse_dcsp)
        
        # Calculated constants needed by the above classes
        self.quot_prefix = self.token_cats['Text'] << 8
        self.max_pos_int = (self.token_cats['Integers'][1] + 1) << 7
        self.max_neg_int = self.max_pos_int << 1
    
    def parse_dcsp(self, dcsp_file):
        # Local variable initialization
        msg_name = None
        err_type = None
        last_cat = None
        rep_item = False
        old_line = ''
        token_names = {}
        default_tokens = {}
        
        for line in dcsp_file:
            if old_line: line = old_line + ' ' + line.strip()
            pos = line.find('>0x')
            if pos > 0:
                # Given sepearately, because the error description
                # might be on the same line as the type number.
                pos2 = pos + line[pos:].find('<')
                err_type = int(line[pos+1:pos2], 16)
            
            if err_type:
                match = re.search(r'<a name="([A-Z]\w+)">', line)
                if match: setattr(self, match.group(1), err_type)
                match = re.search(r'>(\w+ [\w ]+)<', line)
                if match:
                    self.error_strings[err_type] = match.group(1)
                    err_type = None
                    old_line = ''
                else: old_line = line[line.rfind('>'):].strip()
            elif msg_name:
                if line.find('Message Type =') > 0:
                    type_num = int(re.search(r'Type = (\d+)', line).group(1))
                    self.message_types[msg_name] = type_num
                    msg_name = ''
            elif line.find(' (0x') > 0:
                match = re.search(r'[> ](\w[\w ]+) \((0x\w\w)', line)
                descrip = match.group(1)
                start_cat = int(match.group(2), 16)
                match = re.search(r' (0x\w\w)\)', line)
                if match:
                    last_cat = int(match.group(1), 16)
                    self.token_cats[descrip.replace(' ', '_')] = (start_cat, last_cat)
                    for i in range(start_cat, last_cat + 1):
                        self.token_cats[i] = descrip
                else:
                    rep_item = descrip == 'Powers'
                    last_cat = start_cat << 8
                    self.token_cats[descrip.replace(' ', '_')] = start_cat
                    self.token_cats[start_cat] = descrip
            elif last_cat:
                if line.find('category =') > 0:
                    # This must come before the ' 0x' search.
                    match = re.search(r'>([\w -]+) category = (0x\w\w)<', line)
                    if match:
                        last_cat = int(match.group(2), 16)
                        self.token_cats[last_cat] = descrip = match.group(1)
                        self.token_cats[descrip.replace(' ', '_')] = last_cat
                        rep_item = True
                        last_cat <<= 8
                    else:
                        self.log_debug(1, 'Bad line in protocol file: ' + line)
                elif line.find(' 0x') > 0:
                    match = re.search(r'>(\w\w\w) (0x\w\w)', line)
                    if match:
                        name = match.group(1).upper()
                        number = last_cat + int(match.group(2), 16)
                        if rep_item: default_tokens[number] = name
                        else: token_names[number] = name
            elif line.find('M)') > 0:
                match = re.search(r'The (\w+) Message', line)
                if match: msg_name = match.group(1)
            elif line.find('Version ') >= 0:
                match = re.search(r'Version (\d+)', line)
                if match: self.version = int(match.group(1))
            elif line.find('Magic Number =') > 0:
                match = re.search(r'Number = (0x\w+)', line)
                if match: self.magic = int(match.group(1), 16)
                else: self.log_debug(1, 'Invalid magic number: ' + line)
        self.base_rep = Representation(token_names, None)
        self.default_rep = Representation(default_tokens, self.base_rep)
        
        # Sanity checking
        if not self.magic: self.log_debug(1, 'Missing magic number')
        if not self.version: self.log_debug(1, 'Missing version number')

protocol = Protocol()
BRA = protocol.base_rep['BRA']
KET = protocol.base_rep['KET']
