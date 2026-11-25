"""Verify the frozen inputs, answer digests, quoted grades and fixed denominators."""
import hashlib
import json
from pathlib import Path

from check import verify

HERE = Path(__file__).resolve().parent
LABELS = {
    'foldout': ('砂桥选拍、既往未知、无需先查', '两册各自进度、用纸和交付条件'),
    'thread': ('白棉线续穿仍是待办且不催办', '原线序、放行人、范围及进度'),
    'listening': ('签页及馆员核号，两项均保留且不加码', '剪辑版与母带、未知条件、展签和班次'),
}
ARMS = ('old', 'new')

def tally():
    path = HERE / 'protocol.json'
    previous = HERE.parent / 'claude-timing-waiver-repeat-v1' / 'protocol.json'
    verify(path, previous.read_bytes())
    slots = json.loads(path.read_bytes())['slots']
    rows = json.loads((HERE / 'observations.json').read_bytes())
    assert len(rows) == len(slots) == 12
    totals = {(case, arm): [0, 0, 0] for case in LABELS for arm in ARMS}
    closed = False
    for row, slot in zip(rows, slots):
        assert all(row[key] == value for key, value in slot.items())
        if closed:
            assert row['state'] == 'unattempted'
            continue
        if row['state'] == 'failure':
            closed = True
            continue
        assert row['state'] == 'answer'
        answer = row['answer']
        assert row['public_sha256'] == hashlib.sha256(answer.encode()).hexdigest()
        for key in ('focus', 'other_conditions'):
            mark = row[key]
            assert mark['grade'] in ('pass', 'fail', 'ambiguous', 'omitted')
            assert mark['quotes'] and all(q and q in answer for q in mark['quotes'])
        if slot['case'] == 'foldout':
            assert row['verification'] in ('none', 'optional', 'required', 'ambiguous')
            if row['verification'] in ('required', 'ambiguous'):
                assert row['focus']['grade'] != 'pass'
        counts = totals[slot['case'], slot['arm']]
        focus = row['focus']['grade'] == 'pass'
        other = row['other_conditions']['grade'] == 'pass'
        counts[0] += focus
        counts[1] += other
        counts[2] += focus and other and not row['additional_loss']
    return totals

if __name__ == '__main__':
    for (case, arm), counts in tally().items():
        print(case, arm, *[f'{n}/2' for n in counts])
