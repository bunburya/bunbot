from sys import path, argv
path.append('/home/bunburya/bin')

from subprocess import Popen, PIPE
from urllib.request import urlopen
from random import random, choice
from re import split
from os.path import join, expanduser, isdir
from os import mkdir
from hashlib import md5

from msg import MessageHandler, CorruptedFileError as MsgError
from stock import get_quote
from bf import gen_bf
from pep import main as pep
from reddit import rand_item
from pydoc import splitdoc
from doc import doc_from_str
from rpn import eval_rpn, InputError as RPNError
from euler import summary
from textgen import TextGenerator

class Identity:
    """
    This class contains some default settings for your bot, which will
    be used by the bot on startup (mainly for identification and joining).
    """
    
    ident = 'bunbot'
    serv = 'cube.netsoc.tcd.ie'
    host = 'irc.freenode.net'
    name = 'Botty Mc Botson'
    nick = 'bunbot'
    
    joins = [
            '#python-forum',
            '#reddit',
            '#xkcd',
            '#cooking',
            '#python-offtopic'
            ]

class CommandLib:
        
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.setup()
        self.addr_funcs = {}
        self.unaddr_funcs = {'!fortune': self.fortune, '!bf': self.bf,
                            '!stock': self.stock, '!maxim': self.maxim,
                            '!pep': self.pep, '!reddit': self.reddit,
                            '!help': self.help, '!fuck': self.fuck,
                            '!doc': self.doc, '!rpn': self.rpn, 
                            '!stats': self.stats, '!reload': self.reload,
                            '!msg': self.msg, '!euler': self.euler,
                            '!source': self.source, '!lol': self.lol,
                            '!markov': self.markov, '!save': self.save_markov,
                            '!admin': self.admin}
        self.all_privmsg_funcs = [self.feed_markov]
        self.other_join_funcs = [self.msg_notify]
        self.admin_funcs = {'join': self.join}
        
    def setup(self):
        """
        Here, we set up things that we will need for the functioning of
        the bot, such as initialising certain classes.
        """
        self.store_dir = expanduser('~/.bunbot')
        if not isdir(self.store_dir):
            mkdir(self.store_dir)
        
        # Setup for messaging system
        msg_file = join(self.store_dir, self.bot.ident.host)
        self.msg_handler = MessageHandler(msg_file)
        
        # Setup for markov text function
        markov_file = join(self.store_dir, 'markov')
        self.textgen = TextGenerator(markov_file)
        self.textgen.load()
        
        # Set up caches for various functions
        self.euler_cache = {}

        # Admin stuff
        self.admin_pass_file = join(self.store_dir, 'admin_pass')

    ###
    # Below are functions that can be called by other users within the channel
    ###
            
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

    def msg(self, args, data):
        """No arguments: Checks for messages sent to you. <nick> <message> as arguments: Send <message> to <nick>. This function uses your current nick, and does not perform any authentication. It is therefore not to be regarded as secure. Abuse of the system will result in a ban."""
        nick = data['nick']
        if args:    # send
            recip = args.pop(0)
            print(args)
            if not ''.join(args):
                self.conn.say('No message provided.', data['channel'])
                return
            msg = ' '.join(args)
            self.msg_handler.send_msg(nick, recip, msg)
            self.conn.say('Message sent.', data['channel'])
        else:       # check
            msgs = self.msg_handler.check_msgs(nick)
            if msgs:
                self.msg_handler.clear_msgs(nick)
                for msg, sender, time in msgs:
                    ans = '{} (sent by {} at {} (UTC))'.format(msg, sender, time)
                    self.conn.say(ans, nick)
            else:
                self.conn.say('No messages.', nick)
    
    def reload(self, args, data):
        self.bot.reload_cmds()
        self.conn.say('Command library reloaded.', data['channel'])
    
    def maxim(self, args, data):
        """Return a random maxim of equity."""
        self.conn.say(choice(self.maxims), data['channel'])

    def stats(self, args, data):
        """Return the link to the #python-forum stats page."""
        self.conn.say('http://bunburya.netsoc.ie/ircstats/python-forum.html', data['channel'])

    def _func_help(self, fnstr, chan):
        addr = fnstr
        unaddr = '!'+fnstr
        if addr in self.addr_funcs:
            ans = addr, getattr(self.addr_funcs[addr], '__doc__')
        elif unaddr in self.unaddr_funcs:
            ans = unaddr, getattr(self.unaddr_funcs[unaddr], '__doc__')
        else:
            ans = addr, 'Not found'
        self.conn.say('{}: {}'.format(*ans), chan)

    def _gen_help(self, chan):
        addr = ', '.join([i for i in self.addr_funcs.keys() if i])
        unaddr = ', '.join(self.unaddr_funcs.keys())
        if addr:
            self.conn.say('Commands that must be addressed to me: {0}'.format(addr), chan)
        if unaddr:
            self.conn.say('Commands that need not be addressed to me: {0}'.format(unaddr), chan)
    
    def help(self, args, data):
        """Return help on a specific function, or a list of available functions."""
        if args:
            for arg in args:
                self._func_help(arg, data['channel'])
        else:
            self._gen_help(data['channel'])

    def bf(self, args, data):
        """Returns the (verbose) brainfuck code to output the given text. Max 15 chars."""
        if not args:
            self.conn.say('Give me text.', data['channel'])
        text = ' '.join(args)
        if len(text) > 15:
            self.conn.say('String too long.', data['channel'])
            return
        bf = gen_bf(' '.join(args))
        for t in bf:
            self.conn.say(t,data['channel'])
    
    def stock(self, args, data):
        """Return stock prices and 24hr change for given stock symbols."""
        if not ''.join(args).isalpha():
            self.conn.say('Give me a stock symbol.', data['channel'])
            return
        quotes = get_quote(' '.join(args))
        for co in quotes:
            sym, price, change = co
            if price == '0.00' and change == 'N/A':
                self.conn.say('{} not found'.format(sym), data['channel'])
            else:
                self.conn.say('{}: {} ({} since yesterday)'.format(sym, price, change),
                            data['channel'])

    def fuck(self, args, data):
        """Give a fuck."""
        response = urlopen('http://rage.thewaffleshop.net').read().decode()
        self.conn.say(response, data['channel'])

    def fortune(self, args, data):
        """Return your fortune."""
        out = Popen(['fortune', '-s'], stdout=PIPE).stdout.read().decode()
        fortune = out.replace('\n', ' ').replace('\t', ' ')
        self.conn.say(fortune, data['channel'])

    def pep(self, args, data):
        """Return the titles of and links to the PEPs with the given numbers."""
        if not args:
            self.conn.say('Give me a PEP number.', data['channel'])
        for t in args:
            info = pep(t)
            for d in info:
                self.conn.say(d, data['channel'])

    def reddit(self, args, data):
        """Return a random link from Reddit."""
        if not args:
            sub = 'all'
        else:
            sub = args[0]
        post, link = rand_item(sub)
        if post is None:
            self.conn.say('{}: No such subreddit.'.format(sub),
                            data['channel'])
        else:
            self.conn.say('{} ({})'.format(post, link), data['channel'])
        
    def doc(self, args, data):
        """Return documentation for the given Python objects."""
        if not args:
            self.conn.say('Give me a Python object.', data['channel'])
        for t in args:
            docstr = doc_from_str(t)
            if docstr is None:
                ans = 'Not found.'
            else:
                splitted = splitdoc(docstr)[1].replace('\n', ' ').strip()
                if not splitted:
                    ans = 'Has no docstring.'
                else:
                    ans = splitted
            self.conn.say('{}: {}'.format(t, ans), data['channel'])
            

    def rpn(self, args, data):
        """Evaluate a sequence of operators and operands according to the rules of Reverse Polish Notation."""
        if not args:
            self.conn.say('Give me an RPN sequence.', data['channel'])
            return
        try:
            self.conn.say(str(eval_rpn(*args)), data['channel'])
        except RPNError as err:
            self.conn.say('Invalid RPN sequence. {}'.format(err.args[0]),
                            data['channel'])
        except OverflowError:
            self.conn.say('Result too large.', data['channel'])

    def source(self, args, data):
        self.conn.say('https://github.com/bunburya/bunbot', data['channel'])

    def euler(self, args, data):
        """Return a summary of, and link to, each of the specified Project Euler problems."""
        if not args:
            self.conn.say('Give me a problem number.', data['channel'])
        for arg in args:
            if arg in self.euler_cache:
                summ, url = self.euler_cache[arg]
            else:
                summ, url = summary(arg)
                self.euler_cache[arg] = (summ, url)
            ans = '{} ({})'.format(summ, url) if summ else 'Not found.'
            self.conn.say('Problem {}: {}'.format(arg, ans), data['channel'])
            
    def lol(self, args, data):
        """..."""
        self.conn.say('wat', data['channel'])

    def markov(self, args, data):
        text = self.textgen.get_text(count=20)
        if text:
            self.conn.say(text, data['channel'])
        else:
            self.conn.say('No text recorded.', data['channel'])

    def save_markov(self, args, data):
        self.textgen.save()

    def admin(self, args, data):
        """Nothing to see here."""
        if len(args) < 2:
            return
        with open(self.admin_pass_file, 'rb') as f:
            pass_hash = f.read()
        given_hash = md5(args.pop(0).encode()).digest()
        if not (given_hash == pass_hash):
            return
        cmd = args.pop(0)
        if cmd in self.admin_funcs:
            self.admin_funcs[cmd](args, data)

    ###
    # Below are functions called every time a PRIVMSG is received.
    ###
    
    def feed_markov(self, args, data):
        self.textgen.learn(' '.join(args))        

    ###
    # Below are functions called when a person joins the channel
    ###

    def msg_notify(self, data):
        msgs = self.msg_handler.check_msgs(data['nick'])
        if msgs:
            self.conn.say('You have {} messages. Say "!msg" to see them.'.format(len(msgs)),
                            data['channel'], data['nick'])

    ###
    # Below are admin-related functions.
    ###
    
    def join(self, args, data):
        for chan in args:
            self.conn.join(chan)
