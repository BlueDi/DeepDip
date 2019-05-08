r'''Parlance message validation
    Copyright (C) 2004-2008  Eric Wald
    
    This module includes a syntax checker for messages in Pythonic form.
    When used between a network layer and the message interpreter, it provides
    some measure of protection against evil input.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import re

from config   import VerboseObject, parse_file
from language import Token, protocol
from tokens   import BRA, ERR, HUH, KET, PRN

__all__ = ['Validator']

class Validator(VerboseObject):
    ''' Syntax checker, with a few other features.
        Meant to have one instance per game or client;
        usually, it will start out with syntax_level 0,
        elevating to a higher syntax level (maybe)
        when the game starts.
    '''#'''
    syntax = {'string': [(0, ['repeat', 'cat', 'Text'])]}
    press_levels = {}
    trimmed = {}
    __section__ = 'syntax'
    __options__ = (
        ('syntax_file', file, 'parlance://data/syntax.html', 'syntax file',
            'Document specifying syntax rules and level names.'),
    )
    
    def __init__(self, syntax_level=0):
        self.__super.__init__()
        self.syntax_level = syntax_level
        self.spaces = 0
        if not self.press_levels:
            self.read_syntax()
    
    def read_syntax(self):
        levels = parse_file(self.options.syntax_file, self.parse_syntax_file)
        
        if levels:
            # Expand press levels to be useful to the Game class
            for i,name in levels:
                self.press_levels[i] = name
                self.press_levels[str(i)] = i
                self.press_levels[name.lower()] = i
        else:
            # Set reasonable press levels if the file is unparsable
            for i in range(0, 200, 10) + [8000]:
                self.press_levels[i] = str(i)
                self.press_levels[str(i)] = i
    
    @classmethod
    def parse_syntax_file(klass, stream):
        ''' Parses lines from the DAIDE Message Syntax file.
            BNF-like rules are added to the class's syntax dictionary.
            Returns a mapping of press levels to their names.
        '''#'''
        tla = re.compile(r'[A-Z0-9]{3}$')
        #braces = re.compile(r'{.*?}')
        strings = re.compile(r"'\w+'")
        repeats = re.compile(r'(.*) +\1 *\.\.\.')
        lev_mark = re.compile(r'<h2><a name="level(\d+)">.*: (\w[a-zA-Z ]*)<')
        bnf_rule = re.compile(r'<(?:h4|li><b)>({\w\w\w} |)(?:<a name="\w+">|)(\w+) (\+|-|)= (.*?)<(?:/h4|/b|sup)>')
        syntax_level = 0
        neg_level = protocol.max_neg_int
        levels = []
        
        def parse_bnf(name, level, rule):
            ''' Parses a BNF-like syntax rule into dictionary form.'''
            rule = rule.replace('(', ' BRA ')
            rule = rule.replace(')', ' KET ')
            rule = rule.replace('[', ' optional ')
            rule = rule.replace(']', ' ] ')
            rule = rule.replace('...', ' ... ')
            rule = strings.sub('string', rule)
            words = parse_rule(level, rule)
            add_rule(name, level, words)
        
        def parse_rule(level, rule):
            match = repeats.search(rule)
            while match:
                rule = str.join(' ', [rule[:match.start()], 'repeat',
                        subrule(level, parse_rule(level, match.group(1))),
                        rule[match.end():]])
                match = repeats.search(rule)
            
            words = rule.split()
            while words[-1] == ']': words.pop()
            while ']' in words:
                start = None
                for index, word in enumerate(words):
                    if word == ']':
                        words[start:index+1] = subrule(level,
                                words[start:index]).split()
                        break
                    elif word == 'optional': start = index
            
            return words
        
        def subrule(level, words):
            ''' Returns a rule name suitable for repeat.
                May be of the form 'word', 'sub word', 'cat Word',
                'TLA', or '$auto-created-name'.
                In the last case, the new subrule will have been created.
            '''#'''
            if len(words) == 1: result = words[0]
            elif find_ket(words) == len(words) - 1:
                # Warning: Needs work for categories,
                # but the current syntax doesn't have such a situation.
                result = 'sub ' + subrule(level, words[1:-1])
            else:
                result = '$' + str.join('-', words)
                add_rule(result, level, words)
            return result
        
        def add_rule(name, level, words):
            ''' Translates token abbreviations and adds the rule.'''
            def correct(word):
                if tla.match(word): return [protocol.base_rep[word]]
                elif word[0].isupper() and word[1].islower():
                    return ['cat', word]
                else: return [word]
            try: rule = (level, sum([correct(word) for word in words], []))
            except KeyError, err:
                print 'Error parsing syntax document: %s' % err
            else:
                rules = klass.syntax.setdefault(name, [])
                if rule not in rules: rules.append(rule)
                if level < 0: klass.trimmed[rule[1][0]] = -level
        
        for line in stream:
            match = bnf_rule.search(line)
            if match:
                # Ignore the PDA/AOA marks, for now
                option, name, operator, rule = match.groups()
                rule = rule.replace('</a>', '')
                if operator == '+': use_level = -syntax_level
                elif operator == '-': use_level = -neg_level
                else: use_level = syntax_level
                parse_bnf(name, use_level, rule)
            else:
                match = lev_mark.search(line)
                if match:
                    syntax_level = int(match.group(1))
                    levels.append((syntax_level, match.group(2).strip()))
        
        return levels
    
    def trim(self, press):
        ''' Trims high-level tokens from TRY messages.'''
        for token, level in self.trimmed.items():
            if level > self.syntax_level:
                while token in press:
                    press.remove(token)
    
    def validate_server_message(self, msg):
        return self.validate(msg, 'server_message')
    def validate_client_message(self, msg):
        return self.validate(msg, 'client_message')
    def validate(self, msg, base_expression):
        ''' Determines whether the message is syntactically valid.
            Returns False for a good message, or an error Message
            (HUH or PRN) to send to the client.
            
            # Setup for the following tests
            >>> def validate(msg, level=0, from_server=False):
            ...     if from_server:
            ...         return Validator(level).validate_server_message(msg)
            ...     else:
            ...         return Validator(level).validate_client_message(msg)
            >>> from language import Message
            >>> Message.validate = validate
            >>> squeeze = base_rep.options.squeeze_parens
            >>> base_rep.options.squeeze_parens = True
            
            # Checks unbalanced parentheses
            >>> print base_rep.translate("IAM(NOT").validate()
            PRN (IAM (NOT)
            >>> print base_rep.translate("IAM)NOT(").validate()
            PRN (IAM) NOT ()
            >>> print base_rep.translate('PRN ( IAM ( NOT )').validate()
            False
            
            # Checks syntax
            >>> print base_rep.translate('WHT(YES)').validate()
            HUH (ERR WHT (YES))
            >>> print NME('name')(-3).validate()
            HUH (NME ("name") (ERR -3))
            >>> print NME('name').validate()
            HUH (NME ("name") ERR)
            >>> print NME('name')('version').validate()
            False
            
            # Checks syntax level
            >>> Peace = AND (PCE(ENG, FRA)) (DRW)
            >>> print SND(ENG)(PRP(Peace)).validate(40)
            False
            >>> m = SND(ENG)(PRP(ORR(NOT(DRW))(Peace)))
            >>> print m.validate(40)
            HUH (SND (ENG) (PRP (ORR (NOT (DRW)) (ERR AND (PCE (ENG FRA)) (DRW)))))
            >>> print m.validate(100)
            False
            
            # Checks messages from server, too
            >>> msg = MAP('standard')
            >>> print msg.validate()
            HUH (MAP ERR ("standard"))
            >>> print msg.validate(0, True)
            False
            
            # Just to restore the state for other tests:
            >>> base_rep.options.squeeze_parens = squeeze
        '''#'''
        if msg.count(BRA) != msg.count(KET):
            if msg[0] == PRN: return False
            else: return PRN(msg)
        else:
            index, valid = self.validate_expression(msg, base_expression)
            if valid and index == len(msg): return False
            else:
                if index < len(msg) and msg[index] == KET:
                    submsg = msg[:index + 1]
                    if submsg.count(BRA) != submsg.count(KET):
                        if msg[0] == PRN: return False
                        else: return PRN(msg)
                result = HUH(msg)
                result.insert(index + 2, ERR)
                return result
    
    def validate_expression(self, msg, sub):
        ''' Tries to match the message with the given expression level.
            Returns the number of tokens in the best match,
            and whether the full match is valid.
            Intended to be used by the Message class.
            
            >>> def validate_expression(msg, sub, level):
            ...     return Validator(level).validate_expression(msg, sub) 
            >>> Eng = Token('ENG', 0x4101)
            >>> validate_expression([ORR, BRA, DRW, KET, BRA, SLO, BRA, Eng, KET, KET], 'multipart_offer', 200)
            (10, True)
            
            # Serious boundary case: Empty sub-expression valid in TRY, but nowhere else.
            >>> validate_expression(TRY(), 'press_message', 10)
            (3, True)
            >>> validate_expression(SND()(TRY()), 'client_command', 10)
            (2, False)
            
            # Check for returning the correct error position,
            # even within nested expressions
            >>> Fra = Token('FRA', 0x4102)
            >>> m = SND (Eng) (PRP (ORR (NOT (DRW)) (AND (PCE(Eng, Fra)) (DRW))))
            >>> validate_expression(m, 'client_command', 40)
            (15, False)
            
            # Check for infinite recursion in HUH expressions
            >>> m = HUH(ERR, YES(NME("HoldBot")("Parlance 1.0.166")))
            >>> validate_expression(m, 'message', 0)
            (35, True)
            
            # Check for optional unwrapped subexpressions
            >>> m = SMR (SPR, 1901) (TUR, ["Fake Player"], ["Fake_Player"], 3) (AUS, ["Fake Human Player"], ["Fake_Master"], 3)
            >>> validate_expression(m, 'message', 0)
            (71, True)
        '''#'''
        if not isinstance(msg, list):
            raise ValueError('message must be a list')
        if not self.syntax.has_key(sub):
            raise ValueError('unknown expression "%s"' % sub)
        best = 0
        valid = False
        length = len(msg)
        for level,sub_list in self.syntax[sub]:
            if level <= self.syntax_level:
                self.spaces += 1
                self.log_debug(16, '%sChecking "%s" against %s',
                        ' ' * self.spaces, msg, sub_list)
                result, good = self.validate_option(msg, sub_list)
                self.log_debug(16, '%sResult: %s, %s',
                        ' ' * self.spaces, result, good)
                self.spaces -= 1
                if good == valid and result > best:
                    best = result
                    if valid and best == length: break
                elif good and not valid:
                    best = result
                    valid = good
                    if valid and best == length: break
        return best, valid
    
    def validate_option(self, msg, item_list):
        ''' Tries to match the message with the given expression list.
            Returns the number of tokens in the best match,
            and whether the full match is valid.
            
            >>> def validate_option(msg, option, level):
            ...     return Validator(level).validate_option(msg, option) 
            >>> validate_option([BRA, KET, BRA, YES, base_rep[-3]],
            ...     ['repeat', 'cat', 'Miscellaneous', YES, 'number'], 200)
            (5, True)
            >>> Eng = Token('ENG', 0x4101)
            >>> validate_option([BRA, DRW, KET, BRA, PCE, BRA, Eng, KET, KET, KET],
            ...     ['repeat', 'sub', 'offer'], 200)
            (9, True)
            >>> validate_option([BRA, DRW, KET, UNO, KET],
            ...     ['repeat', 'sub', 'offer', 'sco_power'], 200)
            (4, True)
        '''#'''
        index = 0
        option = None
        in_sub = in_cat = repeat = False
        length = len(msg)
        for opt in item_list:
            if isinstance(opt, str):
                if   opt == 'any':      return length, True
                elif opt == 'sub':      in_sub = True
                elif opt == 'cat':      in_cat = True
                elif opt == 'repeat':   repeat = True
                elif opt == 'optional': option = (index, True)
                else:
                    if in_sub:
                        # Wrapped subexpression
                        result, good = self.count_subs(msg[index:], opt, repeat)
                        index += result
                        if not (result and good): break
                    elif in_cat:
                        # Category name
                        if protocol.token_cats.has_key(opt):
                            num = protocol.token_cats[opt]
                            if isinstance(num, tuple):
                                check = lambda x: num[0] <= x.category <= num[1]
                            else: check = lambda x: x.category == num
                        elif opt == 'Token':
                            check = lambda x: x not in (BRA, KET, ERR)
                        else: raise ValueError, 'unknown category "%s"' % opt
                        result = count_valid(msg[index:], check, repeat)
                        if result: index += result
                        else: break
                    else:
                        # Unwrapped subexpression(s)
                        result = self.validate_expression(msg[index:], opt)
                        index += result[0]
                        if not result[1]: break
                        if repeat:
                            while result[1]:
                                result = self.validate_expression(msg[index:], opt)
                                index += result[0]
                    in_sub = in_cat = repeat = False
            elif isinstance(opt, Token):
                result = count_valid(msg[index:], lambda x: x == opt, repeat)
                repeat = False
                if result: index += result
                else: break
            else: raise UserWarning, 'Invalid State'
        else: return index, True
        return option or (index, False)
    
    def count_subs(self, msg, sub, repeat):
        ''' Tries to match the message with the given wrapped subexpression.
            Returns a tuple: (index,valid) where index is the last matched
            expression, and valid is whether it ended on an exact boundary.
            
            >>> def count_subs(msg, sub, repeat, level):
            ...     return Validator(level).count_subs(msg, sub, repeat) 
            >>> Eng = Token('ENG', 0x4101)
            >>> Fra = Token('FRA', 0x4102)
            >>> msg = [
            ...     BRA, DRW, KET,
            ...     BRA, XOY, BRA, Fra, KET, BRA, Eng, KET, KET,
            ... KET ]
            ... 
            >>> count_subs(msg, 'offer', True, 40)
            (4, False)
            >>> count_subs(msg, 'offer', True, 120)
            (12, True)
        '''#'''
        # Check for the start of a subexpression
        if not msg or msg[0] != BRA: return 0, False
        
        # Find the matching KET
        level = 1
        sublen = 0
        while level > 0:
            sublen += 1
            old_sublen = sublen
            sublen += msg[sublen:].index(KET)
            level += msg[old_sublen:sublen].count(BRA) - 1
        
        result = self.validate_expression(msg[1:sublen], sub)
        index = result[0] + 2
        if result[1]:
            if repeat:
                result, valid = self.count_subs(msg[index:], sub, repeat)
                if result: return index + result, valid
            return index, True
        else: return index - 1, False

