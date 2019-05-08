r'''Parlance configuration management
    Copyright (C) 2004-2008  Eric Wald
    
    This module harfs files for constants and other information.
    The main configuration files are parlance.cfg in the current working
    directory, and ~/.config/parlance.cfg in the user's home directory.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

import re
from ConfigParser import RawConfigParser
from os           import linesep, path
from pkg_resources import iter_entry_points, resource_stream
from sys          import argv
from weakref      import WeakValueDictionary

from functions import any, autosuper, defaultdict, expand_list, \
        s, settable_property

# Parsers for standard option types
def boolean(value):
    if str(value).lower() in ('yes', 'true', 'on'):
        result = True
    elif str(value).lower() in ('no', 'false', 'off'):
        result = False
    else: raise ValueError('Unrecognized boolean value; try "yes" or "no"')
    return result
def number(value):
    try: result = float(value)
    except ValueError:
        raise ValueError('Unrecognized numeric value')
def integer(value):
    # Todo: Recognize a leading zero as indicating an octal value.
    try: result = int(value)
    except ValueError:
        try: result = int(value, 16)
        except ValueError:
            raise ValueError('Unrecognized integer value')
    return result
def string(value):
    return value
def stringlist(value):
    result = [r for r in [s.strip() for s in value.split(',')] if r]
    return result
    
# Various option classes.
class Configuration(object):
    ''' Container for various configurable settings and constants.
        Each subclass may have an __options__ member, treated somewhat like
        __slots__ in that it builds on, rather than supplants, those in parent
        classes.  The __options__ member should be a sequence of tuples:
        (name, type, default, alternate name(s), help line, ...)
        
        For each item of __options__, all instances of the class will have
        a member by that name, set either from the command line, the main
        configuration files, the default value, or elsewhere in the program.
        Each instance may be modified independently, but set_globally()
        can be used to set all of them at once.
        
        The subclass may also have a __section__ member, indicating the
        section of the configuration file under which its corresponding
        options should be located.  If it does not have one, the name of
        the class's module will be used.
    '''#'''
    __metaclass__ = autosuper
    _user_config = RawConfigParser()
    _user_config.read(['parlance.cfg',
            path.expanduser('~/.config/parlance.cfg')])
    _cache = {}
    _args = {}
    _configurations = WeakValueDictionary()
    
    def __init__(self):
        self.parse_options(self.__class__)
        self._configurations[id(self)] = self
    def parse_options(self, klass):
        for cls in reversed(klass.__mro__):
            section = cls.__dict__.get('__section__', cls.__module__)
            opts = cls.__dict__.get('__options__', ())
            for item in opts: self.add_option(section, *item)
    def add_option(self, section, name, option_type, default, alt_names, *help):
        value = default
        if self._cache.has_key(name):
            value = self._cache[name]
        else:
            parser = self._validators.get(option_type, option_type)
            def attempt_arg(option):
                result = None
                if self._args.has_key(option):
                    val = self._args[option]
                    try: result = parser(val)
                    except ValueError, err:
                        print ('Warning: Illegal value for argument %s: '
                                '%r (%s)' % (option, val, str(err)))
                return result
            def attempt_file(option):
                result = None
                if self._user_config.has_option(section, option):
                    val = self._user_config.get(section, option)
                    try: result = parser(val)
                    except ValueError, err:
                        print ('Warning: Illegal value for %s, in section '
                                '%s of the configuration file: %r (%s)'
                                % (option, section, val, str(err)))
                return result
            
            if isinstance(alt_names, str):
                canon = self.canonical_name(alt_names)
                if canon and canon != alt_names:
                    names = (name, alt_names, canon)
                else: names = (name, alt_names)
            elif alt_names:
                names = (name,)
                for item in alt_names:
                    canon = self.canonical_name(item)
                    if canon and canon != item:
                        names += (item, canon)
                    else: names += (item,)
            else: names = (name,)
            
            # Check the config file(s) first, so an argument overrides it.
            for item in names:
                val = attempt_file(item)
                if val is not None:
                    value = val
                    break
            for item in names:
                val = attempt_arg(item)
                if val is not None:
                    value = val
                    break
            
            # Cache the result, so we don't have to go through this again.
            self._cache[name] = value
        setattr(self, name, value)
    
    @staticmethod
    def canonical_name(option_name):
        while option_name and not option_name[0].isalpha():
            option_name = option_name[1:]
        if len(option_name) == 1:
            # Case matters for single-char options
            result = option_name
        elif len(option_name) > 3:
            # Lower-case most names
            result = option_name.lower().replace('-', '_').replace(' ', '_')
        elif option_name.isalpha():
            # Upper-case TLAs
            result = option_name.upper()
        else: result = None
        return result
    @classmethod
    def parse_argument(klass, arg):
        if not arg: return False
        result = False
        if arg[0] == '-':
            if arg[1] == '-':
                if len(arg) > 2:
                    index = arg.find('=')
                    if index < 0:
                        name = klass.canonical_name(arg[2:])
                        if name:
                            klass._args[name] = True
                            result = True
                    elif index > 2:
                        name = klass.canonical_name(arg[2:index])
                        if name:
                            klass._args[name] = arg[index + 1:]
                            result = True
                elif len(arg) == 2: raise StopIteration
            elif arg[1].isalpha():
                if len(arg) == 2:
                    klass._args[arg[1]] = False
                    result = True
                else:
                    klass._args[arg[1]] = arg[2:]
                    result = True
        elif arg[0] == '+':
            if len(arg) == 2 and arg[1].isalpha():
                klass._args[arg[1]] = True
                result = True
        else:
            index = arg.find(':')
            port = arg[index+1:]
            if index >= 0 and port.isdigit():
                if index > 0: klass._args['host'] = arg[:index]
                klass._args['port'] = int(port)
                result = True
            elif not port:
                # Handle "example.tld:" as a host name, with default port.
                # Do we really want this?
                klass._args['host'] = arg[:index]
                result = True
        return result
    @classmethod
    def parse_argument_list(klass, args):
        ''' Collects options from the given argument list,
            returning any unparsable ones.
        '''#'''
        if klass._cache:
            print ('Warning: Option%s %s set before command-line parsing'
                    % (s(len(klass._cache)), expand_list(klass._cache.keys())))
        result = [arg for arg in args if not klass.parse_argument(arg)]
        return result
    
    @classmethod
    def set_globally(klass, name, value):
        klass._cache[name] = value
        for conf in klass._configurations.values():
            if hasattr(conf, name): setattr(conf, name, value)
    def update(self, option_dict):
        for key in option_dict:
            if hasattr(self, key):
                setattr(self, key, option_dict[key])
    
    _validators = {
        bool: boolean,
        float: number,
        int: integer,
        str: string,
        file: string,  # Todo: Write something to verify this
        list: stringlist,
    }
