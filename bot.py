#!/usr/bin/env python3
# -*- coding: iso-8859-15 -*-

import socket
from subprocess import Popen, PIPE

# Importing functionality from other scripts
from sys import path, argv
path.append('/home/bunburya/bin')


from urllib.request import urlopen
from stock import get_quote
from bf import gen_bf
from re import split
from random import random, choice
from pep import main as pep
from reddit import rand_item
from pydoc import splitdoc
from doc import doc_from_str
from rpn import eval_rpn, InputError as RPNError

class Bot:
    
    def __init__(self, host=False, chan=False, nick=False):
        # Define required instance variables
        self.serv = 'cube.netsoc.tcd.ie'
        self.host = host or 'irc.netsoc.tcd.ie'
        self.port = 6667
        self.nick = nick or 'lawlburya'
        self.ident = 'lawlburya'
        self.name = 'Botty McBotson'
        self.owner = 'bunburya'
        self.channel = chan or '#bots'
        
        # Initialise dictionaries of commands, to be replaced/supplemented later.
        self.addr_funcs = {}
        self.unaddr_funcs = {}
        self.expr_funcs = {}
        self.regex_funcs = {} # not implemented yet
    
    def handle_error(self, tokens):
        print('error. tokens:', tokens)
        self.connect()

    def handle_privmsg(self, tokens, sender):
        chan = tokens.pop(0)
        tokens[0] = tokens[0].strip(':')
        if tokens[0] == self.nick:
            tokens.pop(0)
            is_to_me = True
        else:
            is_to_me = False
        
        if is_to_me:
            try:
                cmd = tokens.pop(0)
            except IndexError:
                cmd = ''
            #print(cmd, self.addr_funcs, cmd in self.addr_funcs)
            if cmd in self.addr_funcs:
                return self.addr_funcs[cmd](tokens, sender, chan)
            #else:
            #    self.help()
        else:
            if tokens[0].strip(':') in self.unaddr_funcs:
                cmd = tokens.pop(0)
                return self.unaddr_funcs[cmd](tokens, sender, chan)
                
            for word in self.expr_funcs:
                if word in ' '.join(tokens):
                    return self.expr_funcs[word](tokens, sender, chan)

    
    def say(self, msg, chan=None):
        """say(chan, msg): Say msg on chan."""
        if chan is None:
            chan = self.channel
        cmd = 'PRIVMSG'
        self._send('{0} {1} :{2}'.format(cmd, chan, msg))
    
    def pong(self, trail):
        cmd = 'PONG'
        self._send('{0} {1}'.format(cmd, trail))
    
    def _send(self, msg):
        """Send something (anything) to the IRC server."""
        print('sending: {0}\r\n'.format(msg))
        self.s.send('{0}\r\n'.format(msg).encode())
    
    def parse(self, line):
        if not line:
            # empty line; this should throw up an error.
            return
        line = line.strip('\r\n')
        tokens = line.split(' ')
        if tokens[0].startswith(':'):
            prefix = tokens.pop(0)[1:]
        else:
            prefix = ''
        
        cmd = tokens.pop(0)
        
        if cmd == '433':
            self.nick += '_'
            self._send('NICK {0}'.format(self.nick))
        if cmd == '376':    # this means end of MOTD
            self.on_connect()
        if cmd == 'PING':
            self.pong(' '.join(tokens))
        elif cmd == 'PRIVMSG':
            self.handle_privmsg(tokens, prefix)
        elif cmd == 'ERROR':
            self.handle_error(tokens)
    
    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        self._send('USER {0} {1} {2} :{3}'.format(self.ident, self.host, self.serv, self.name))
        self._send('NICK {0}'.format(self.nick))
        # we send join in the on_connect method
    
    def on_connect(self):
        self._send('JOIN {0}'.format(self.channel))

    def receive(self):
        buf = []
        while True:
            nxt_ch = None
            ch = self.s.recv(1)
            if ch == b'\r':
                nxt_ch = self.s.recv(1)
                if nxt_ch == b'\n':
                    try:
                        line = b''.join(buf).decode()
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        self.handle_encoding_error()
                        return ''
                    print('received:', line)
                    return line
            buf.append(ch)
            if nxt_ch:
                buf.append(nxt_ch)
            
            
        if not line.strip():
            return None
        else:
            try:
                parsable = line.strip(b'\r\n').decode()
                print('received:', parsable)
                return parsable
            except (UnicodeEncodeError, UnicodeDecodeError):
                self.handle_encoding_error()
    
    def mainloop(self):

        while True:
            line = self.receive()
            self.parse(line)
                
    def handle_encoding_error(self):
        self.say('You\'re talking gibberish man.')

