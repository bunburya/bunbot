#!/usr/bin/env python3

from imp import reload
from re import findall
from collections import OrderedDict, deque
from os.path import dirname, join
from logging import getLogger, FileHandler, Formatter
from copy import deepcopy

import connect
from config import get_config
from plugin_handler import PluginHandler
from sys import argv

class MessageData:
    
    def __init__(self):
        self.irc_cmd = None
        self.to = None
        self.from_nick = None
        self.from_host = None
        self.tokens = None
        self.string = None
        self.regex_match = None
        self.is_ctcp = None
        self.ctcp_cmd = None
        self.trailing = None    # this is a tokenised version of the last token
                                # (eg, the message part of a PRIVMSG) 

    def copy(self):
        new = MessageData()
        new.irc_cmd = deepcopy(self.irc_cmd)
        new.to = deepcopy(self.to)
        new.from_nick = deepcopy(self.from_nick)
        new.from_host = deepcopy(self.from_host)
        new.tokens = deepcopy(self.tokens)
        new.string = deepcopy(self.string)
        new.regex_match = self.regex_match #Can't deepcopy match object
        new.is_ctcp = deepcopy(self.is_ctcp)
        new.ctcp_cmd = deepcopy(self.ctcp_cmd)
        new.trailing = deepcopy(self.trailing)
        return new

class History:
    
    def __init__(self, bot, chan, limit=200):
        self.bot = bot
        self.chan = chan
        self.limit = limit
        self.data = deque(maxlen=limit)

    def add_message(self, msg):
        self.data.append(msg.copy())
        print('added: {}'.format(msg.copy().trailing))
    
    def __iter__(self):
        self._iter = reversed(self.data)
        return self
    
    def __next__(self):
        return next(self._iter)
    
    
class HandlerLib:
    
    """This class contains functions for handling various IRC events."""
    
    def __init__(self, bot):
        self.bot = bot
        self.ident = bot.ident
        self.conn = bot.conn
    
    def handle_connect(self, data):
        """
        Called once we have connected to and identified with the server.
        Mainly joins the channels that we want to join at the start.
        """
        self.plugin_handler.exec_hooks('on_connect', None, data)
        for chan in self.bot.joins:
            self.bot.join(chan)

    def handle_nick_in_use(self, data):
        self.ident.nick += '_'
        self.conn.connect()
    
    def handle_ping(self, data):
        self.plugin_handler.exec_hooks('ping', None, data)

    def handle_join(self, data):
        if data.from_nick != self.ident.nick:
            self.plugin_handler.exec_other_join(data)
        else:
            self.plugin_handler.exec_self_join(data)

    def handle_privmsg(self, data):
        
        # Add message to History.
        # This should be done before data is modified
        # (TODO: Is data modified by the below code? should it be?)
        self.bot.histories[data.to].add_message(data)

        # At this stage we should have one token, which is the message;
        # now break this out so that each token is a word
        self.plugin_handler.exec_privmsg_re_if_exists(data)
        self.plugin_handler.exec_privmsg(data)
        self.plugin_handler.exec_cmd_if_exists(data)
        
    def handle_nick(self, data):
        if data.from_nick != self.ident.nick:
            self.plugin_handler.exec_hooks('other_nick_change', '', data)

    def handle_part(self, data):
        if data.from_nick != self.ident.nick:
            self.plugin_handler.exec_hooks('other_part', None, data)

    def handle_quit(self, data):
        self.handle_part(data)  # for now

    def handle_errors(self, data):
        print('ERROR:', data.string)

    def handle_ctcp(self, data):
        if data.ctcp_cmd == 'ACTION':
            self.plugin_handler.exec_hooks('action', None, data)
    
    def get_handler(self, data):
        """This is the function that is called externally.  It decides
        which handler should be used and calls that handler."""
        cmd = data.irc_cmd
        if cmd == '433':    # nick already in use
            handler = self.handle_nick_in_use
        elif cmd == '376':    # end of MOTD
            handler = self.handle_connect
        elif cmd == 'PING':
            handler = self.handle_ping
        elif cmd == 'ERROR':
            handler = self.handle_errors
        elif cmd == 'JOIN':
            data.to = data.tokens.pop(0)
            handler = self.handle_join
        elif cmd == 'PRIVMSG':
            data.to = data.tokens.pop(0)
            # If message is to me, pretend "channel" is the sender
            if data.to == self.ident.nick:
                data.to = data.from_nick
            if data.trailing[0].startswith('\x01') and data.trailing[-1].endswith('\x01'):
                # CTCP command
                data.is_ctcp = True
                data.ctcp_cmd = data.trailing.pop(0).lstrip('\x01')
                handler = self.handle_ctcp
            else:
                data.is_ctcp = False
                handler = self.handle_privmsg
        elif cmd == 'NICK':
            data.to = data.tokens.pop(0)
            handler = self.handle_nick
        elif cmd == 'QUIT':
            handler = self.handle_quit
        elif cmd == 'PART':
            data.to = data.tokens.pop(0)
            handler = self.handle_part
        else:
            handler = lambda d: True    # this is probably not the best 
        return handler

    @property
    def plugin_handler(self):
        return self.bot.plugin_handler

