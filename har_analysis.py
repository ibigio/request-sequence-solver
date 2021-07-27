from collections import defaultdict
import json
from dataclasses import dataclass
from enum import Enum
from typing import Tuple


# Path = list[str]
# JsonPath = 'list[str | int]'

Path = any
JsonPath = any


class SymbolValueType(Enum):
    NAME_VALUE = 1
    JSON = 2


@dataclass
class ResponseSymbol:
    request_id: str
    path: Path
    type: SymbolValueType
    json_path: JsonPath
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass
class ValuedResponseSymbol:
    value: str
    symbol: ResponseSymbol


@dataclass
class RequestSymbol:
    request_id: str
    path: Path
    type: SymbolValueType
    json_path: JsonPath
    name: str
    hard_coded_value: str
    potential_dependencies: 'list'
    # potential_dependencies: list[ResponseSymbol] = []

    def add_dependency(self, dep: ResponseSymbol) -> None:
        self.potential_dependencies.append(dep)


@dataclass
class ValuedRequestSymbol:
    value: str
    symbol: RequestSymbol


@dataclass
class Request:
    id: str
    idx: int
    method: str
    url: str
    symbols: 'list[RequestSymbol]'
    # symbols: set[RequestSymbol] = []

    def add_symbol(self, symbol: RequestSymbol) -> None:
        self.symbols.append(symbol)


@dataclass
class JsonLeaf:
    value: str
    path: JsonPath


# @dataclass
# class RequestField:
#     name: str

#     def extract_all(request: dict) -> 'list[RequestSymbol]':
#         pass

#     def

def flatten_json(j: dict) -> 'list[JsonLeaf]':
    flat: list[JsonLeaf] = []

    def flatten_helper(cur_j, path: JsonPath = []):
        if type(cur_j) is dict:
            for key in cur_j:
                flatten_helper(cur_j[key], path + [key])
        elif type(cur_j) is list:
            for i, c in enumerate(cur_j):
                flatten_helper(c, path + [i])
        else:
            flat.append(JsonLeaf(cur_j, path.copy()))
    flatten_helper(j, [])
    return flat


