from urllib.request import urlopen
from urllib.parse import urlencode
from json import loads

BASE_URL = 'http://twitter.com/search.json?'

def query(terms):
    q_str = urlencode(terms)
    print(BASE_URL+q_str)
    json_data = urlopen(BASE_URL+q_str).read().decode()
    data = loads(json_data)
    return data

def get_tweets_from(user, n=1):
    args = {'q': 'from:{}'.format(user)}
    n = min(n, 1500)
    if n > 100:
        args['page'] = n // 100
        args['rpp'] = 100
    else:
        args['page'] = 1
        args['rpp'] = n
    return query(args)

def get_tweet_text(tweet):
    results = tweet['results']
    return [r['text'] for r in results]
