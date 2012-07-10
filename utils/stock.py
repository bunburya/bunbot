#!/usr/bin/env python3

from sys import argv
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError

import re

BASE_URL = 'http://finance.yahoo.com/d/quotes.csv?'
FORMAT = ['s', 'l1', 'c']
INDEX = {'NASDAQ': '^IXIC', 'S&P': '^GSPC'}

def main(*symbols):
    print(get_quote(*symbols))
        

def get_csv(*symbols):
    """Query the website and fetch the CSV containing the data."""
    symbols = [INDEX.get(s.upper(), s) for s in symbols]
    query = (('s', '+'.join(symbols)), ('f', ''.join(FORMAT)))
    args = urlencode(query)
    csv = urlopen(BASE_URL+args)
    csv = csv.readlines()
    return [line.decode().strip('\r\n') for line in csv]

def parse_csv(csv):
    """Parse the CSV to extract the relevant data, and return it
    in an appropriate format."""
    data = []
    for line in csv:
        sym, price, change = [w.strip('"') for w in line.split(',')]
        change = change.split(' ')[-1]
        data.append([sym, price, change])
    return data

def get_quote(*symbols):
    csv = get_csv(*symbols)
    data = parse_csv(csv)
    return data
            

if __name__ == '__main__':
    main(*argv[1:])