Configuration.arguments = Configuration.parse_argument_list(argv[1:])

class GameOptions(Configuration):
    ''' Options sent in the HLO message.'''
    __section__ = 'game'
    __options__ = (
        ('LVL', int, 0, 'syntax level',
            'Syntax level of the game.',
            'Mostly determines what kind of press can be sent.',
            'See the message syntax document for more details.'),
        ('MTL', int, 0, 'Move Time Limit',
            'Time limit for movement phases, in seconds.',
            'A setting of 0 disables movement time limits.',
            'The standard "real-time" setting is 600 (five minutes).'),
        ('RTL', int, 0, 'Retreat Time Limit',
            'Time limit for retreat phases, in seconds.',
            'A setting of 0 disables retreat time limits.',
            'The standard "real-time" setting is 120 (two minutes).'),
        ('BTL', int, 0, 'Build Time Limit',
            'Time limit for build phases, in seconds.',
            'A setting of 0 disables build time limits.',
            'The standard "real-time" setting is 180 (three minutes).'),
        ('PTL', int, 0, 'Press Time Limit',
            'Time (in seconds) before movement deadlines to start blocking press.',
            'If there is no movement time limit, this has no effect;',
            'otherwise, if this is greater than or equal to MTL,',
            'press is entirely blocked in movement phases.'),
        
        ('NPR', bool, False, 'No Press during Retreats',
            'Whether press is blocked during retreat phases.'),
        ('NPB', bool, False, 'No Press during Builds',
            'Whether press is blocked during build phases.'),
        ('DSD', bool, True, 'Deadline Stops on Disconnection',
            'Whether time limits pause when a non-eliminated player disconnects.',
            'The standard "real-time" setting is yes.'),
        ('AOA', bool, False, 'Any Orders Allowed',
            'Whether to accept any syntactically valid order, regardless of legality.',
            "This server is more permissive than David's in AOA games;",
            "the latter doesn't accept orders for non-existent or foreign units.",
            'See also DATC option 4.E.1, which only comes up in AOA games.',
            'The standard "real-time" setting is no.'),
        ('PDA', bool, False, 'Partial Draws Allowed',
            "Whether to allow draws that don't include all survivors.",
            'When this is on, clients can specify powers to allow in the draw,',
            'and the server can specify the powers in a draw.',
            'Only available at syntax level 10 or above.'),
    )
    
    def __init__(self):
        self.__super.__init__()
        self.sanitize()
    def parse_message(self, message):
        ''' Collects the information from a HLO or LST message.'''
        from language import Time
        for var_opt in message.fold()[-1]:
            text = var_opt[0].text
            if len(var_opt) == 1: setattr(self, text, True)
            elif text[1:3] == 'TL': setattr(self, text, int(Time(*var_opt[1:])))
            elif len(var_opt) == 2: setattr(self, text, var_opt[1])
            else:
                raise ValueError('Unknown variant option in %s message' %
                        message[0].text)
            
    def sanitize(self):
        ''' Performs a few sanity checks on the options.'''
        # Todo: Ensure that all numbers are positive.
        if self.LVL >= 10:
            if self.MTL > 0:
                if self.PTL >= self.MTL: self.PTL = self.MTL
            else: self.PTL = 0
        else:
            self.PTL = 0
            self.PDA = False
    def get_params(self):
        from language import Time
        from tokens import LVL, MTL, RTL, BTL, AOA, DSD, PDA, NPR, NPB, PTL
        params = [(LVL, self.LVL)]
        if self.MTL: params.append((MTL, Time(self.MTL)))
        if self.RTL: params.append((RTL, Time(self.RTL)))
        if self.BTL: params.append((BTL, Time(self.BTL)))
        if self.AOA: params.append((AOA,))
        if self.DSD: params.append((DSD,))
        
        if self.LVL >= 10:
            if self.PDA: params.append((PDA,))
            if self.NPR: params.append((NPR,))
            if self.NPB: params.append((NPB,))
            if self.PTL: params.append((PTL, Time(self.PTL)))
        return params
    def tokenize(self):
        from language import Message
        return Message(self.get_params())
    
    # Idea for future expansion:
    # Press Types (SND?)
        # Bit vector in integer field:
            #  0  Can send signed partial press
            #  1  Can send anonymous partial press
            #  2  Can fake sender in partial press
            #  3  Can fake recipients in partial press
            #  4  Can fake partial press as broadcast
            #  5  Can send signed broadcast press
            #  6  Can send anonymous broadcast press
            #  7  Can fake sender in broadcast press
            #  8  Can fake recipients in broadcast press
            #  9  Can fake broadcast press as partial
            # 10  Touching powers can send press
            # 11  Non-touching powers can send press
            # 12  Non-map players can send press
            # 13  Observers can send press
        # White:    3073 Your own identity given, can't be faked. (Default)
        # Black:    3077 You choose the identity to give
        # Grey:     3074 Anonymous
        # Public:   3104 Broadcast only
        # Yellow:   3136 Anonymous broadcast
        # Fake:     3081 Faked set of recipients
        # Touch:    1025 Only between powers with touching units
        # Backseat: 4128 Only non-map powers, and them broadcast-only
    # Tournaments (TRN)


