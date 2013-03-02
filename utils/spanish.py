from urllib.request import urlopen, quote
from urllib.error import HTTPError
from unicodedata import normalize
import re

BASE_URL = 'http://www.spanishdict.com/translate/{}'
WILDCARD_URL = BASE_URL.format(r'\w+;?')
LINE_RE = re.compile(r'<h2 class="quick_def">.+</h2>')
WORD_RE = re.compile(r'<a href="{}">(\w+;?)</a> '.format(WILDCARD_URL))

def translate(word):
    """NB: Takes one word only; no whitespace."""
    url = BASE_URL.format(quote(word))
    try:
        html = urlopen(url).read().decode()
    except HTTPError:
        return ['Bad request']
    try:
        line= re.search(LINE_RE, html).group()
    except AttributeError:
        return []
    matches = re.findall(WORD_RE, line)
    print(matches)
    return matches
