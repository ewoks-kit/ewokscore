from collections.abc import Mapping
from collections.abc import Sequence


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
