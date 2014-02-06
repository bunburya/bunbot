#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import load, dump
from os.path import expanduser, join, basename, exists
from os import mkdir
from time import asctime

Error = object()

class Plugin:
    
    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.name = basename(__file__).rstrip('.py')
        self.msg_file = self.get_msg_file()
        self.hooks = [
                {'type': 'command', 'key': '!msg', 'func': self.msg,
                    'help': [
                        '!msg <user> <message> : Send `message` to `user`.',
                        '!msg : View (and delete) your messages.',
                        ]
                    },
                {'type': 'other_join', 'key': None, 'func': self.check_for_msgs}
                ]

    def _load_msgs(self):
        try:
            with open(self.msg_file) as f:
                msgs = load(f)
        except FileNotFoundError:
            msgs = {}
        except ValueError:
            msgs = {Error: 'Error loading messages. Operation could not complete.'}
        return msgs
    
    def _save_msgs(self, msgs):
        with open(self.msg_file, 'w') as f:
            dump(msgs, f)
    
    def get_msg_file(self):
        plugin_dir = self.handler.plugin_dir
        serv = self.bot.ident.host
        name = self.name

        data_dir = join(plugin_dir, 'data')
        if not exists(data_dir):
            mkdir(data_dir)
        serv_dir = join(data_dir, serv)
        if not exists(serv_dir):
            mkdir(serv_dir)
        name_dir = join(serv_dir, name)
        if not exists(name_dir):
            mkdir(name_dir)
        msg_file = join(name_dir, 'msg.json')
        if not exists(msg_file):
            with open(msg_file, 'w') as f:
                dump({}, f)
        return msg_file

    def msg(self, data):
        if not data.tokens:
            self.view_msgs(data)
        else:
            self.send_msg(data)

    def check_for_msgs(self, data):
        msgs = self._load_msgs()
        if data.from_nick.lower() in msgs:
            self.conn.say('You have messages. Type "!msg" to view them.',
                    data.from_nick)

    def view_msgs(self, data):
        msgs = self._load_msgs()
        user_msgs = msgs.pop(data.from_nick.lower(), None)
        if user_msgs is None:
            self.conn.say('No messages.', data.from_nick)
        else:
            for sender, msg, time in user_msgs:
                self.conn.say('<{}> {} (sent at {})'.format(sender, msg, time),
                        data.from_nick)
        self._save_msgs(msgs)

    def send_msg(self, data):
        _from = data.from_nick
        to = data.tokens[0].lower()
        msg = ' '.join(data.tokens[1:])
        time = asctime()
        msgs = self._load_msgs()
        if to in msgs:
            msgs[to].append((_from, msg, time))
        else:
            msgs[to] = [(_from, msg, time)]
        self._save_msgs(msgs)
        self.conn.say('Message sent.', data.to)
    
    def clear_msgs(self, data):
        msgs = self._load_msgs()
        msgs.pop(data.from_nick)
        self._save_msgs(msgs)