class BunBot:

    def __init__(self, host=False, chan=False, nick=False, spam_factor=0):
        self.bot = Bot(host, chan, nick)
        self.spam_factor = spam_factor
        self.bot.addr_funcs = {'stock': self.stock, '': self.help, 'help': self.help}
        self.bot.unaddr_funcs = {'!fortune': self.fortune, '!bf': self.bf, '!stock': self.stock, '!maxim': self.maxim, '!pep': self.pep, '!reddit': self.reddit,
                                 '!help': self.help, '!fuck': self.fuck, '!doc': self.doc, '!rpn': self.rpn}
        self.bot.expr_funcs = {'': self.spam}
        self.bot.connect()
        self.bot.mainloop()    

    spam_msgs = ['You always say that {nick}!',
                 'LOL, typical {nick}!',
                 'LMAO, that was a classic {nick} line!',
                 'Er, {nick}, I think you\'ve had a bit too much to drink...',
                 'You know {nick}, you\'re really not as funny as you think you are.']
    
    maxims =    ['Equity will not suffer a wrong to be without a remedy.',
                 'Equity follows the law.',
                 'He who seeks equity must do equity.',
                 'He who comes to equity must come with clean hands.',
                 'Delay defeats equity.',
                 'Equality is equity.',
                 'Equity looks to the intent rather than the form.',
                 'Equity looks on that as done which ought to have been done.',
                 'Equity imputes an intention to fulfil an obligation.',
                 'Equity acts in personam.',
                 'Where the equities are equal, the first in time prevails.',
                 'Where the equities are equal, the law prevails.']
    
    def maxim(self, tokens, sender, chan):
        """Return a random maxim of equity."""
        self.bot.say(choice(self.maxims), chan)
    
    def spam(self, tokens, sender, chan):
        n = sender.split('!')[0]
        if random() < self.spam_factor:
            self.bot.say(choice(self.spam_msgs).format(nick=n), chan)

    def func_help(self, fnstr):
        addr = fnstr
        unaddr = '!'+fnstr
        if addr in self.bot.addr_funcs:
            ans = addr, getattr(self.bot.addr_funcs[addr], '__doc__')
        elif unaddr in self.bot.unaddr_funcs:
            ans = unaddr, getattr(self.bot.unaddr_funcs[unaddr], '__doc__')
        else:
            ans = addr, 'Not found'
        self.bot.say('{}: {}'.format(*ans))

    def gen_help(self):
        addr = ', '.join([i for i in self.bot.addr_funcs.keys() if i])
        unaddr = ', '.join(self.bot.unaddr_funcs.keys())
        if addr:
            self.bot.say('Commands that must be addressed to me: {0}'.format(addr))
        if unaddr:
            self.bot.say('Commands that need not be addressed to me: {0}'.format(unaddr))
    
    def help(self, tokens, sender, chan):
        """Return help on a specific function, or a list of available functions."""
        if tokens:
            for t in tokens:
                self.func_help(t)
        else:
            self.gen_help()

    def bf(self, tokens, sender, chan):
        """Returns the (verbose) brainfuck code to output the given text. Max 15 chars."""
        if not tokens:
            self.bot.say('Give me text.')
        text = ' '.join(tokens)
        if len(text) > 15:
            self.bot.say('String too long.')
            return
        bf = gen_bf(' '.join(tokens))
        for t in bf:
            self.bot.say(t, chan)
        
        #for i in range(0, len(bf), 100):
        #    try: self.bot.say(bf[i:i+100], chan)
        #    except IndexError: return
    
    def stock(self, tokens, sender, chan):
        """Return stock prices and 24hr change for given stock symbols."""
        if not ''.join(tokens).isalpha():
            self.bot.say('Give me a stock symbol.', chan)
            return
        data = get_quote(' '.join(tokens))
        for co in data:
            sym, price, change = co
            if price == '0.00' and change == 'N/A':
                self.bot.say('{s} not found'.format(s=sym))
            else:
                self.bot.say('{s}: {p} ({c} since yesterday)'.format(s=sym, p=price, c=change), chan)

    def fuck(self, tokens, sender, chan):
        """Give a fuck."""
        response = urlopen('http://rage.thewaffleshop.net').read().decode()
        self.bot.say(response, chan)

    def fortune(self, tokens, sender, chan):
        """Return your fortune."""
        out = Popen(['fortune', '-s'], stdout=PIPE).stdout.read().decode()
        fortune = out.replace('\n', ' ').replace('\t', ' ')
        self.bot.say(fortune, chan)

    def pep(self, tokens, sender, chan):
        """Return the titles of and links to the PEPs with the given numbers."""
        if not tokens:
            self.bot.say('Give me a PEP number.', chan)
        for t in tokens:
            info = pep(t)
            for d in info:
                self.bot.say(d, chan)

    def reddit(self, tokens, sender, chan):
        """Return a random link from Reddit."""
        if not tokens:
            sub = 'all'
        else:
            sub = tokens[0]
        post = rand_item(sub)
        if post is None:
            self.bot.say('{}: No such subreddit.'.format(sub))
        else:
            self.bot.say('{} ({})'.format(*post))
        
    def doc(self, tokens, sender, chan):
        """Return documentation for the given Python objects."""
        if not tokens:
            self.bot.say('Give me a Python object.')
        for t in tokens:
            docstr = doc_from_str(t)
            print(docstr)
            if docstr is None:
                ans = 'Not found.'
            else:
                splitted = splitdoc(docstr)[1].replace('\n', ' ').strip()
                if not splitted:
                    ans = 'Has no docstring.'
                else:
                    ans = splitted
            self.bot.say('{}: {}'.format(t, ans))
            

    def rpn(self, tokens, sender, chan):
        """Evaluate a sequence of operators and operands according to the rules of Reverse Polish Notation."""
        if not tokens:
            self.bot.say('Give me an RPN sequence.')
            return
        try:
            self.bot.say(str(eval_rpn(*tokens)))
        except RPNError as err:
            self.bot.say('Invalid RPN sequence. {}'.format(err.args[0]))

    def ronpaul(self, tokens, sender, chan):
        """A random quote from, or factoid about, Glorious Leader Ron Paul, courtesy of r/circlejerk."""
        self.bot.say(paulquote())

if __name__ == '__main__':
    BunBot(*argv[1:])
