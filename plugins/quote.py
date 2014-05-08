from os import mkdir
from os.path import exists, basename, join
from random import choice
from json import load, dump
from sys import version_info

if version_info.minor < 3:
    FileNotFoundError = IOError

class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.name = basename(__file__).rstrip('.py')
        self.quotes_file = self.get_quotes_file()
        self.hooks = [
                {'type': 'command', 'key': '!add_quote', 'func': self.add_quote},
                {'type': 'command', 'key': '!quote', 'func': self.get_quote},
                {'type': 'command', 'key': '!del_quote', 'func': self.del_quote},
                {'type': 'command', 'key': '!nuke_quotes', 'func': self.nuke_quotes}
                ]

    def _load_quotes(self):
        try:
            with open(self.quotes_file) as f:
                quotes = load(f)
        except FileNotFoundError:
            quotes = {}
        except ValueError:
            quotes = {'error': 'Error loading quotes file. '
                        'Operation could not complete.'}
        return quotes
    
    def _save_quotes(self, quotes):
        with open(self.quotes_file, 'w') as f:
            dump(quotes, f)

    def get_quotes_file(self):
        plugin_dir = self.handler.plugin_dir
        serv = self.bot.ident.host
        name = self.name

        data_dir = join(plugin_dir, 'data')
        if not exists(data_dir):
            mkdir(data_dir)
        serv_dir = join(data_dir, serv)
        if not exists(serv_dir):
            mkdir(serv_dir)
        name_dir = join(serv_dir, name)
        if not exists(name_dir):
            mkdir(name_dir)
        quotes_file = join(name_dir, 'quotes.json')
        if not exists(quotes_file):
            with open(quotes_file, 'w') as f:
                dump({}, f)
        return quotes_file

    def add_quote(self, data):
        uname, quote = self._get_uname(data.tokens)
        if not (uname and quote):
            self.conn.say('{}: Quotes must be of form "<username> quote"'
                    ' or "(username) quote".'.format(
                data.from_nick), data.to)
        else:
            d = self._load_quotes()
            err = d.get('error')
            if err:
                self.conn.say('{}: {}'.format(data.from_nick, err), data.to)
                return

            try:
                d[uname].append(quote)
            except KeyError:
                d[uname] = [quote]
            self._save_quotes(d)
            self.conn.say('Quote added.', data.to)

    def del_quote(self, data):
        uname, quote = self._get_uname(data.tokens)
        quotes = self._load_quotes()
        user_quotes = quotes.get(uname)
        if user_quotes and (quote in user_quotes):
            user_quotes.remove(quote)
            if not user_quotes:
                quotes.pop(uname)
            self._save_quotes(quotes)
            self.conn.say('Quote removed.', data.to)
        else:
            self.conn.say('{}: No such quote.'.format(data.from_nick), data.to)

    def nuke_quotes(self, data):
        uname = data.tokens[0]
        quotes = self._load_quotes()
        if uname in quotes:
            quotes.pop(uname)
            self._save_quotes(quotes)
            self.conn.say('All quotes from {} removed.'.format(uname), data.to)
        else:
            self.conn.say('No quotes from {}.'.format(uname), data.to)


    def _get_uname(self, tokens):
        tokens = tokens[:]
        if not tokens:
            return None, None
        elif (tokens[0] in {'<', '('}) and (len(tokens) > 1):
            uname = ''.join(tokens[:2])
            tokens = tokens[2:]
        else:
            uname = tokens.pop(0)

        if ((uname.startswith('<') and uname.endswith('>'))
            or (uname.startswith('(') and uname.endswith(')'))):
            uname = uname[1:-1].lstrip('@%+ ')
        else:
            uname = None
        return uname, ' '.join(tokens).strip()

    def get_quote(self, data):
        if data.tokens:
            uname = data.tokens[0].strip()
        else:
            uname = None

        quotes = self._load_quotes()
        err = quotes.get('error')
        if err:
            self.conn.say('{}: {}'.format(data.from_nick, err), data.to)
            return

        if not quotes:
            self.conn.say('{}: No quotes found. Add some!'.format(data.from_nick), data.to)
            return
        
        if not uname:
            uname = choice(list(quotes.keys()))
        user_quotes = quotes.get(uname)

        if user_quotes:
            quote = choice(user_quotes)
        else:
            quote = None
            
        if quote:
            self.conn.say('<{}> {}'.format(uname, quote), data.to)
        else:
            self.conn.say('{}: No quotes{}. Add some!'.format(data.from_nick,
                ' from {}'.format(uname) if uname else ''), data.to)
