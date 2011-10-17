#!/usr/bin/env python3

from connect import IRCConn
from config import CommandLib, Identity

class Bot:
    
    def __init__(self):
        self.ident = Identity()
        self.conn = IRCConn(self)
        self.cmds = CommandLib(self)
        self.conn.connect()
        self.conn.mainloop()
    
    def handle_privmsg(self, tokens, sender):
        chan = tokens.pop(0)
        tokens[0] = tokens[0].strip(':')
        if tokens[0] == self.ident.nick:
            tokens.pop(0)
            is_to_me = True
        else:
            is_to_me = False
        
        data = {'channel': chan, 'sender': sender, 'is_to_me': is_to_me}
        
        cmd = tokens[0]
        try:
            args = tokens[1:]
        except IndexError:
            args = []
        
        if is_to_me and (cmd in self.cmds.addr_funcs):
            return self.cmds.addr_funcs[cmd](args, data)
        elif cmd in self.cmds.unaddr_funcs:
            return self.cmds.unaddr_funcs[cmd](args, data)

if __name__ == '__main__':
    Bot()