class Identity:

    def __init__(self, vals):
        self.host = vals['host']
        self.serv = vals['server']
        self.ident = vals['ident']
        self.name = vals['name']
        self.nick = vals['nick']

class Bot:

    valid_hooks = {
            'command',
            'privmsg_re'
            # TODO: implement more
            }
   
    history_limit = 200

    def __init__(self, config):
        self.config = config
        self.ident = Identity(config['identity'])
        self.joins = config['channels']['join'].split()
        self.ignores = set(config['misc']['ignore'].split())
        self.hooks = {hook_type: OrderedDict() for hook_type in self.valid_hooks}
        self.conn = connect.IRCConn(self)
        self.handlers = HandlerLib(self)
        self.histories = {}
        self.plugin_handler = PluginHandler(self, join(dirname(__file__), 'plugins'))
        self.conn.connect()
        try:
            self.conn.mainloop()
        except BaseException as e:
            self.handle_exception(e)

    def handle_exception(self, e):
        raise e
    
    def parse(self, line):
        if not line:
            # empty line; this should throw up an error.
            return
        line = line.strip('\r\n')
        tokens = line.split()
        if tokens[0].startswith(':'):
            # Prefix, ie host from which message originated.

            # Not sure if this if-else is necessary, as possibly lines
            # always start with ":"
            prefix = tokens.pop(0)[1:].strip(':')
        else:
            prefix = ''
        
        # IRC command, eg "NOTICE", "PRIVMSG" etc
        cmd = tokens.pop(0)

        data = MessageData()
        data.irc_cmd = cmd
        try:
            data.from_nick, data.from_host = prefix.split('!')
        except ValueError:
            pass

        if data.from_nick in self.ignores:
            print('ignoring {}'.format(data.from_nick))
            return
                    
        for i, t in enumerate(tokens):
            if t.startswith(':'):
                # Last token is everything after :
                # data.trailing is last token, split by space

                # data.trailing has the semicolon removed but
                # last token in data.tokens does not
                data.trailing = [tokens[i][1:]] + tokens[i+1:]
                print(data.trailing)
                data.tokens = tokens[:i] + [' '.join(tokens[i:])]
                break
            if data.tokens is None:
                data.tokens = tokens
        data.string = ' '.join(data.tokens)
        handler = self.handlers.get_handler(data)
        handler(data)
    
    def join(self, chan):
        self.conn.join(chan)
        self.histories[chan] = History(self, chan, self.history_limit)

    
    def reload_cmds(self):
        self.cmds = reload(config).CommandLib(self)
        
def main(*args):
    if not args:
        print('You must at least specify a host server to connect to.')
        return 1
    host = args[0]
    cfgdir = join(dirname(__file__), 'configs')
    conf = get_config(cfgdir, host)
    if conf is None:
        print('No config file found or config file incomplete.')
        return 1
    Bot(conf)

if __name__ == '__main__':
    main(*argv[1:])
