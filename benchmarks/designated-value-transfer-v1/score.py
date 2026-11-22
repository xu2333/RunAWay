"""Offline scores. No part of this file is loaded by either model condition."""
import argparse
import json
from pathlib import Path

NAMES = {'signed': '雾铃邮差', 'unsigned': '桥下回声'}
FIELDS = {'素材名', '起点秒', '终点秒', '倍速'}


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate field')
        result[key] = value
    return result


def score(reply, branch):
    try:
        obj = json.loads(reply, object_pairs_hook=unique)
    except (TypeError, ValueError):
        obj = None
    obj = obj if isinstance(obj, dict) else {}
    def equals(key, expected):
        value = obj.get(key)
        return type(value) in (float, int) and value == expected
    fields = set(obj) == FIELDS
    name = obj.get('素材名') == NAMES[branch]
    tail = equals('起点秒', 4) and equals('终点秒', 12)
    rate = equals('倍速', 1)
    return dict(exact_fields=fields, selected_name=name, retained_tail=tail, original_speed=rate,
                joint=fields and name and tail and rate)


def report(directory):
    if not (directory / 'closed.json').is_file():
        raise ValueError('Only score a closed run')
    cards = {}
    for method in ('original', 'current'):
        for gen in (1, 2):
            card = f'{method}-{gen}'
            rows = {}
            for branch in NAMES:
                for rep in (1, 2):
                    path = directory / f'{card}-{branch}-{rep}.json'
                    rows[f'{branch}-{rep}'] = score(json.loads(path.read_text())['answer'], branch) if path.is_file() else None
            cards[card] = {'reads': rows, 'all_four': all(row and row['joint'] for row in rows.values())}
    return cards


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('closed_directory', type=Path)
    print(json.dumps(report(parser.parse_args().closed_directory), indent=2))
