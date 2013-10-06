from urllib.request import urlopen
from urllib.error import URLError
from html.parser import HTMLParseError
import re

from bs4 import BeautifulSoup

class Plugin:
    
    # This regex is borrowed from Django, with some groups added in
    url_regex = re.compile(
        r'((?:http|ftp)s?://' # http:// or https://
        r'((?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))|' # domain...
        r'localhost|' # localhost...
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|' # ...or ipv4
        r'(\[?[A-F0-9]*:[A-F0-9:]+\]?))' # ...or ipv6
        r'(?::(\d+))?' # optional port
        r'([/+]\S+)?)', re.IGNORECASE)

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.ignore_titles = set() # TODO: save to/read from file
        self.hooks = [
                {'type': 'privmsg_re', 'key': self.url_regex, 'func': self.parse_url},
                {'type': 'privmsg_re', 'key': self.url_regex, 'func': self.title}
                ]


    def parse_url(self, data):
        """To be called before the other functions.
        Parses the url and stores info about it to be accessed
        by other functions."""
        match = data.regex_match
        url, domain, ipv4, ipv6, port, filepath = match.groups()
        self.url_data = {}
        self.url_data['url'] = url
        self.url_data['domain'] = domain
        self.url_data['ipv4'] = ipv4
        self.url_data['ipv6'] = ipv6
        self.url_data['port'] = port
        self.url_data['filepath'] = filepath

    def title(self, data):
        try:
            html = urlopen(self.url_data['url']).readall()
        except (URLError):
            return
        try:
            soup = BeautifulSoup(html)
        except HTMLParseError:
            return
        try:
            title = soup.find('head').find('title').text
        except AttributeError:
            title = None
        if title is not None:
            self.conn.say('Title: {} (at {})'.format(title,
                self.url_data['domain']), data.to)
