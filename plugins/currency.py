#!/usr/bin/env python3

from sys import argv
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError
from json import loads

import re


class Plugin:
    
    BASE_URL = 'http://api.fixer.io/'
    PAIR_PATTERN = re.compile(r'\A[a-zA-Z]{3}/[a-zA-Z]{3}\Z')
    SINGLE_PATTERN = re.compile(r'\A[a-zA-Z]{3}\Z')
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
        request = {'base': base, 'symbols': comp}
        get = urlencode(request).encode('utf-8')
        try:
            response = urlopen(url, post).read().decode('utf-8')
        except HTTPError:
            self.conn.say('Error communicating with currency API.', data.to)
            return None
        data = loads(response)
        return {
            'rate': data['rates'][comp],
            'date': data['date'],
            'base': data['base']
        }
    
    def convert(self, data):
        if 1 > len(data.trailing) > 2:
            self.syntax_help(data.to)
            return
        cur = data.trailing[0]
        
        if len(data.trailing) > 1:
            date = data.trailing[1]
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
        data = self.get_data(url, base, comp)
        if data is not None:
            self.conn.say('{base}/{comp} = {rate} on {date}.'.format(data),
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