class Configurable(object):
    ''' Generic class for anything that can be configured by preference files.
        __options__ and __section__ will be used to build a Configuration
        instance for each Configurable instance, which will be available
        as self.options.
    '''#'''
    __metaclass__ = autosuper
    def __init__(self):
        self.options = Configuration()
        self.options.parse_options(self.__class__)

class VerboseObject(Configurable):
    ''' Basic logging system.
        Provides one function, log_debug, to print lines either to stdout
        or to a configurable file, based on verbosity level.
        Classes or instances may override prefix to set the label on each
        line written by that item.
    '''#'''
    __files = {}
    __section__ = 'main'
    __options__ = (
        ('verbosity', int, 1, 'v',
            'How much debug or logging information to display.'),
        ('log_file', file, '', None,
            'File in which to log output lines, instead of printing them.'),
    )
    
    def log_debug(self, level, line, *args):
        if level <= self.options.verbosity:
            line = self.prefix + ': ' + str(line) % args
            filename = self.options.log_file
            if filename:
                output = self.__files.get(filename)
                if not output:
                    output = file(filename, 'a')
                    self.__files[filename] = output
                output.write(line + linesep)
            else:
                try: print line + '\n',
                except IOError: self.verbosity = 0 # Ignore broken pipes
    @settable_property
    def prefix(self): return self.__class__.__name__


