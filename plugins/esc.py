from os import mkdir
from os.path import exists, basename, join
from random import choice
from json import load, dump
from sys import version_info

if version_info.minor < 3:
    FileNotFoundError = IOError

class Plugin:

    HELPSTR = 'Syntax is \'!esc [year] [country]\'.'

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.name = basename(__file__).rstrip('.py')
        self.load_country_codes()
        self.hooks = [
                {'type': 'command', 'key': '!esc', 'func': self.esc}
                ]

    def load_country_codes(self):
        codes_file = join(self.handler.plugin_dir, 'data',
                self.bot.ident.host, self.name, 'country_iso_codes.json')
        with open(codes_file) as f:
            self.country_codes = load(f)

    def load_data(self, year):
        data_file = join(self.handler.plugin_dir, 'data',
                self.bot.ident.host, self.name, 'esc_{}.csv'.format(year))
        data = {}
        with open(data_file) as f:
            for line in f:
                d = line.strip().split(',')
                data[d[0].lower()] = d
        return data

    def esc(self, data):

        if not data.trailing:
            year = '2015'
            country = None
        else:
            tokens = data.trailing
            if tokens[0].isdigit() and len(tokens[0]) == 4:
                year = tokens.pop(0)
            else:
                year = '2015'

            country = ' '.join(tokens)
            country = self.country_codes.get(country.upper(), country)


        if not country:
            if year == '2015':
                self.conn.say('This year\'s Eurovision Song Contest is on 23 May. '
                              'You can watch it at http://www.eurovision.tv/page/webtv?program=132913.',
                        data.to)
                self.conn.say('Type \'!esc [country name]\' to see that country\'s entry.', data.to)
            else:
                self.conn.say(self.HELPSTR, data.to)
            return

        try:
            songs_data = self.load_data(year)
        except FileNotFoundError:
            self.conn.say('Sorry, no data found for that year.', data.to)
            return

        d = songs_data.get(country.lower(), None)
        if not d:
            self.conn.say('No song found for {}.  Either I don\'t have an entry for that country and year, '
                    'or the spelling is incorrect.'.format(country), data.to)
            return

        c, a, s, v = d
        
        if year == '2015':
            self.conn.say('{} are in this year\'s Eurovision with "{}" by {} ({}).'.format(c, s, a, v),
                data.to)
        else:
            self.conn.say('{} were in the finals of the {} Eurovision with "{}" by {} ({}).'.format(c, year, s, a, v),
                data.to)

