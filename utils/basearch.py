#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from html.parser import HTMLParser
from urllib.request import urlopen
from urllib.parse import urlencode, urljoin

BA_URL = 'http://beeradvocate.com'

class ResultParser(HTMLParser):
        
    def __init__(self, *args, **kwargs):
        self.parsing = False
        self.text = []
        self.links = []
        self.results = []
        self.total = 0
        HTMLParser.__init__(self, *args, **kwargs)
    
    def handle_starttag(self, tag, attrs):
        if tag == 'ul':
            self.parsing = True
        elif tag == 'li':
            if self.parsing:
                self.text = []
                self.links = []
        elif tag == 'a':
            if self.parsing:
                for attr, val in attrs:
                    if attr == 'href':
                        self.links.append(val)
    
    def handle_endtag(self, tag):
        if tag == 'ul':
            self.parsing = False
        elif tag == 'li':
            if self.parsing:
                self.results.append(Result(self.text, self.links))
    
    def handle_data(self, data):
        if self.parsing:
            if data.strip():
                self.text.append(data)
        elif data.startswith('Found: '):
            self.total = int(data.split(' ')[1])

class Result:
    
    def __init__(self, text, links):
        self.parse_text(text)
        self.parse_links(links)
    
    def parse_text(self, text):
        if len(text) > 3:
            print('RETIRED')
            print(text)
            self.retired = True
            text.pop(0)
            print(text)
        else:
            self.retired = False
        print(text)
        print(text[0])
        self.beer = text[0]
        self.brewer = text[1]
        self.location = text[2].lstrip('| ')
    
    def parse_links(self, links):
        self.beer_link = urljoin(BA_URL, links[0])
        self.brewer_link = urljoin(BA_URL, links[1])

def search(query, to_return=None):
    data = urlencode({'qt': 'beer', 'q': query})
    base_search_url = urljoin(BA_URL, 'search')
    search_url = '?'.join((base_search_url, data))
    html = urlopen(search_url).read().decode()
    html = html.replace('<php if($userId){ ?>', '').replace('<php } ?>', '')
    html = html.replace('&', 'and')
    #print(html)
    #return
    parser = ResultParser()
    parser.feed(html)
    if to_return is None:
        results = parser.results
    else:
        results = parser.results[:to_return]
    return results, parser.total, search_url

def test():
    url = 'http://beeradvocate.com/search?q=smithwicks&qt=beer'
    html = urlopen(url).read().decode()
    html = html.replace('<php if($userId){ ?>', '').replace('<php } ?>', '')
    parser = ResultParser()
    parser.feed(html)
    return parser.results
