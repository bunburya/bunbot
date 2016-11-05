#!/usr/bin/env python3

from sys import argv
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from json import loads

import re

class CurrencyError(Exception): pass

class Plugin:
    
    BASE_URL = 'http://api.fixer.io/'
    PAIR_PATTERN = re.compile(r'\A[a-zA-Z]{3}/[a-zA-Z]{3}\Z')
    SINGLE_PATTERN = re.compile(r'\A[a-zA-Z]{3}\Z')
    DATE_PATTERN = re.compile(r'\A\d{4}-\d{2}-\d{2}\Z')
    DEFAULT_BASE = 'EUR'

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.symbols = self.get_symbols()
        self.hooks = [
                {'type': 'command', 'key': '!conv', 'func': self.convert}
                ]
    
    def get_symbols(self):
        url = self.BASE_URL + 'latest'
        try:
            response = urlopen(url).read().decode('utf-8')
        except HTTPError:
            return None
        data = loads(response)
        symbols = []
        symbols.append(data['base'])
        symbols.extend(data['rates'].keys())
        return symbols

    def get_data(self, url, base, comp):
        bad_cur = []
        if self.symbols:
            for s in (base, comp):
                if s not in self.symbols:
                    bad_cur.append(s)
        if bad_cur:
            raise CurrencyError(*bad_cur)
        request = {'base': base, 'symbols': comp}
        get = urlencode(request)
        response = urlopen(url + '?' +  get).read().decode('utf-8')
        data = loads(response)
        rate = data['rates'].get(comp)
        if rate is None:
            # this is somewhat redundant given the check at the start of
            # the function but is helpful in case self.symbols is inaccurate
            # for whatever reason.
            raise CurrencyError(comp)
        return {
                'rate': data['rates'][comp],
                'comp': comp,
                'date': data['date'],
                'base': data['base']
        }

    
    def convert(self, data):
        print(data.trailing)
        if not (1 <= len(data.trailing) <= 2):
            print('invalid number of arguments')
            self.syntax_help(data.to)
            return
        cur = data.trailing[0].upper()
        
        if len(data.trailing) > 1:
            date = data.trailing[1]
            if not re.match(self.DATE_PATTERN, date):
                self.conn.say('Date syntax is YYYY-MM-DD.', data.to)
                return
        else:
            date = 'latest'
        url = self.BASE_URL + date 
        if re.match(self.PAIR_PATTERN, cur):
            base, comp = cur.split('/')
        elif re.match(self.SINGLE_PATTERN, cur):
            base = self.DEFAULT_BASE
            comp = cur
        else:
            self.syntax_help(data.to)
            return

        try:
            cur_data = self.get_data(url, base, comp)
        except CurrencyError as e:
            self.conn.say('Bad currency code: {}'.format(', '.join(e.args)), data.to)
            return
        except HTTPError:
            self.conn.say('Error communicating with currency API.', data.to)
            return
        else:
            self.conn.say('{base}/{comp} = {rate} on {date}.'.format(**cur_data),
                data.to)
            
    def syntax_help(self, recip):
        self.conn.say('Syntax is !conv <currency>[/<currency>] [yyyy-mm-dd]',
            recip)
        if self.symbols is None:
            self.symbols = self.get_symbols()
        if self.symbols is not None:
            symbol_str = ', '.join(self.symbols)
            self.conn.say('Supported currencies are: {}'.format(symbol_str),
                recip)
    
    def stock(self, data):
        if not data.trailing:
            self.conn.say('Syntax is !stock <ticker>', data.to)
            return
        sym = data.trailing.pop(0)
        try:
            s, p, c = self.get_quote(sym)[0]
            self.conn.say('{}: {} ({})'.format(s, p, c), data.to)
        except:
            self.conn.say('Could not find quote for {}'.format(sym), data.to)
