#!/usr/bin/env python3

from imp import reload
from re import findall
from collections import OrderedDict

import config, connect

class MessageData:
    
    def __init__(self):
        self.irc_cmd = None
        self.to = None
        self.from_nick = None
        self.from_host = None
        self.channel = None
        self.tokens = None
        self.string = None


class Bot:

    valid_hooks = {
            'command',
            'privmsg_re'
            # TODO: implement more
            }
    
    def __init__(self, host=None, chan=None, nick=None):
        self.ident = config.Identity()
        if host:
            self.ident.host = host
        if chan:
            self.ident.joins = [chan]
        if nick:
            self.ident.nick = nick
            self.ident.ident = nick

        self.hooks = {hook_type: OrderedDict() for hook_type in self.valid_hooks}

        self.conn = connect.IRCConn(self)
        self.cmds = config.CommandLib(self)
        self.conn.connect()
        self.conn.mainloop()
    
    def on_connect(self, data):
        """
        Called once we have connected to and identified with the server.
        Mainly joins the channels that we want to join at the start.
        """
        for chan in self.ident.joins:
            self.conn.join(chan)
    
    def handle_nick_in_use(self, data):
        self.ident.nick += '_'
        self.conn.connect()
    
    def handle_ping(self, data):
        self.conn.pong(data.string)

    def handle_join(self, data):
        if data.from_nick != self.ident.nick:
            for func in self.cmds.other_join_funcs:
                func(data)
    
    def handle_privmsg(self, data):
        
        try:
            cmd = tokens[0]
        except IndexError:
            cmd = None
        try:
            args = tokens[1:]
        except IndexError:
            args = []
        
        if is_to_me and (cmd in self.cmds.addr_funcs):
            self.cmds.addr_funcs[cmd](args, data)
        elif cmd in self.cmds.unaddr_funcs:
            self.cmds.unaddr_funcs[cmd](args, data)
        else:
            for func in self.cmds.all_privmsg_funcs:
                func(tokens, data)
            for pattern in self.cmds.regex_funcs:
                groups = findall(pattern, ' '.join(tokens))
                if groups:
                    self.cmds.regex_funcs[pattern](groups)
        
    def handle_nick(self, data):
        if data.from_nick != self.ident.nick:
            self.hooks['other_nick_change'][''](data)
    
    def parse(self, line):
        if not line:
            # empty line; this should throw up an error.
            return
        line = line.strip('\r\n')
        tokens = line.split()
        if tokens[0].startswith(':'):
            prefix = tokens.pop(0)[1:].strip(':')
        else:
            prefix = ''
        
        cmd = tokens.pop(0)

        # Maybe best to create MessageData here??
        data = MessageData()
        data.irc_cmd = cmd
        if prefix:
            data.from_nick, data.from_host = prefix.split('!')

        if cmd == '433':    # nick already in use
            handler = self.handle_nick_in_use
        elif cmd == '376':    # end of MOTD
            handler = self.on_connect
        elif cmd == 'PING':
            handler = self.handle_ping
        elif cmd == 'ERROR':
            handler = self.handle_errors
        elif cmd == 'JOIN':
            data.to = tokens.pop(0)
            handler = self.handle_join
        elif cmd == 'PRIVMSG':
            data.to = tokens.pop(0)
            handler = self.handle_privmsg
        elif cmd == 'NICK':
            data.to = tokens.pop(0)
            handler = self.handle_nick
        
        data.tokens = tokens
        data.string = ' '.join(tokens)
        handler(data)

    def add_hook(self, hook_type, key, func):
        # empty key will always fire
        self.hooks[hook_type][key] = func
    
    def fire_hook(self, hook_type, key, data):
        try:
            self.hooks[hook_type][key](data)
        except KeyError:
            # should probably do something here
            pass
    
    def reload_cmds(self):
        self.cmds = reload(config).CommandLib(self)
        

if __name__ == '__main__':
    from sys import argv
    Bot(*argv[1:])
