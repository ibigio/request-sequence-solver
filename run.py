#!/usr/bin/env python3

import json
import sys
from collections import defaultdict

path = sys.argv[1]


def read_har(filepath) -> dict:
    with open(filepath) as f:
        return json.load(f)


def unique_cookies(entries):
    seen = defaultdict(int)
    values = defaultdict(str)
    changes = defaultdict(int)
    cookies = []
    print(len(entries))
    for e in entries:
        for c in e['request']['cookies']:
            name = c['name']
            value = c['value']

            if name not in seen:
                cookies.append(name)
            seen[name] += 1

            if values[name] != value:
                changes[name] += 1
                values[name] = value

    return [(c, seen[c], changes[c]) for c in cookies]


har = read_har(path)
entries = har['log']['entries']
entries = [e for e in entries if e['request']['cookies']]
cookies = unique_cookies(entries)

for c, s, chs in sorted(cookies, key=lambda x: x[1]):
    if chs == 1:
        print(s, c)
