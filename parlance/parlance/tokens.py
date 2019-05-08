r'''Parlance core language tokens
    Copyright (C) 2004-2008  Eric Wald
    
    This module is designed to be used as "from tokens import *".
    It includes all of the token from the core protocol, with upper-case
    names, including BRA ('(') and KET (')'), but not including provinces
    or powers from the standard map.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

from sys import modules

from language import protocol

__all__ = protocol.base_rep.keys()

module = modules[__name__]
for name in __all__:
    setattr(module, name, protocol.base_rep[name])
