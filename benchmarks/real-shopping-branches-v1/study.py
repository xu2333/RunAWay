"""Paired extraction on the archived shopping task, with an unchanged reader."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'real-shopping-scope-v1/study.py'
spec = importlib.util.spec_from_file_location('previous_shopping', path)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

GUIDANCE = (
    '若来源说明某项选择只有满足特定条件才多一项收益，在详细主张和随身正文里并列保留两条走法：'
    '满足什么条件时选什么、额外得到什么；条件不满足时原文支持哪种普通选择。'
    '若有多项独立取舍，逐项绑定到各自对象。资格未说明就保留为待确认；原文没给替代做法就标未知。'
    '分清当事人已选的做法和他人给出的条件建议。'
)
EXTRACTIONS = previous.EXTRACTIONS
DELIVERIES = previous.encoder.DELIVERIES
REQUIREMENTS = ('quality', 'television', 'bundle', 'membership', 'cashback',
                'tv_benefit', 'tablet_benefit')


def prepare(case):
    sources, requests = previous.prepare(case)
    baseline = requests['candidate']
    candidate = dict(baseline, system=baseline['system'] + '\n' + GUIDANCE)
    return sources, dict(original=baseline, candidate=candidate, none=requests['none'])


def delivery(arm, requests, cards):
    if arm not in EXTRACTIONS:
        raise ValueError('Expected a fixed card')
    return previous.delivery(arm, requests, cards)


def joint(criteria):
    return all(criteria[key] == 'met' for key in REQUIREMENTS)