# File parsing
def parse_file(filename, parser):
    result = None
    try:
        if filename.startswith("parlance://"):
            stream = resource_stream(__name__, filename.split("://")[1])
        else:
            stream = open(filename, 'rU', 1)
    except IOError, err:
        raise IOError("Failed to open configuration file %r %s" %
                (filename, err.args))
    
    try: result = parser(stream)
    finally: stream.close()
    return result

def read_representation_file(stream):
    ''' Parses a representation file.
        The first line contains a decimal integer, the number of tokens.
        The remaining lines consist of four hex digits, a colon,
        and the three-letter token name.
    '''#'''
    from language import Representation, protocol
    num_tokens = int(stream.readline().strip())
    if num_tokens > 0:
        rep = {}
        for line in stream:
            number = int(line[0:4], 16)
            name = line[5:8]
            uname = name.upper()
            if protocol.base_rep.has_key(uname):
                raise ValueError, 'Conflict with token ' + uname
            rep[number] = uname
            num_tokens -= 1
        if num_tokens == 0: return Representation(rep, protocol.base_rep)
        else: raise ValueError, 'Wrong number of lines in representation file'
    else: return protocol.default_rep


# Entry points
class EntryPointContainer(object):
    r'''Wrapper for a set of entry points, to be used like a dict.
        Keys are case-insensitive, to make admin commands easier.
    '''#"""#'''
    
    def __init__(self, group):
        self.group = group
    def __iter__(self):
        for item in iter_entry_points(self.group):
            yield item.name
    def __getitem__(self, name):
        for item in iter_entry_points(self.group, name):
            return item.load()
        else:
            for item in self:
                if item.lower() == name.lower():
                    return self[item]
            else:
                raise KeyError(name)
    def __contains__(self, name):
        lower = name.lower()
        return any(lower == n.lower() for n in self)

bots = EntryPointContainer("parlance.bots")
judges = EntryPointContainer("parlance.judges")
variants = EntryPointContainer("parlance.variants")


