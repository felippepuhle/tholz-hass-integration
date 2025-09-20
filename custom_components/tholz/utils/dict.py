from functools import reduce
import operator


def get_in(data: dict, path: list, default=None):
    try:
        return reduce(operator.getitem, path, data)
    except (KeyError, TypeError):
        return default


def set_in(data: dict, path: list, value):
    if not path:
        raise ValueError
    node = reduce(lambda d, k: d.setdefault(k, {}), path[:-1], data)
    node[path[-1]] = value
    return data
