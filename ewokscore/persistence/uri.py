from pathlib import Path
from urllib.parse import ParseResult, urlparse


def _normalize(uri):
    uri = uri.replace("\\", "/")
    if "::" in uri:
        # Non-standard notation:
        #   "/some/path::/another/path"
        # means
        #   "/some/path?path=/another/path"
        if "?" in uri:
            before, _, after = uri.partition("?")
            if "::" in before:
                if "path=" in uri:
                    raise ValueError("Cannot mix '::' with '?path='")
                uri = before.replace("::", "?path=")
                uri += "&" + after
        else:
            uri = uri.replace("::", "?path=")
    return uri


def parse_uri(
    uri: str,
    default_scheme: str = "file",
    default_port: int = None,
) -> ParseResult:
    """The general structure of a URI is:
    scheme://netloc/path;parameters?query#frag
    """
    result = urlparse(_normalize(uri))
    scheme, netloc, path, params, query, fragment = result
    if not scheme and default_scheme:
        scheme = default_scheme
    if default_port and not result.port:
        netloc = f"{result.hostname}:{default_port}"
    return type(result)(scheme, netloc, path, params, query, fragment)


def path_from_uri(parse_result: ParseResult) -> Path:
    return Path(parse_result.netloc) / parse_result.path


def parse_query(parse_result: ParseResult) -> dict:
    return dict(s.split("=") for s in parse_result.query.split("&") if s)
