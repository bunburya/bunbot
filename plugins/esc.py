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
        self.data = self.load_data()
        self.hooks = [
                {'type': 'command', 'key': '!esc', 'func': self.esc}
                ]

    def load_data(self):
        data_file = join(self.handler.plugin_dir, 'data',
                self.bot.ident.host, self.name, 'esc.csv')
        data = {}
        with open(data_file) as f:
            for line in f:
                d = line.strip().split(',')
                data[d[0].lower()] = d
        return data

    def esc(self, data):
        if data.trailing:
            country = ' '.join(data.trailing).strip().lower()
        else:
            country = None

        if not country:
            self.conn.say('Watch the Eurovision final at '
                    'http://www.eurovision.tv/page/webtv?program=102853',
                    data.to)
            return

        if country == 'ireland':
            self.conn.say('Ireland has won the Eurovision Song Contest more times '
                    'than any other country! http://en.wikipedia.org/wiki/'
                    'List_of_Eurovision_Song_Contest_winners', data.to)
            return

        d = self.data.get(country, None)
        if not d:
            self.conn.say('No song found for {}.  Either they didn\'t get through '
                    'to the final, or you can\'t spell!'.format(country), data.to)
            return

        c, a, s, v = d
        self.conn.say('{} are in this year\'s Eurovision final with "{}" by {} ({}).'.format(c, s, a, v),
                data.to)

