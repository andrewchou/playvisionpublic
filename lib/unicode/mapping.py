# -*- coding: utf-8 -*-

_mapping = {
    'á': 'a',
    'é': 'e',
    'î': 'i',
    'ñ': 'n',
    'ö': 'o',
    'ü': 'u',
}


def best_effort_unicode_to_ascii(u):
    a = ''.join([_mapping.get(c, c) for c in u])
    assert a.encode('ascii', errors='ignore').decode() == a, (u, a)
    return a
