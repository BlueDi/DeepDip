r'''Parlance standard map environment
    Copyright (C) 2004-2008  Eric Wald
    
    This module includes the standard map, default map tokens, and starting
    position messages. It can take a few seconds to load, and might not work
    properly, but offers a convenient way to import all those names.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''
from sys       import modules

from gameboard import Map, Variant
from language  import protocol


mini = Variant("mini", filename="parlance://data/mini.cfg")
small = Variant("small", filename="parlance://data/small.cfg")
standard = Variant("standard", filename="parlance://data/standard.cfg")

__all__ = ['mini', 'mini_map', 'mini_sco', 'mini_now',
        'small', 'small_map', 'small_sco', 'small_now',
        'standard', 'standard_map', 'standard_sco', 'standard_now',
		'default_rep', 'base_rep']

# Mini map and its various attendants
mini_map = Map(small)
mini_sco = small.sco()
mini_now = small.now()

# Small map and its various attendants
small_map = Map(small)
small_sco = small.sco()
small_now = small.now()

# Standard map and its various attendants
standard_map = Map(standard)
standard_sco = standard.sco()
standard_now = standard.now()

default_rep = protocol.default_rep
base_rep = protocol.base_rep

# Tokens of the standard map
module = modules[__name__]
for name, token in default_rep.items():
    setattr(module, name, token)
__all__.extend(default_rep.keys())