class ConfigPrinter(Configuration):
    ''' Collects options from all files in this package,
        and prints them as a sample configuration file.
    '''#'''
    
    class OrderedDict(dict):
        def __init__(self): self.keylist = []
        def __setitem__(self, key, value):
            if key not in self.keylist: self.keylist.append(key)
            dict.__setitem__(self, key, value)
        def keys(self): return self.keylist
    
    def __init__(self):
        # Yes, this deliberately skips Configuration.__init__()
        
        self.names = {
            'str': 'string',
            'int': 'integer',
            'bool': 'boolean',
            'float': 'number',
            'intlist': 'list of integers',
        }
        
        self.intro = (
            'Example configuration file for Parlance, a Diplomacy framework',
            '',
            'This file may be saved as parlance.cfg in either $HOME/.config or',
            'the program working directory; settings in the latter will override',
            'those in the former.',
            '',
            'Lines starting with hash marks (#) or semicolons (;) are ignored,',
            'and may be used for comments.  In this sample file, semicolons are',
            'used to show the default setting for each option.',
            '',
            'The sections are ordered in approximate likelihood of customization.',
        )
        
        # I should probably find a better place to put this information.
        # Perhaps I could simply collect it from parlance.cfg.sample?
        self.headers = headers = self.OrderedDict()
        headers['game'] = 'Parameters to be sent in the HLO message.'
        headers['server'] = 'Options for server operation.'
        headers['judge'] = 'Options for basic judge operation, including premature endings.'
        headers['clients'] = 'Options applicable for all Parlance clients.'
        headers['network'] = 'Settings for the network (DCSP) layer.'
        headers['main'] = 'Options used by the core program functionality.'
        headers['datc'] = ("Options from Lucas B. Kruijswijk's Diplomacy Adjudicator Test Cases.",
                'Not all options are supported; some cannot be, within DAIDE.',
                'Some options use letters not used by the DATC; in general,',
                'the syntax disallows the option entirely in these cases.')
        headers['tokens'] = 'Minor options for dealing with token conversion.'
        headers['syntax'] = ('Syntax files and special tokens.',
                'Note: File names are relative to the current working directory,',
                '      *not* the directory of this file.')
        
        self.modules = defaultdict(self.OrderedDict)
    
    def value_string(self, name, value):
        if isinstance(value, (list, tuple)):
            result = str.join(', ', (str(item) for item in value))
        elif value is False: result = 'no'
        elif value is True: result = 'yes'
        elif value is None: result = 'N/A'
        elif name.endswith('_bit'): result = hex(value)
        else: result = str(value)
        return result
    
    def add_option(self, section, name, option_type, default, alt_names, *help):
        #print '    %s.%s = %s' % (section, name, default)
        if any(opts.has_key(name) for opts in self.modules.values()):
            print '# Warning: Duplicate definition for option', name
        self.__super.add_option(section, name, option_type, default, alt_names, *help)
        
        if isinstance(alt_names, str) and len(alt_names) > 1:
            main_name = alt_names
        else: main_name = name
        
        type_name = option_type.__name__
        default_value = self.value_string(name, default)
        text = ['# %s (%s)' % (main_name, self.names.get(type_name, type_name))]
        text.extend('# ' + line for line in help)
        text.append(';%s = %s' % (name, default_value))
        
        current_value = self.value_string(name, getattr(self, name))
        if current_value != default_value:
            text.append('%s = %s' % (name, current_value))
        self.modules[section][name] = text
    
    def get_options(self, mname, container):
        for name, item in container.__dict__.iteritems():
            if isinstance(item, type) and item.__module__.split('.')[-1] == mname:
                section = item.__dict__.get('__section__', mname)
                opts = item.__dict__.get('__options__', ())
                #if opts: print '  Options in %s:' % item.__name__
                for option in opts: self.add_option(section, *option)
                if hasattr(item, '__dict__'): self.get_options(mname, item)
                #else: print '  Class %s has no __dict__?' % item.__name__
    
    def collect_modules(self, package):
        pack = __import__(package, {}, {}, [])
        for name in pack.__all__:
            try:
                module = getattr(pack, name)
            except AttributeError:
                __import__(str.join(".", (package, name)))
                module = getattr(pack, name)
            
            #print 'Processing %s as [%s]:' % (module.__name__, name)
            self.get_options(name, module)
    
    def print_section(self, section, comments):
        print
        print
        print '[%s]' % section
        for line in comments: print '#', line
        for option in self.modules[section].keys():
            print
            for line in self.modules[section][option]:
                print line
    
    def walk(self, package):
        self.collect_modules(package)
        for line in self.intro: print '#', line
        for section in self.headers.keys():
            header = self.headers[section]
            if isinstance(header, str): header = (header,)
            self.print_section(section, header)
        for section in sorted(self.modules.keys()):
            header = ('Options for the %s module.' % section,)
            if section not in self.headers: self.print_section(section, header)

def run():
    r'''Print out a configuration file template.
        Includes lines to reproduce the currently selected options.
    '''#'''
    ConfigPrinter().walk(__name__.rsplit(".", 1)[0])
