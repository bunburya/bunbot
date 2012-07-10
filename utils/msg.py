#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import load, dump
from os.path import expanduser, join
from time import asctime
from html.parser import HTMLParser

class CorruptedFileError(Exception): pass

user_cfg_path = '/home/bunburya/webspace/cgi-bin/pisg/pum/users.cfg'

class AliasParser(HTMLParser):

    def __init__(self, *nicks):
        self._nicks = set(nicks)
        self.nick_to_alias = {}
        self.alias_to_nick = {}
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if not tag == 'user':
            return
        attrs = dict(attrs)
        nick = attrs.get('nick')
        alias = attrs.get('alias')
        if not ((nick in self._nicks) and alias):
            return
        aliases = alias.split()
        self.nick_to_alias[nick] = aliases
        for a in aliases:
            self.alias_to_nick[a] = nick

class MessageHandler:
    
    # these default values are to work with bunbot
    def __init__(self, store_file):
        self.store_file = store_file

    def get_msgs(self):
        try:
            with open(self.store_file, 'r') as f:
                return load(f)
        except IOError:
            # file doesn't exist (yet)
            return {}
        except ValueError:
            # couldn't get a JSON object from the file
            raise CorruptedFileError(msg_file)

    def save_msgs(self, msgs):
        with open(self.store_file, 'w') as f:
            dump(msgs, f)
    
    def clear_msgs(self, name=None):
        if name is None:
            self.save_msgs({})
        else:
            msgs = self.get_msgs()
            if name in msgs:
                msgs.pop(name)
            self.save_msgs(msgs)

    def check_msgs(self, name):
        msgs = self.get_msgs()
        return msgs.get(name, [])
        
    def send_msg(self, sender, recip, msg):
        msgs = self.get_msgs()
        data = (msg, sender, asctime())
        if recip in msgs:
            msgs[recip].append(data)
        else:
            msgs[recip] = [data]
        self.save_msgs(msgs)
