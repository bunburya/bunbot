#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# http://www.python.org/dev/peps/pep-0008/

from sys import argv
from urllib.request import urlopen
from urllib.error import HTTPError

import re



class PEPNotFoundError(Exception): pass

base_url = 'http://www.python.org/dev/peps/pep-{0}'
title_pattern = r'\<title\>(.+)\</title\>'
pep_pattern = r'(PEP \d+) -- (.+)'

def get_url(pep):

    pep = str(pep).lstrip('0')
    if len(pep) > 4:
        raise PEPNotFoundError
    
    pep = '{0}{1}'.format('0'*(4-len(pep)), pep)
    return base_url.format(pep)

def get_title(url):
    try:
        html = urlopen(url).read().decode('utf-8')
    except HTTPError:
        raise PEPNotFoundError
#    print(html[:400])
#    print(title_pattern)
    page_title = re.search(title_pattern, html).group(1)
    pep_title = re.match(pep_pattern, page_title).group(1, 2)
    return ': '.join(pep_title)

def main(n=None):
    if n is None:
        pep = argv[1]
    else:
        pep = n
    response = []
    try:
        url = get_url(pep)
        response.append(get_title(url))
        response.append(url)
    except PEPNotFoundError:
        response.append('PEP {0} not found.'.format(pep))
    return(response)

if __name__ == '__main__':
    print(main())
