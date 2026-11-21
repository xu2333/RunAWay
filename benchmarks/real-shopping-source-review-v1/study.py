"""Review one fixed portable draft against its source, then reuse the prior reader."""
import importlib.util
import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'real-shopping-branches-v1/study.py'
spec = importlib.util.spec_from_file_location('shopping_branches', path)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

REVIEW_GUIDANCE = (
    '把随附的随身正文当作待复核的草稿。先从来源逐一辨认涉及独立取舍的对象，'
    '逐个对照草稿：条件成立与不成立时各有什么依据、做法和后果？'
    '保留原文足以影响选择的具体信息及其归属。把有依据的遗漏补入，纠正无依据的内容，'
    '保住草稿中已有依据的其他取舍。草稿本身不能作为证据。'
)
REVIEWS = ('candidate1', 'candidate2')
DELIVERIES = previous.DELIVERIES
REQUIREMENTS = previous.REQUIREMENTS
delivery = previous.delivery
joint = previous.joint


def review_request(extractor, parent):
    if not isinstance(parent, str) or not parent.strip() or len(parent) > 768:
        raise ValueError('Expected a nonempty whole card within budget')
    draft = json.dumps(parent, ensure_ascii=False)
    return dict(extractor, system=extractor['system'] + '\n' + REVIEW_GUIDANCE,
                prompt='DRAFT_JSON:\n' + draft + '\n\n' + extractor['prompt'])
