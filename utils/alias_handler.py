#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from html.parser import HTMLParser

user_cfg_path = '/home/bunburya/webspace/cgi-bin/pisg/pum/users.cfg'

class AliasParser(HTMLParser):

    def __init__(self):
        self.nick_to_alias = {}
        self.alias_to_nick = {}
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if not tag == 'user':
            return
        attrs = dict(attrs)
        nick = attrs.get('nick')
        alias = attrs.get('alias')
        if not (nick and alias):
            return
        aliases = alias.split()
        self.nick_to_alias[nick] = aliases
        for a in aliases:
            self.alias_to_nick[a.rstrip(',')] = nick

def _get_maps():
    with open(user_cfg_path, 'r') as f:
        data = f.read()
    parser = AliasParser()
    parser.feed(data)
    return parser.nick_to_alias, parser.alias_to_nick

def get_true_nick(alias):
    _, alias_to_nick = _get_maps()
    return alias_to_nick.get(alias, alias)
    
def get_aliases(nick):
    nick_to_alias, _ = _get_maps()
    return nick_to_alias.get(nick, [])
