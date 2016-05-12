#!/usr/bin/env python3

from sys import argv
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError

import re

BASE_URL = 'http://finance.yahoo.com/d/quotes.csv?'
FORMAT = ['s', 'l1', 'c']
INDEX = {'NASDAQ': '^IXIC', 'S&P': '^GSPC'}

class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [
                {'type': 'command', 'key': '!stock', 'func': self.stock}
                ]

    def stock(self, data):
        sym = data.trailing.pop(0)
        try:
            s, p, c = self.get_quote(sym)[0]
            self.conn.say('{}: {} ({})'.format(s, p, c), data.to)
        except:
            self.conn.say('Could not find quote for {}'.format(sym), data.to)

    def get_csv(self, *symbols):
        """Query the website and fetch the CSV containing the data."""
        symbols = [INDEX.get(s.upper(), s) for s in symbols]
        query = (('s', '+'.join(symbols)), ('f', ''.join(FORMAT)))
        args = urlencode(query)
        csv = urlopen(BASE_URL+args)
        csv = csv.readlines()
        return [line.decode().strip('\r\n') for line in csv]

    def parse_csv(self, csv):
        """Parse the CSV to extract the relevant data, and return it
        in an appropriate format."""
        data = []
        for line in csv:
            print(line)
            sym, price, change = [w.strip('"') for w in line.split(',')]
            change = change.split(' ')[-1]
            data.append([sym, price, change])
        return data

    def get_quote(self, *symbols):
        csv = self.get_csv(*symbols)
        data = self.parse_csv(csv)
        return data

