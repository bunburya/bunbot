#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import loads
from os.path import expanduser, join, basename, exists

from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError

BASE_URL = 'http://www.bunburya.eu/songlist'
ADD_URL = '/'.join((BASE_URL, 'add'))
RANDOM_URL = '/'.join((BASE_URL, 'random'))

Error = object()

class Plugin:
    
    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.name = basename(__file__).rstrip('.py')
        self.hooks = [
                {'type': 'command', 'key': '!add_song', 'func': self.add_song},
                {'type': 'command', 'key': '!random_song', 'func': self.random_song}
                ]

    def add_song(self, data):
        print(data.trailing)
        if len(data.trailing) < 3:
            self.conn.say('Syntax for adding a song is "!add_song [url] [song artist and title]"', data.to)
            return
        request = {
                'from':         'bunbot',
                'url':          data.trailing[0],
                'title':        ' '.join(data.trailing[1:]),
                'other':        'Submitted via bunbot.',
                'submitter':    data.from_nick
                }
        post = urlencode(request).encode('utf-8')
        try:
            response = urlopen(ADD_URL, post).read().decode('utf-8')
        except HTTPError:
            self.conn.say('Error communicating with songlist!', data.to)
            return
        status = int(response)
        if status >= 0:
            self.conn.say('Song added!', data.to)
        else:
            self.conn.say('Something went wrong; song not added.', data.to)

    def random_song(self, data):
        request = {'from': 'bunbot'}
        if data.tokens:
            submitter = ' '.join(data.trailing)
            request['submitter'] = submitter
        else:
            submitter = None
        post = urlencode(request).encode('utf-8')
        try:
            response = urlopen(RANDOM_URL, post).read().decode('utf-8')
        except HTTPError:
            self.conn.say('Error communicating with songlist!', data.to)
            return
        jdata = loads(response)
        if not jdata:
            if submitter is None:
                self.conn.say('No songs found. Add some!', data.to)
            else:
                self.conn.say('No songs submitted by {}.'.format(submitter), data.to)
        else:
            title = jdata['title']
            url = jdata['url']
            submitter = jdata['submitter']
            self.conn.say('"{}" - {} {}'.format(
                title, url, '- submitted by {}'.format(submitter) if submitter else ''),
                data.to)
        