class RequestSequenceSolver:
    '''
    Request sequence solver
    TODO: fill in rest of doc
    '''

    def __init__(self, har: dict) -> None:
        self.__har = har.copy()
        self.__entries: dict = self.__har['log']['entries']
        self.requests: dict[str, Request] = dict()
        self.all_request_symbols: dict[str,
                                       list[RequestSymbol]] = defaultdict(list)

        self.__significant_request_paths = [["headers"], [
            "cookies"], ["queryString"], ["postData", "params"]]

    def get_request(self, request_id: str) -> Request:
        if request_id not in self.requests:
            raise Exception(
                f"No request found with id {request_id}.")
        return self.requests[request_id]

    def __extract_request_symbols_at_path__(self, request: dict, request_id: str, path: Path) -> 'list[ValuedRequestSymbol]':
        # TODO: maybe clean up this path resolution?
        valued_symbols: list[ValuedRequestSymbol] = []
        location = request
        for p in path:
            if p not in location:
                return valued_symbols
                # TODO: is this ever an error? could defintely be a mistake that is never caught...
                raise Exception(
                    f"Could not follow path {path} (failed at {p}). Possible keys were {location.keys()}.")
            location = location[p]

        for pair in location:
            name = pair['name']
            value = pair['value']
            symbol = RequestSymbol(
                request_id, path, SymbolValueType.NAME_VALUE, None, name, value, [])
            # skip cookies in the header - these are handeled explicitly
            if path == ["headers"] and name.lower() == "cookie":
                continue
            valued_symbols.append(ValuedRequestSymbol(value, symbol))

        return valued_symbols

    def __extract_request_symbols_post_data__(self, request: dict, request_id: str) -> 'list[ValuedRequestSymbol]':
        valued_symbols: list[ValuedRequestSymbol] = []
        if 'postData' not in request or 'json' not in request['postData']['mimeType']:
            return []
        path = ['postData', 'text']
        location = request['postData']['text']

        text = json.loads(location)
        for leaf in flatten_json(text):
            symbol = RequestSymbol(
                request_id, path, SymbolValueType.JSON, leaf.path, leaf.path[-1], leaf.value, [])
            valued_symbols.append(ValuedRequestSymbol(leaf.value, symbol))

        return valued_symbols

    def extract_request_symbols(self, request: dict, request_id: str) -> 'list[ValuedRequestSymbol]':
        '''
        Extract request symbols.
        TODO: fill in rest of doc
        '''
        # TODO: do I need to special case 'queryParams' to do URL decoding?
        valued_symbols: list[ValuedRequestSymbol] = []
        for path in self.__significant_request_paths:
            valued_symbols += self.__extract_request_symbols_at_path__(
                request, request_id, path)
        valued_symbols += self.__extract_request_symbols_post_data__(
            request, request_id)
        return valued_symbols

    def __add_response_symbol_as_depedency__(self, symbol: ResponseSymbol, value: str) -> int:
        if value not in self.all_request_symbols:
            return 0

        request_symbols_with_value = self.all_request_symbols[value]
        assert(len(request_symbols_with_value) > 0)

        for request_symbol in request_symbols_with_value:
            request_symbol.add_dependency(symbol)
        return len(request_symbols_with_value)

    def __extract_response_symbols_for_cookies__(self, response: dict, request_id: str) -> 'list[ValuedResponseSymbol]':
        valued_symbols: list[ValuedResponseSymbol] = []
        location = response['cookies']

        for pair in location:
            name = pair['name']
            value = pair['value']
            symbol = ResponseSymbol(
                request_id, ['cookies'], SymbolValueType.NAME_VALUE, None, name)
            valued_symbols.append(ValuedResponseSymbol(value, symbol))

        return valued_symbols

    def __extract_response_symbols_for_content__(self, response: dict, request_id: str) -> 'list[ValuedResponseSymbol]':
        # TODO: implement
        # iterate through entire response content text json and create symbol
        # for every leaf value
        valued_symbols: list[ValuedResponseSymbol] = []
        if 'json' not in response['content']['mimeType']:
            return []
        path = ['content', 'text']
        location = response['content']['text']

        text = json.loads(location)
        for leaf in flatten_json(text):
            symbol = ResponseSymbol(
                request_id, path, SymbolValueType.JSON, leaf.path, leaf.path[-1])
            valued_symbols.append(ValuedResponseSymbol(leaf.value, symbol))

        return valued_symbols

    def extract_response_symbols(self, response: dict, request_id: str) -> 'list[ValuedResponseSymbol]':
        '''
        Extract response symbols.
        TODO: fill in rest of doc
        '''

        cookies_valued_symbols = self.__extract_response_symbols_for_cookies__(
            response, request_id)
        content_valued_symbols = self.__extract_response_symbols_for_content__(
            response, request_id)

        return cookies_valued_symbols + content_valued_symbols

    def __process_entry__(self, entry: dict, request_id: str, request_idx: int, force_add: bool = False) -> None:
        num_dependent_symbols = 0
        request = entry['request']
        response = entry['response']

        # == Step I : Extract Response Symbols == #
        valued_response_symbols = self.extract_response_symbols(
            response, request_id)
        for vs in valued_response_symbols:
            num_dependent_symbols += self.__add_response_symbol_as_depedency__(
                vs.symbol, vs.value)

        if num_dependent_symbols == 0 and not force_add:
            return

        # == Step II : Extract Request Symbols == #
        valued_request_symbols = self.extract_request_symbols(
            request, request_id)
        for vs in valued_request_symbols:
            self.all_request_symbols[vs.value].append(vs.symbol)

        # == Step III: Add Request == #
        self.requests[request_id] = Request(request_id, request_idx, request['method'], request['url'], [
            vs.symbol for vs in valued_request_symbols])

        return num_dependent_symbols, [vs.symbol for vs in valued_request_symbols]

    def build_dependency_graph(self, target_request_index: int):

        for i in reversed(range(target_request_index + 1)):
            entry: dict = self.__entries[i]
            request_id = str(i)
            self.__process_entry__(
                entry, request_id, i, i == target_request_index)


# def get_request_symbol_value(symbol: RequestSymbol, responses: 'dict[str, dict]') -> any:
#     if symbol.type


# def execute_requests(requests: 'dict[str, Request]'):
#     ordered_requests = sorted(requests.values(), key=lambda r: r.request_idx)
#     responses = dict()
#     for request in ordered_requests:
#         for symbol in request.symbols:
#             symbol.
#             pass
