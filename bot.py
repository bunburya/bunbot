#!/usr/bin/env python3

from imp import reload

import config, connect

class Bot:
    
    def __init__(self):
        self.ident = config.Identity()
        self.conn = connect.IRCConn(self)
        self.cmds = config.CommandLib(self)
        self.conn.connect()
        self.conn.mainloop()
    
    def reload_cmds(self):
        self.cmds = reload(config).CommandLib(self)
    
    def handle_privmsg(self, tokens, sender):
        chan = tokens.pop(0)
        tokens[0] = tokens[0].strip(':')
        if tokens[0] == self.ident.nick:
            tokens.pop(0)
            is_to_me = True
        else:
            is_to_me = False

        nick, host = sender.split('!')        
        data = {'channel': chan, 'sender': sender, 'is_to_me': is_to_me,
                'nick': nick, 'host': host}
        
        cmd = tokens[0]
        try:
            args = tokens[1:]
        except IndexError:
            args = []
        
        if is_to_me and (cmd in self.cmds.addr_funcs):
            return self.cmds.addr_funcs[cmd](args, data)
        elif cmd in self.cmds.unaddr_funcs:
            return self.cmds.unaddr_funcs[cmd](args, data)

    def handle_other_join(self, tokens, joiner):
        chan = tokens.pop()
        nick, host = joiner.split('!')
        data = {'channel': chan, 'joiner': joiner, 'nick': nick, 'host': host}
        for func in self.cmds.other_join_funcs:
            func(data)
        

if __name__ == '__main__':
    Bot()
