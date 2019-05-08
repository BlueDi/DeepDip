r'''Docstring test cases for Parlance modules
    Copyright (C) 2004-2008  Eric Wald
    
    This module runs docstring tests in selected Parlance modules.
    It should import them into the unittest framework for setuptools.
    
    Parlance may be used, modified, and/or redistributed under the terms of
    the Artistic License 2.0, as published by the Perl Foundation.
'''#'''

def _test():
    import doctest
    import sys
    
    from parlance import functions
    from parlance import gameboard
    from parlance import language
    from parlance import orders
    from parlance import validation
    from parlance import xtended
    
    # List of modules to test
    modules = [
        functions,
        gameboard,
        language,
        orders,
        validation,
    ]
    
    extension = dict((name, getattr(xtended, name)) for name in xtended.__all__)
    extension.update(language.protocol.base_rep)
    verbose = "-v" in sys.argv
    
    for mod in modules:
        print 'Testing', mod.__name__
        # Configure basic options assumed by docstrings
        opts = language.protocol.base_rep.options
        opts.squeeze_parens = False
        opts.output_escape = '"'
        opts.quot_char = '"'
        
        globs = mod.__dict__
        globs.update(extension)
        doctest.testmod(mod, verbose=verbose, report=0, globs=globs)
    doctest.master.summarize()

if __name__ == "__main__": _test()
