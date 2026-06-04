from collections.abc import Mapping
from collections.abc import Sequence
from difflib import get_close_matches
from typing import Iterable
from typing import Optional


def dict_merge(
    destination, source, overwrite=False, _nodes=None, contatenate_sequences=False
):
    """Merge the source into the destination"""
    if _nodes is None:
        _nodes = tuple()
    for key, value in source.items():
        if key in destination:
            _nodes += (str(key),)
            if isinstance(destination[key], Mapping) and isinstance(value, Mapping):
                dict_merge(
                    destination[key],
                    value,
                    overwrite=overwrite,
                    _nodes=_nodes,
                    contatenate_sequences=contatenate_sequences,
                )
            elif value == destination[key]:
                continue
            elif overwrite:
                destination[key] = value
            elif (
                contatenate_sequences
                and isinstance(destination[key], Sequence)
                and isinstance(value, Sequence)
            ):
                destination[key] += value
            else:
                raise ValueError("Conflict at " + ".".join(_nodes))
        else:
            destination[key] = value


def suggest_close_match(word: str, possibilities: Iterable[str]) -> Optional[str]:
    """Return the closest match from possibilities, or None if none found."""
    close_match = get_close_matches(word, list(possibilities), n=1, cutoff=0.5)
    return close_match[0] if close_match else None


def build_close_match_report(words: Iterable[str], possibilities: Iterable[str]) -> str:
    """Return an error report with close match suggestions for each word."""
    possibilities = list(possibilities)
    error_report = ""
    for word in words:
        suggestion = suggest_close_match(word, possibilities)
        if suggestion:
            error_report += f"\n  @ You provided '{suggestion}'. Did you mean '{word}'?"
    return error_report