def count_valid(msg, func, repeat):
    ''' Counts the number of tokens for which the given function returns True.
        If repeat is false, only the first token will be counted.
        
        >>> count_valid([True, True, False, True], lambda x:x, False)
        1
        >>> count_valid([True, True, False, True], lambda x:x, True)
        2
        >>> count_valid([False, True, False, True], lambda x:x, True)
        0
        >>> count_valid([False, True, False, True], lambda x:x, False)
        0
    '''#'''
    if repeat:
        index = 0
        length = len(msg)
        while index < length and func(msg[index]): index += 1
        return index
    elif msg and func(msg[0]): return 1
    else: return 0

def find_ket(msg):
    ''' Finds the index of a KET that matches the BRA starting the message.
        If the message is empty or does not start with BRA, returns 0.
        Also returns 0 if the parentheses are imbalanced.
        Modified to accept strings as well as tokens.
        
        >>> find_ket([BRA, NOT, BRA, GOF, KET, KET, BRA, DRW, KET])
        5
        >>> find_ket([BRA, BRA, GOF, KET, BRA, DRW, KET, KET])
        7
        >>> find_ket([BRA, BRA, GOF, KET])
        0
    '''#'''
    if not msg: return 0
    start = msg[0]
    if start == 'BRA': end = 'KET'
    elif start == BRA: end = KET
    else: return 0
    
    level = 1
    index = 0
    while level > 0:
        index += 1
        old_index = index
        try: index += msg[index:].index(end)
        except ValueError: return 0
        level += msg[old_index:index].count(start) - 1
    return index
