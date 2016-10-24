from urllib.request import urlopen, Request, build_opener, HTTPRedirectHandler
from urllib.parse import quote
from urllib.error import URLError, HTTPError
try:
    from html.parser import HTMLParseError
except ImportError:
    class HTMLParseError(BaseException): pass
from http.client import HTTPException
import re

from bs4 import BeautifulSoup

ascii_chars = ''.join((chr(i) for i in range(128)))

def quote_url(url):
    return quote(url, safe=ascii_chars)

class RedirectHandler(HTTPRedirectHandler):
    
    def _handle_redirect(self, req, fp, code, msg, headers):
        url_unescaped = headers.get('Location')
        new_url = quote_url(url_unescaped)
        headers.replace_header('Location', new_url)
        result = HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        return result
                                                    
    def http_error_301(self, *args):
        return self._handle_redirect(*args)
                                                                    
    def http_error_302(self, *args):
        return self._handle_redirect(*args)
                                                                                    
    def http_error_303(self, *args):
        return self._handle_redirect(*args)
                                                                                                    
    def http_error_307(self, *args):
        return self._handle_redirect(*args)

class Plugin:

    req_header = {'User-Agent': 'bunbot IRC bot'}
    
    # This regex is borrowed from Django, with some groups added in
    url_regex = re.compile(
        r'((?:http|ftp)s?://' # http:// or https://
        r'((?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))|' # domain...
        r'localhost|' # localhost...
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|' # ...or ipv4
        r'(\[?[A-F0-9]*:[A-F0-9:]+\]?))' # ...or ipv6
        r'(?::(\d+))?' # optional port
        r'([/+]\S+)?)', re.IGNORECASE)

    ignore_title = {
        "reddit.com",
        "redd.it",
        "youtube.com",
        "youtu.be",
        "twitter.com",
        "amazon.com",
        "soundcloud.com",
        "spotify.com"
    }

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.ignore_titles = set() # TODO: save to/read from file
        self.hooks = [
                {'type': 'privmsg_re', 'key': self.url_regex, 'func': self.parse_url}
                # ceding this job to gonzobot (TODO: find a way to blacklist it instead)
                #{'type': 'privmsg_re', 'key': self.url_regex, 'func': self.title}
                ]

    def fetch_url(self, url):
        req = Request(url, headers=self.req_header)
        opener = build_opener(RedirectHandler())
        return opener.open(req)

    def parse_url(self, data):
        """To be called before the other functions.
        Parses the url and stores info about it to be accessed
        by other functions."""
        match = data.regex_match
        url, domain, ipv4, ipv6, port, filepath = match.groups()
        url = quote_url(url)    # To handle unicode chars in the URL
        self.url_data = {}
        self.url_data['url'] = url
        self.url_data['domain'] = domain
        self.url_data['ipv4'] = ipv4
        self.url_data['ipv6'] = ipv6
        self.url_data['port'] = port
        self.url_data['filepath'] = filepath

    def title(self, data):
        url = self.url_data['url']
        if url.endswith('.mp4') or url.endswith('.webm'):
            # The html parser chokes on some video files, so this is a
            # (rather inadequate) way of addressing the issue.
            return
        for domain in self.ignore_title:
            if self.url_data['domain'].endswith(domain):
                return
        try:
            html = self.fetch_url(self.url_data['url']).readall()
        except (URLError, HTTPException, HTTPError) as e:
            print('Error encountered in fetching URL: {}'.format(type(e)))
            return
        try:
            soup = BeautifulSoup(html)
        except HTMLParseError:
            print('Error parsing HTML.')
            return
        try:
            title = soup.find('head').find('title').text.replace('\n', '').replace('\r', '').replace('\t', ' ').strip()
        except AttributeError:
            title = None
        if title is not None:
            self.conn.say('Title: {} (at {})'.format(title,
                self.url_data['domain']), data.to)
