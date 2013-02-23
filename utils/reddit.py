#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import loads
from urllib.request import urlopen
from urllib.error import HTTPError
from http.client import HTTPResponse
from random import choice

USER_URL = 'http://www.reddit.com/user/{}/about.json'
SUB_URL = 'http://www.reddit.com/r/{}.json'

def user(name):
    url = USER_URL.format(name)
    try:
        response = urlopen(url).readall().decode('utf-8')
    except HTTPError:
        return (None, None)
    data = loads(response)['data']
    return (data['link_karma'], data['comment_karma'])

def rand_item(sub='all'):
    result = []
    url = SUB_URL.format(sub)
    try:
        data = loads(urlopen(url).read().decode('utf-8'))
        print(data)
    except (ValueError, HTTPError):
        return None, None
    if data.get('error', None) is not None:
        return None, None
    posts = data['data']['children']
    post_data = choice(posts)['data']
    title = post_data['title']
    if sub == 'all':
        sub = post_data['subreddit']
        title = '[{}] {}'.format(sub, title)
    link = post_data['url']
    return title, link
                


def main():
    from sys import argv
    if len(argv) < 2:
        print('Syntax: reddit <command> <args>')
        exit(1)
    command = argv[1]
    if len(argv) > 2:
        args = argv[2:]
    else:
        args = None
    if command == 'user':
        if args is None:
            print('Syntax: user <user1> <user2> ... <userN>')
            exit(1)
        for u in args:
            link, comment = user(u)
            if link is None:
                response = 'User not found.'
            else:
                response = '{} link karma, {} comment karma.'.format(link, comment)
            print('{}: {}'.format(u, response))
    elif command == 'random':
        if args is None:
            args = ['all']
        for s in args:
            title, link = rand_item(s)
            if title is None:
                response = 'Subreddit not found.'
            else:
                response = '{} ({})'.format(title, link)
            print('{}: {}'.format(s, response))
    else:
        print('Invalid command: {}. Valid commands are: user, random.'.format(command))
            
if __name__ == '__main__':
	main()

