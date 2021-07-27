import json
from har_analysis import Request, RequestSequenceSolver

PATH = 'data/privacy.com.har'


def read_har(filepath) -> dict:
    with open(filepath) as f:
        return json.load(f)


def contains_cookie(request, value):
    for cookie in request['cookies']:
        if cookie['value'] == value:
            return True
    return False


def contains_header(request, value):
    for header in request['headers']:
        if header['value'] == value:
            return True
    return False


def contains_url(request, url):
    return request['url'] == url


cookie_value = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI1YjRhNDEwYjM4MGVhZjU5YmIxZDliMjYiLCJpYXQiOjE2MjY4NDQwMTksImV4cCI6MTYyNjg2MjAxOX0.dJe_WC4sX3OMO0qV6ted2p--D8j8hcf9EgG70mz20L8'
v = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI1YjRhNDEwYjM4MGVhZjU5YmIxZDliMjYiLCJpYXQiOjE2MjY4NDQwMTksImV4cCI6MTYyNjg2MjAxOX0.dJe_WC4sX3OMO0qV6ted2p--D8j8hcf9EgG70mz20L8'
URL = 'https://privacy.com/api/v1/organization/plans'

har = read_har(PATH)
# entries = har['log']['entries']


# A = [(i, e) for i, e in enumerate(entries)
#      if contains_header(e['request'], cookie_value)]

target_index = 65
rss = RequestSequenceSolver(har)
rss.build_dependency_graph(target_index)

requests = rss.requests
for request_id in requests:
    r = requests[request_id]
    print(r.url)
    for symbol in r.symbols:
        # , symbol.hard_coded_value,
        print(('/'.join(symbol.path)), symbol.name, symbol.hard_coded_value)
        #   [e.name for e in symbol.potential_dependencies])

    all_values = rss.all_request_symbols
# for k in rss.all_request_symbols:
    print()


# A = [e for e in entries if e['response']['content']['mimeType'].lower().find(
#     'json') != -1 and 'text' in e['response']['content'] and e['response']['content']['text']]

# request = entries[142]['request']
# rss.requests['1'] = Request(request['method'], request['url'])

# print(rss.extract_request_symbols(request, '1'))

# for value in rss.all_request_symbols:
#     symbols = rss.all_request_symbols[value]
#     for s in symbols:
#         print(s.path, s.name)
