#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urljoin

BA_URL = 'http://beeradvocate.com'

class ResultParser(HTMLParser):
        
    def __init__(self, *args, **kwargs):
        self.parsing = False
        self.parsed = False
        self.text = []
        self.links = []
        self.results = []
        self.total = 0
        HTMLParser.__init__(self, *args, **kwargs)
    
    def handle_starttag(self, tag, attrs):
        if tag == 'ul':
            if not self.parsed:
                # We only parse the first ul tag, because that's
                # where the beers are
                self.parsing = True
        elif tag == 'li':
            if self.parsing:
                self.results.append({})
        elif tag == 'a':
            if self.parsing and ('link' not in self.results[-1]):
                for attr, val in attrs:
                    if attr == 'href':
                        link = urljoin(BA_URL, val)
                        self.results[-1]['link'] = link
    
    def handle_endtag(self, tag):
        if tag == 'ul':
            self.parsing = False
            self.parsed = True
    
    def handle_data(self, data):
        # Each entry should have 3 text entries:
        # 1. Beer name;
        # 2. Brewery;
        # 3. Location
        if self.parsing:
            data = data.strip()
            if data:
                beer = self.results[-1]
                if not 'name' in beer:
                    beer['name'] = data
                elif not 'brewer' in beer:
                    beer['brewer'] = data
                elif not 'location' in beer:
                    beer['location'] = data.lstrip('| ')
        elif data.startswith('Found: '):
            self.total = int(data.split(' ')[1])

def search(query, to_return=None):
    data = urlencode({'qt': 'beer', 'q': query, 'retired': 'N'})
    base_search_url = urljoin(BA_URL, 'search/')
    search_url = '?'.join((base_search_url, data))
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'
    req = Request(
            search_url,
            data=None,
            headers={'User-Agent': user_agent}
            )
    html = urlopen(req).read().decode()
    html = html.replace('<php if($userId){ ?>', '').replace('<php } ?>', '')
    html = html.replace('&', 'and')
    parser = ResultParser()
    parser.feed(html)
    if to_return is None:
        results = parser.results
    else:
        results = parser.results[:to_return]
    return results, parser.total, search_url

class Plugin:

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.hooks = [
                {'type': 'command', 'key': '!beer', 'func': self.beer}
                ]

    def beer(self, data):
        query = ' '.join(data.trailing)
        if not query.strip():
            self.conn.say('Syntax is !beer <beer name>', data.to)
            return
        result = search(query, 1)[0][0]
        print(result)
        try:
            response = '{} (by {}, {}): {}'.format(
                    result['name'],
                    result['brewer'],
                    result['location'],
                    result['link']
                    )
        except KeyError:
            self.conn.say('No beer found by that name!', data.to)
            return
        self.conn.say(response, data.to)
