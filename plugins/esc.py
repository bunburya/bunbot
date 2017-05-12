from os import mkdir
from os.path import exists, basename, join
from random import choice
from json import load, dump
from sys import version_info

if version_info.minor < 3:
    FileNotFoundError = IOError

class Plugin:

    HELPSTR = 'Syntax is \'!esc [year] [country]\' or \'!esc vote [country]\' to vote.'

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.name = basename(__file__).rstrip('.py')
        self.load_country_codes()
        self.hooks = [
                {'type': 'command', 'key': '!esc', 'func': self.esc}
                ]

    def vote(self, data, country=None):
        if country.lower() == 'netherlands':
            country = 'the netherlands'
        if not country:
            country = None
        vote_file = join(self.handler.plugin_dir, 'data',
                self.bot.ident.host, self.name, 'votes.json')
        songs_data = self.load_data('2017')
        countries = [i.lower() for i in songs_data.keys()]
        print(countries)
        try:
            with open(vote_file, 'r') as f:
                user_votes, country_votes = load(f)
        except FileNotFoundError:
            user_votes = {}
            country_votes = {c.lower(): [c, 0] for c in songs_data.keys()}
            print(country_votes)
        if country is not None:
            country = self.country_codes.get(country.upper(), country)
            if country.lower() not in countries:
                self.conn.say('{} are not in the ESC final.'.format(country), data.to)
                return
            else:
                prev_vote = user_votes.get(data.from_host, None)
                if prev_vote is not None and prev_vote.upper() == country.upper():
                    self.conn.say('{}, you already voted for that country.'.format(data.from_nick), data.to)
                    return
                user_votes[data.from_host] = country
                country_votes[country.lower()][1] += 1
                if prev_vote is not None:
                    country_votes[prev_vote.lower()][1] -= 1
                self.conn.say('{} voted for {} to win (this overrules any previous vote).'.format(data.from_nick, country), data.to)
                with open(vote_file, 'w') as f:
                    dump([user_votes, country_votes], f)
        else:
            rank = list(country_votes.keys())
            rank.sort(key=lambda k:country_votes[k][1], reverse=True)
            print(rank)
            top_3 = rank[:3]
            responses = []
            for k in top_3:
                name = country_votes[k][0]
                votes = country_votes[k][1]
                responses.append('{} ({} votes)'.format(name, votes))
            self.conn.say('Top 3 countries: {}'.format(', '.join(responses)), data.to)

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
            year = '2017'
            country = None
        else:
            tokens = data.trailing
            if tokens[0].lower() == 'vote':
                tokens.pop(0)
                self.vote(data, ' '.join(tokens))
                return
            if tokens[0].isdigit() and len(tokens[0]) == 4:
                year = tokens.pop(0)
            else:
                year = '2017'

            country = ' '.join(tokens)
            country = self.country_codes.get(country.upper(), country)
            
            if country.lower() == 'netherlands':
                country = 'the netherlands'

        if not country:
            if year == '2017':
                self.conn.say('This year\'s Eurovision Song Contest is on 13 May. '
                        'You can watch it at https://www.youtube.com/watch?v=ehH0_UXtQlY.',
                        data.to)
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
        
        if year == '2017':
            self.conn.say('{} are in this year\'s Eurovision with "{}" by {} ({}).'.format(c, s, a, v),
                data.to)
        else:
            self.conn.say('{} were in the finals of the {} Eurovision with "{}" by {} ({}).'.format(c, year, s, a, v),
                data.to)

