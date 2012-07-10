#!/usr/bin/env python3

from html.parser import HTMLParser
from urllib.request import urlopen

class SummaryParser(HTMLParser):
    
    def __init__(self, n):
        self.problem = n
        self.read_data = False
        self.data = []
        HTMLParser.__init__(self)
    
    def handle_starttag(self, tag, attrs):
        if (tag == 'a') and (dict(attrs)['href'] == 'problem={}'.format(self.problem)):
            self.read_data = True
    
    def handle_endtag(self, tag):
        if tag == 'a':
            self.read_data = False
    
    def handle_data(self, data):
        if self.read_data:
            self.data.append(data)
    
    @property
    def summary(self):
        return ''.join(self.data)

def summary(n):
    """Return a summary of and link to the nth Project Euler problem."""
    try:
        n = int(n)
    except ValueError:
        return (None, None)
    page = (n//50)+1
    page_url = 'http://projecteuler.net/problems;page={}'.format(page)
    direct_url = 'http://projecteuler.net/problem={}'.format(n)
    html = urlopen(page_url).read().decode('latin-1')
    
    parser = SummaryParser(n)
    parser.feed(html)
    summary = parser.summary

    return (summary, direct_url) if summary else (None, None)
