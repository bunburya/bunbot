from os.path import join

import xml.etree.ElementTree as ET

from urllib.request import urlopen
from urllib.parse import urlencode

class Plugin:

    SEARCH_URL = 'https://www.goodreads.com/search/index.html?'
    BOOK_URL = 'https://www.goodreads.com/book/show/'

    def __init__(self, bot, handler):
        self.bot = bot
        self.conn = bot.conn
        self.handler = handler
        self.conf_dir = join(self.handler.plugin_data_dir, 'goodreads')
        self.load_keys()
        self.hooks= [
                {'type': 'command', 'key': '!book', 'func': self.search_book_by_title}
                ]


    def search(self, title):
        query = urlencode({'q': title, 'key': self.key, 'search': 'title'})
        return urlopen(self.SEARCH_URL + query).read().decode()

    def parse_result(self, result):
        print(result)
        et = ET.fromstring(result)
        work = et.find('search').find('results').find('work')
        if not work:
            raise ValueError
        book = work.find('best_book')
        avg_rating = work.findtext('average_rating')
        title = book.findtext('title')
        author = book.find('author').findtext('name')
        year = book.findtext('original_publication_year')
        url = self.BOOK_URL + book.findtext('id')
        return title, author, year, avg_rating, url

    def load_keys(self):
        key_file = join(self.conf_dir, 'keys')
        with open(key_file) as f:
            key_data = f.readlines()
        self.key = key_data[0].split()[1].strip()
        self.secret = key_data[1].split()[1].strip()

    def search_book_by_title(self, data):
        query = ' '.join(data.trailing).strip()
        xml = self.search(query)
        try:
            title, author, year, avg_rating, url = self.parse_result(xml)
            if year:
                response = '"{}" by {} ({}, avg rating {}/5): {}'.format(
                        title, author, year, avg_rating, url
                    )
            else:
                response = '"{}" by {} (avg rating {}/5): {}'.format(
                        title, author, avg_rating, url
                    )
        except ValueError:
            response = 'No results found.'
        self.conn.say(response, data.to)


if __name__ == '__main__':
    from sys import argv
    print(parse_result(search(' '.join(argv[1:]))))
