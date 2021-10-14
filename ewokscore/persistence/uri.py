import os
import re
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union
from urllib.parse import ParseResult, urlparse


def _normalize(uri: str) -> Tuple[str, str]:
    uri = uri.replace("\\", "/")
    # Non-standard notation:
    #   "/some/path::/another/path"
    # means
    #   "/some/path?path=/another/path"
    query = ""
    query_paths = re.findall("::([^;?#]*)", uri)
    if query_paths:
        for path in query_paths:
            uri = uri.replace("::" + path, "")
        query = join_query(("path", path) for path in query_paths)
    return uri, query


def parse_uri(
    uri: str,
    default_scheme: str = "file",
    default_port: int = None,
) -> ParseResult:
    """The general structure of a URI is:
    scheme://netloc/path;parameters?query#frag
    """
    uri, query_paths = _normalize(uri)
    result = urlparse(uri)
    scheme, netloc, path, params, query, fragment = result
    query = merge_query(query_paths, query)
    if not scheme and default_scheme:
        scheme = default_scheme
    if default_port and not result.port:
        netloc = f"{result.hostname}:{default_port}"
    return type(result)(scheme, netloc, path, params, query, fragment)


def path_from_uri(uri: Union[str, ParseResult], **parse_options) -> Path:
    if isinstance(uri, str):
        uri = parse_uri(uri, **parse_options)
    return Path(uri.netloc) / uri.path


def parse_query(uri: Union[str, ParseResult], **parse_options) -> dict:
    if isinstance(uri, str):
        uri = parse_uri(uri, **parse_options)
    return split_query(uri.query)


def split_query(query: str) -> dict:
    result = dict()
    for s in query.split("&"):
        if not s:
            continue
        name, _, value = s.partition("=")
        prev_value = result.get(name)
        if prev_value:
            value = join_string(prev_value, value, "/")
        result[name] = value
    return result


def join_query(query_items: Iterable[Tuple[str, str]]) -> str:
    return "&".join(f"{k}={v}" for k, v in query_items)


def join_string(a: str, b: str, sep: str):
    aslash = a.endswith(sep)
    bslash = b.startswith(sep)
    if aslash and bslash:
        return a[:-1] + b
    elif aslash or bslash:
        return a + b
    else:
        return a + sep + b


def merge_query(query1: str, query2: str) -> str:
    query1 = split_query(query1)
    query2 = split_query(query2)
    merged = list()
    names = list(query1) + list(query2)
    for name in names:
        value1 = query1.pop(name, None)
        value2 = query2.pop(name, None)
        if value1 and value2:
            merged.append((name, join_string(value1, value2, "/")))
        elif value1:
            merged.append((name, value1))
        elif value2:
            merged.append((name, value2))
    return join_query(merged)


def join_uri(
    root: Union[str, ParseResult], relative: Union[str, ParseResult], **parse_options
) -> ParseResult:
    if isinstance(root, str):
        root = parse_uri(root, **parse_options)
    if isinstance(relative, str):
        relative = parse_uri(relative, **parse_options)
    if root.params or relative.params:
        raise NotImplementedError()
    path = os.path.join(root.path, relative.path)
    query = merge_query(root.query, relative.query)
    return ParseResult(root.scheme, root.netloc, path, "", query, "")


def uri_as_string(uri: Union[str, ParseResult]) -> Optional[str]:
    if isinstance(uri, str):
        return uri
    elif isinstance(uri, ParseResult):
        return uri.geturl()
