============================
Parlance Diplomacy Framework
============================

--------------
About Parlance
--------------

Parlance is a framework for playing the `Diplomacy`_ board game over a network,
using the protocol and message syntax developed by the `Diplomacy AI
Development Environment`_ (DAIDE) community.

The Parlance server differs from the official DAIDE server in that it can serve
multiple games (consecutively or concurrently), is more configurable, can be
managed remotely through admin commands, and accepts a slightly broader message
syntax.

Parlance also includes a framework for clients, including a command-line game
observer, and can be used as a library for computer players (bots).

Parlance may be used, modified, and/or redistributed under the terms of
the `Artistic License 2.0`_, as published by the Perl Foundation.

.. _Diplomacy: http://en.wikipedia.org/wiki/Diplomacy_(game)
.. _Diplomacy AI Development Environment: http://www.daide.org.uk/index.xml
.. _Artistic License 2.0: http://www.perlfoundation.org/artistic_license_2_0


--------
Commands
--------

Parlance installs the following commands:

parlance-server
  Starts a game server

parlance-holdbot
  Starts one or more HoldBots

parlance-chatty
  Starts a game observer

parlance-config
  Prints out an example configuration file

parlance-raw-client
  Connects to a server, translating network messages to and from DAIDE message
  syntax on standard input and output.

parlance-raw-server:
  Listens for clients, translating network messages to and from DAIDE message
  syntax on standard input and output.


------------
Installation
------------

Parlance can be installed with `Easy Install`_ from a command prompt::

    > easy_install parlance

Alternatively, once you have downloaded and unpacked a source distribution, you
can install it with::

    > python setup.py install

.. _Easy Install: http://peak.telecommunity.com/DevCenter/EasyInstall

-------
Credits
-------

* Daniel Loeb started the `Diplomacy Programming Project`_ in 1990, developing
  a language for communication between computer players and a GM.

* Andrew Rose developed the `network protocol`_ used to connect clients to the
  server, and wrote a DLL implementation of it.

* David Norman extended the DPP communication language into the `DAIDE message
  syntax`_, translated several variant maps into it, and wrote the first
  full-featured server, bot, and graphical player interface to use the DAIDE
  protocols.

* Eric Wald wrote the first versions of Parlance to extend the DAIDE
  environment to non-Windows platforms, particularly Linux.

.. _Diplomacy Programming Project: http://www.diplom.org/Zine/S1995M/Loeb/Project.html
.. _DAIDE message syntax: http://www.ellought.demon.co.uk/dipai/dpp_syntax.rtf
.. _network protocol: http://www.daide.org.uk/external/comproto.html

