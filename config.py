from sys import path, argv
path.append('/home/bunburya/bin')

from subprocess import Popen, PIPE
from urllib.request import urlopen
from urllib.parse import quote as urlquote
from random import random, choice
from re import split
from os.path import join, expanduser, isdir
from os import mkdir
from hashlib import md5
from sys import version

from alias_handler import get_true_nick, get_aliases
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
from basearch import search
from twitter import get_tweets_from, get_tweet_text
from rps import RockPaperScissors

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
            ]

class CommandLib:
        
    def __init__(self, bot):
        self.bot = bot
        self.conn = bot.conn
        self.setup()
        self.addr_funcs = {}
        self.unaddr_funcs = {'!fortune': self.fortune, '!k': self.k,
                            '!stock': self.stock, '!maxim': self.maxim,
                            '!pep': self.pep, '!reddit': self.reddit,
                            '!help': self.help, '!fuck': self.fuck,
                            '!doc': self.doc, '!rpn': self.rpn, 
                            '!stats': self.stats, '!reload': self.reload,
                            '!msg': self.msg, '!euler': self.euler,
                            '!source': self.source, '!lol': self.lol,
                            '!admin': self.admin, '!google': self.google,
                            '!snowman': self.snowman, '!beer': self.beer,
                            '!twitter': self.twitter, '!rps': self.rps,
                            '!rps-optout': self.rps_optout}
        self.other_join_funcs = [self.msg_notify]
        self.other_nick_funcs = [self.msg_notify]
        self.all_privmsg_funcs = []
        self.admin_funcs = {'join': self.join, 'part': self.part, 'say': self.say,
                'nick': self.nick}
        
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
        
        # Rock Paper Scissors system
        rps_dir = join(self.store_dir, 'rps')
        self.rps_handler = RockPaperScissors(rps_dir)

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
        nick = get_true_nick(data['nick'])
        if args:    # send
            recip = get_true_nick(args.pop(0))
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
        """Reload the command library."""
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
        if not ''.join(args):
            self.conn.say('Give me a stock symbol.', data['channel'])
            return
        quotes = get_quote(' '.join(args))
        for co in quotes[:13]:
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
        for t in args[:13]:
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
        for t in args[:13]:
            ans = []
            docstr = doc_from_str(t)
            if docstr is None:
                v = version.split()[0]
                ans.append('Not found on Python {}.'.format(v))
            else:
                usage, docstring = (i.replace('\n', ' ').strip() for i in splitdoc(docstr))
                if usage:
                    ans.append(usage)
                if docstring:
                    ans.append(docstring)
            for a in ans:
                self.conn.say('{}: {}'.format(t, a), data['channel'])
            

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
        except ZeroDivisionError:
            self.conn.say('Division by zero.', data['channel'])

    def source(self, args, data):
        """Returns the link to my source code, at bunburya's GitHub."""
        self.conn.say('https://github.com/bunburya/bunbot', data['channel'])

    def euler(self, args, data):
        """Return a summary of, and link to, each of the specified Project Euler problems."""
        if not args:
            self.conn.say('Give me a problem number.', data['channel'])
        for arg in args[:13]:
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

    def google(self, args, data):
        """Return a Google search URL for the given query."""
        if not args:
            self.conn.say('Give me a query.', data['channel'])
            return
        query = urlquote(' '.join(args))
        url = 'http://www.google.com/search?q={}'.format(query)
        self.conn.say(url, data['channel'])

    def snowman(self, args, data):
        """A festive addition. Prints the unicode snowman character."""
        self.conn.say('\u2603', data['channel'])

    def k(self, args, data):
        """k"""
        self.conn.say('k', data['channel'])

    beer_result = '{} by {} ({})'
    more_beer = '{} more results at {}.'
    def beer(self, args, data):
        """Search for beer reviews at BeerAdvocate.com."""
        if not args:
            self.conn.say('Give me a beer name.', data['channel'])
            return
        limit = 3
        results, total, url = search(' '.join(args), limit)
        if not total:
            self.conn.say('No beers found.', data['channel'])
            return
        for r in results:
            self.conn.say(
                    self.beer_result.format(r.beer, r.brewer, r.beer_link),
                    data['channel']
                    )
        more = total - limit
        if more > 0:
            self.conn.say(self.more_beer.format(more, url), data['channel'])

    def twitter(self, args, data):
        """Return the last tweet of up to three given twitter users."""
        if not args:
            self.conn.say('Give me a twitter user.', data['channel'])
        names = args[:3]
        to_say = []
        for n in names:
            tweet = get_tweets_from(n, 1)
            text = get_tweet_text(tweet)
            if text:
                text = text[0].replace('\n', ' ')
            else:
                text = 'No tweets found.'
            to_say.append('{}: {}'.format(n, text))
        for line in to_say:
            self.conn.say(line, data['channel'])

    def _play_rps(self, challor, challee, challor_move):
        result = self.rps_handler.challenge(challor, challee, challor_move)
        if result is None:
            # Challenge only; no game took place
            return None
        if result is False:
            # Draw
            winner = False
            challee_move = challor_move
        else:
            winner = result
            if challor == winner:
                challee_move = self.rps_handler.get_losing_move(challor_move)
            else:
                challee_move = self.rps_handler.get_winning_move(challor_move)
        return winner, challee_move

    def rps(self, args, data):
        """With no args, list your current games. With opponent name as arg, list the status of your current game, if any, with that opponent. With opponent name and move as args, challenge opponent to a game or accept their challenge, playing the specified move."""
        nick = get_true_nick(data['nick'])
        optouts = self.rps_handler.get_optouts()
        if nick in optouts:
            self.conn.say('You have opted out of the Rock Paper Scissors system.', nick)
            self.conn.say('Send !rps-optout again to opt back in.', nick)
            return
        games = self.rps_handler.get_player_games(nick)
        if not args:
            if not games:
                self.conn.say('You have no current games.', nick)
            else:
                self.conn.say('player: your move', nick)
                for g in games:
                    self.conn.say('{}: {}'.format(g, games[g]), nick)
            return
        challee = get_true_nick(args.pop(0))
        if challee == nick:
            self.conn.say('Rock Paper Scissors is best played with two people.', nick)
            return
        if challee in optouts:
            self.conn.say('{} has opted out of the Rock Paper Scissors system.'.format(challee), nick)
            return
        if not args:
            if challee in optouts:
                self.conn.say('{} has opted out of the Rock Paper Scissors system.'.format(challee), nick)
            elif challee in games:
                self.conn.say('You are currently in a game with {}. You have played a {}.'.format(challee, games[challee]), nick)
            else:
                self.conn.say('You are not currently in a game with {}.'.format(challee), nick)
        elif len(args) > 1:
            self.conn.say('I need 0, 1 or 2 args.')
        else:
            if data['channel'].startswith('#'):
                self.conn.say('You should probably try that in a private message to me.', data['channel'])
                return
            move = self.rps_handler.get_move(args.pop())
            if move is None:
                self.conn.say('Valid commands are "rock", "paper", "scissors".', nick)
                return
            result = self._play_rps(nick, challee, move)
            if result is None:
                self.conn.say('You have challenged {} to a game of Rock Paper Scissors.'.format(challee), nick)
                self.conn.say('{} has challenged you to a game of Rock Paper Scissors.'.format(nick), challee)
                return
            winner, challee_move = result
            self.conn.say('You play a {}; {} plays a {}.'.format(move, challee, challee_move), nick)
            self.conn.say('You play a {}; {} plays a {}.'.format(challee_move, nick, move), challee)
            if winner is False:
                for p in (nick, challee):
                    self.conn.say('You draw!', p)
            else:
                loser = {nick, challee}.difference({winner}).pop()
                outcomes = {winner: 'win', loser: 'lose'}
                for p in outcomes:
                    self.conn.say('You {}!'.format(outcomes[p]), p)

    def rps_optout(self, args, data):
        """Opt in to or out of bunbot's Rock Paper Scissors system."""
        out = self.rps_handler.toggle_optout(data['nick'])
        inout = 'out of' if out else 'in to'
        self.conn.say('You have opted {} the Rock Paper Scissors system.'.format(inout), data['nick'])



    ###
    # Below are functions called every time a PRIVMSG is received.
    ###
    
    ###
    # Below are functions called when a person joins the channel
    ###

    def msg_notify(self, data):
        nick = get_true_nick(data['nick'])
        msgs = self.msg_handler.check_msgs(nick)
        if msgs:
            self.conn.say('You have {} messages. Say "!msg" to see them.'.format(len(msgs)),
                            nick)

    ###
    # Below are admin-related functions.
    ###
    
    def join(self, args, data):
        for chan in args:
            self.conn.join(chan)

    def part(self, args, data):
        for chan in args:
            self.conn.part(chan)

    def say(self, args, data):
        if args:
            chan = args[0]
            self.conn.say(' '.join(args[1:]), chan)

    def nick(self, args, data):
        if args:
            self.conn.nick(args[0])
