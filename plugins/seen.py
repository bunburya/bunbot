from os import mkdir
from os.path import exists, basename, join
from random import choice
from json import load, dump
from sys import version_info
from time import asctime

if version_info.minor < 3:
    FileNotFoundError = IOError

class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.name = basename(__file__).rstrip('.py')
        self.data_file = self.get_data_file()
        self.hooks = [
                {'type': 'other_part', 'key': None, 'func': self.add_seen},
                {'type': 'command', 'key': '!seen', 'func': self.get_seen},
                {'type': 'privmsg', 'key': None, 'func': self.add_seen},
                {'type': 'action', 'key': None, 'func': self.add_seen},
                {'type': 'other_join', 'key': None, 'func': self.add_seen}
                ]

    def _load_data(self):
        try:
            with open(self.data_file) as f:
                data = load(f)
        except FileNotFoundError:
            data = {}
        except ValueError:
            data = {'error': 'Error loading seen file. '
                        'Operation could not complete.'}
        return data
    
    def _save_data(self, data):
        with open(self.data_file, 'w') as f:
            dump(data, f)

    def get_data_file(self):
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
        data_file = join(name_dir, 'seen.json')
        if not exists(data_file):
            with open(data_file, 'w') as f:
                dump({}, f)
        return data_file

    def add_seen(self, data):
        seens = self._load_data()
        chan = data.to
        if chan not in seens:
            seens[chan] = {}
        seens[chan][data.from_nick] = asctime()
        self._save_data(seens)

    def get_seen(self, data):
        if not data.trailing:
            self.conn.say('Specify a username.', data.to)
            return
        seens = self._load_data()
        nick = data.trailing[0]
        try:
            time = seens[data.to][nick]
        except KeyError:
            time = None
        if not time:
            self.conn.say('Sorry, I haven\'t seen {} lately.'.format(nick), data.to)
        else:
            self.conn.say('{} was last seen at {}'.format(nick, time), data.to)
