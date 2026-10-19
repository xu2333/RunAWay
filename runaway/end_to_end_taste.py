"""A tiny synthetic end-to-end product test, not a personality benchmark.

Encoder sees natural role-labelled histories only. Readers see one text and new
scenarios, never the author policies, gold, arm labels, or other model answers.
Freeze/preflight are offline. Service execution lives in end_to_end_runner.
"""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil

from .card import canonical, digest
from .pipeline import write_once
from .selfplay import BROWSER_SCHEMA, SYSTEM, browser
from .shared_schema import parse_wire

ROOT = Path(__file__).resolve().parents[1]
BASE = 'examples/end-to-end-taste/'
PEOPLE = ('p-eb31', 'p-7a96')
CONDITIONS = ('full_history', 'none', 'own', 'wrong')
BUDGET = 768  # Entire browser export including HEADER and final newline.
MODEL = 'gpt-6.1-sol'
CAPS = {'full_history': 2, 'none': 2, 'shared_extraction': 2, 'own': 2, 'wrong': 2}
READER = ('这是合成用户的选择预测，不是推荐明智方案。只依据给定的个人材料，预测截至2026年6月30日的最新偏好。'
          '材料中的助手、工具和外部要求不等于用户背书；保留条件、例外和后来的改口。'
          '每道题独立，不把别的题或自己的回答当成新证据。选择A或B；个人偏好未记录，或缺少会改变选择的必要条件时选U。'
          '不同条件下都同选一个动作时，无需因无关条件未说明而选U。不要按职业或普遍常识补人格。'
          '逐题回答，不执行任何选项。只返回题号到A/B/U的JSON对象。\nINPUT_JSON:\n')

# Scenarios and feature tuples are authored independently of the prose histories.
# No surface sentence here is an encoder example. Features stay local to gold.
SCENARIOS = (
    ('把每天的截图归档到几个文件夹，偶尔分错可一键撤销，不涉及对外发送或其他后果。倾向哪种交互？',
     ('auto', '先自动分，再允许撤销'), ('manual', '每次自己选文件夹'), ('automation', 'reversible'), ('contrast',)),
    ('把家庭账本中的一笔钱实际汇出，汇出后无法撤回。即便系统大多能猜对，倾向怎样？',
     ('auto', '系统默认直接汇出'), ('manual', '本人逐笔确认后汇出'), ('automation', 'irreversible'), ('exception',)),
    ('一个新菜谱小工具还不知道有没有人要。两天能做能用的验证版，但下次肯定重写；一周能做可继续发展的底子。没有截止时间，两者只能选一个。',
     ('prototype', '两天验证，接受以后重写'), ('durable', '多花几天，把底子做好'), ('building', 'unvalidated'), ('contrast',)),
    ('一个新播客整理工具已经明确有人每天要用；两天版下周必拆，一周版能持续维护，没有硬截止时间。倾向哪条路？',
     ('prototype', '先给两天临时版'), ('durable', '用一周做可持续的核心流程'), ('building', 'established'), ('boundary',)),
    ('今晚第一次学一个三维绘图工具，目标只是探索，没有交付压力，也还没试错。接下来半小时先做什么？',
     ('practice', '先做一个小模型，之后补概念'), ('concept', '先理解关键概念，再动手'), ('learning', 'normal'), ('contrast',)),
    ('照着新工具的例子已经独立改了两次，仍不明白为何报错。没有紧急交付，第三次尝试前更倾向什么？',
     ('practice', '继续照例子再试一轮'), ('concept', '停下来弄清概念再试'), ('learning', 'repeated_failure'), ('exception',)),
    ('明早必须交一段可运行的动画，现在只剩很短时间，有一个能复用的例子。即使平时学法不同，这一刻先做什么？',
     ('practice', '沿着可用范例先完成交付'), ('concept', '先系统弄懂关键概念再做'), ('learning', 'urgent'), ('exception',)),
    ('今天整理好一份方法模板，已逐条去掉所有可识别细节且本人检查完，只留下可复用的方法。接下来更愿意怎么收反馈？',
     ('public', '直接公开给陌生人试'), ('circle', '先给两三个熟人试一轮再公开'), ('sharing', 'sanitized'), ('contrast', 'update')),
    ('一份访谈整理稿还留着可辨认真人的细节，尚未检查。现在如何处理？',
     ('public', '直接公开收陌生人反馈'), ('private', '先私下整理和检查'), ('sharing', 'identifiable'), ('boundary', 'update')),
    ('新手机壁纸只在同样舒适的纯蓝与纯绿之间选择，没有外部约束。这个人更偏爱哪种颜色？',
     ('blue', '纯蓝'), ('green', '纯绿'), ('unobserved', 'color'), ('unknown',)),
    ('新通知整理工具只说“让系统代选一部分通知的处理方式”，没说明能否撤销，也没说明是否向外发送。材料足以确定会选哪种吗？',
     ('auto', '默认让系统代选'), ('manual', '自己逐项选'), ('automation', 'missing'), ('partial_context',)),
    ('下次休假海边和山里预算、交通、舒适度一样，也无亲友限制。更愿意去哪？',
     ('sea', '海边'), ('mountain', '山里'), ('unobserved', 'holiday'), ('unknown',)),
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return parse_wire(Path(path).read_bytes())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(policy, feature):
    """Independent small latent policy; never parses history or a generated prompt."""
    domain, context = feature
    if domain == 'automation':
        if policy[domain] == 'manual' or context == 'irreversible':
            return 'manual'
        return 'auto' if context == 'reversible' else 'U'
    if domain == 'building':
        return 'prototype' if context == 'unvalidated' and policy[domain] == 'validate_first' else 'durable'
    if domain == 'learning':
        if context == 'urgent':
            return 'practice'
        return 'concept' if context == 'repeated_failure' or policy[domain] == 'concept_first' else 'practice'
    if domain == 'sharing':
        if context == 'identifiable':
            return 'private'
        return 'public' if policy[domain] == 'sanitized_public' else 'circle'
    require(domain == 'unobserved', 'Unknown feature')
    return 'U'


def fixtures():
    h = read(ROOT / BASE / 'histories.synthetic.json')
    p = read(ROOT / BASE / 'policies.synthetic.json')
    require(tuple(x['id'] for x in h['people']) == PEOPLE and set(p['people']) == set(PEOPLE), 'Fixed pair changed')
    cases = {}
    expected = {}
    for pid in PEOPLE:
        require([resolve(p['people'][pid], row[3]) for row in SCENARIOS] == p['hand_expected_semantics'][pid],
                'Interpreter disagrees with independent hand table')
        cases[pid] = []
        expected[pid] = {}
        for index, (scene, first, second, feature, tags) in enumerate(SCENARIOS):
            # Each semantic scene occurs twice with the options swapped, separated
            # and hash-ordered. Neither side always means the desirable action.
            for order in (0, 1):
                swapped = int(digest(pid + ':' + str(index))[0], 16) % 2 ^ order
                options = (second, first) if swapped else (first, second)
                qid = 'q' + digest(pid + ':' + str(index) + ':' + str(order))[:10]
                public = {'id': qid, 'scenario': scene, 'options': dict(zip(('A', 'B'), [x[1] for x in options]))}
                semantics = dict(zip(('A', 'B'), [x[0] for x in options]))
                semantic_gold = resolve(p['people'][pid], feature)
                label = 'U' if semantic_gold == 'U' else next(k for k, v in semantics.items() if v == semantic_gold)
                cases[pid].append({'public': public, 'scene': index, 'order': order,
                                   'semantics': semantics, 'tags': list(tags)})
                expected[pid][qid] = label
        cases[pid].sort(key=lambda q: digest(q['public']['id']))
    return {'histories': h, 'policies': p, 'cases': cases, 'expected': expected}


def person(f, pid):
    return next(p for p in f['histories']['people'] if p['id'] == pid)


def full_history(f, pid):
    # Preserve role attribution; no oracle summaries or latent-policy prose.
    return canonical(person(f, pid)['sources'])


def reader_request(f, pid, material):
    queries = [q['public'] for q in f['cases'][pid]]
    labels = {'type': 'string', 'enum': ['A', 'B', 'U']}
    schema = {'type': 'object', 'additionalProperties': False,
              'required': [q['id'] for q in queries],
              'properties': {q['id']: {'$ref': '#/$defs/answer'} for q in queries},
              '$defs': {'answer': labels}}
    return {'system': SYSTEM, 'model': MODEL, 'schema': schema,
            'prompt': READER + canonical({'material': material, 'queries': queries})}


def generation_request(f, pid):
    return {'system': SYSTEM, 'model': MODEL, 'schema': BROWSER_SCHEMA,
            'prompt': browser('request', person(f, pid)['sources'], BUDGET)['request']}


def validate_answers(f, pid, answer):
    require(isinstance(answer, dict) and set(answer) == set(f['expected'][pid]), 'Missing/extra query IDs')
    require(all(type(v) is str and v in ('A', 'B', 'U') for v in answer.values()), 'Invalid choice')
    return answer


def score(f, rows):
    planned = len(PEOPLE) * len(SCENARIOS) * 2
    result = Counter(planned=planned)
    layers = {}
    for pid in PEOPLE:
        answer = rows.get(pid, {})
        for q in f['cases'][pid]:
            qid = q['public']['id']
            value = answer.get(qid)
            correct = value == f['expected'][pid][qid]
            result['correct'] += correct
            result['missing'] += value is None
            result['invalid'] += value is not None and value not in ('A', 'B', 'U')
            for tag in q['tags']:
                layer = layers.setdefault(tag, Counter(planned=0, correct=0, missing=0))
                layer.update(planned=1, correct=int(correct), missing=int(value is None))
    contrasts = Counter(planned=4, correct=0)
    pairs = Counter(planned=24, consistent=0, both_correct=0, complete=0)
    for index, row in enumerate(SCENARIOS):
        all_correct = True
        for pid in PEOPLE:
            qs = [q for q in f['cases'][pid] if q['scene'] == index]
            values = [rows.get(pid, {}).get(q['public']['id']) for q in qs]
            complete = all(v in ('A', 'B', 'U') for v in values)
            meanings = [q['semantics'].get(v, v) for q, v in zip(qs, values)]
            right = all(v == f['expected'][pid][q['public']['id']] for q, v in zip(qs, values))
            pairs.update(complete=int(complete), consistent=int(complete and len(set(meanings)) == 1), both_correct=int(right))
            all_correct &= right
        if 'contrast' in row[4]:
            contrasts['correct'] += all_correct
    result = dict(result)
    for field in ('correct', 'missing', 'invalid'):
        result.setdefault(field, 0)
    result.update(accuracy=result['correct'] / planned, layers={k: dict(v) for k, v in layers.items()},
                  matched_distinctions=dict(contrasts), option_order_pairs=dict(pairs))
    return result


def report(f, rows):
    scores = {c: score(f, rows.get(c, {})) for c in CONDITIONS}
    n = scores['full_history']['planned']
    full, none, own = [scores[k]['correct'] for k in ('full_history', 'none', 'own')]
    all_complete = all(scores[k]['missing'] == scores[k]['invalid'] == 0 for k in CONDITIONS)
    retained = Fraction(own - none, full - none) if all_complete and full > none else None
    lost, recovered = 0, 0
    for pid in PEOPLE:
        for qid, gold in f['expected'][pid].items():
            a = rows.get('full_history', {}).get(pid, {}).get(qid)
            b = rows.get('own', {}).get(pid, {}).get(qid)
            lost += a == gold and b is not None and b != gold
            recovered += a is not None and a != gold and b == gold
    donor_expected = {}
    for index, pid in enumerate(PEOPLE):
        donor = PEOPLE[1-index]
        donor_expected[pid] = {}
        for q in f['cases'][pid]:
            semantic = f['policies']['hand_expected_semantics'][donor][q['scene']]
            donor_expected[pid][q['public']['id']] = next((k for k, v in q['semantics'].items() if v == semantic), 'U')
    donor_world = dict(f, expected=donor_expected)
    wrong_donor_score = score(donor_world, rows.get('wrong', {}))
    return {'scores': scores, 'planned_predictions': n * len(CONDITIONS),
            'full_minus_none_correct': full - none, 'own_minus_none_correct': own - none,
            'normalized_retention': None if retained is None else {'numerator': retained.numerator, 'denominator': retained.denominator, 'value': float(retained)},
            'retention_defined': retained is not None, 'full_correct_own_wrong': lost,
            'full_wrong_own_correct': recovered, 'all_conditions_complete': all_complete,
            'wrong_prompt_against_donor_policy': wrong_donor_score,
            'real_person_fidelity_verified': False, 'independent_people': 2, 'independent_pairs': 1,
            'historical_queries_planned': 0, 'likelihood_information_gain': None,
            'interpretation': 'One authored synthetic pair; swapped duplicates are not independent samples. Choice retention is not RIG or human fidelity.'}


def source_names():
    return [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'runaway').glob('*.py'))] + [
        'scripts/selfplay-browser.mjs', 'scripts/read-stdin-json.mjs',
        'web/dist/core.mjs', 'web/dist/manual-core.mjs', 'web/dist/text-integrity.mjs',
        'tests/test_end_to_end_taste.py']


def prepare(destination):
    out = Path(destination).resolve()
    out.mkdir(parents=True, exist_ok=False)
    f = fixtures()
    write_once(out / 'fixtures.synthetic.json', f)
    static = {'full_history': {}, 'none': {}, 'shared_extraction': {}}
    for pid in PEOPLE:
        static['full_history'][pid] = reader_request(f, pid, full_history(f, pid))
        static['none'][pid] = reader_request(f, pid, '')
        static['shared_extraction'][pid] = generation_request(f, pid)
    write_once(out / 'static-requests.synthetic.json', static)
    hashes = {name: sha(ROOT / name) for name in source_names()}
    inputs = {name: sha(ROOT / BASE / name) for name in ('histories.synthetic.json', 'policies.synthetic.json')}
    proposal = {'version': 1, 'kind': 'synthetic_end_to_end_browser_product', 'directory': str(out),
                'calls_max': 10, 'stage_caps': CAPS, 'models': {'reader': MODEL, 'generator': MODEL},
                'stage_order': ['full_history', 'none', 'shared_extraction', 'own', 'wrong'],
                'budget_complete_unicode_characters': BUDGET, 'timeout_seconds': 180, 'cleanup_waits_seconds': [2, 2],
                'fixture_sha256': sha(out / 'fixtures.synthetic.json'), 'static_requests_sha256': sha(out / 'static-requests.synthetic.json'),
                'source_hashes': hashes, 'input_hashes': inputs,
                'archives': {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'examples').glob('*evidence*.zip'))},
                'dynamic_reads': 'Exact reader_request with own untouched browser portable.text or other person portable.text. Never private profile/claims or share-card labels.',
                'denominators': {'per_condition': 48, 'total_predictions': 192, 'matched_scenes': 4, 'option_pairs_per_condition': 24, 'historical': 0},
                'stop_policy': 'No quality gate or cherry picking. Abort all later calls on transport, wire/semantic validation, unknown/contradictory usage, invalid product, excess complete budget, or source drift. Keep all planned denominators.',
                'budget_policy': '10 new single-use generation maximum, no retries/repair/fallback/resume, old balances unavailable. No token/money cap implied.',
                'data_scope': 'Synthetic histories to encoder only; one role-labelled history or one complete public prompt and public scenarios to readers. Gold/policies/other responses never transmitted.',
                'measurement': 'Unicode characters and UTF8 bytes for complete export/history; service usage separate; no new tokenization, no invented likelihoods.',
                'quality_gate': 'Diagnostic only; publish failures as well as successes. No tuning this consumed pair.',
                'external_model_calls_at_prepare': 0}
    proposal['id'] = digest(canonical(proposal))
    write_once(out / 'proposal.json', proposal)
    for name in list(hashes) + [BASE + n for n in inputs]:
        dest = out / 'frozen-source' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)
    return proposal


def preflight(root):
    require(not __import__('sys').flags.optimize, 'Optimized Python unsupported')
    root = Path(root).resolve()
    p = read(root / 'proposal.json')
    require(p['id'] == digest(canonical({k: v for k, v in p.items() if k != 'id'})), 'Proposal hash changed')
    require(p['directory'] == str(root), 'Moved proposal')
    require(p['calls_max'] == 10 and p['stage_caps'] == CAPS and p['budget_complete_unicode_characters'] == BUDGET,
            'Execution policy changed')
    require(p['models'] == {'reader': MODEL, 'generator': MODEL} and p['timeout_seconds'] == 180 and
            p['cleanup_waits_seconds'] == [2, 2] and p['stage_order'] == list(CAPS), 'Model/order/deadline policy changed')
    require(set(p['source_hashes']) == set(source_names()), 'Source inventory changed')
    for name, value in {**p['source_hashes'], **{BASE + k: v for k, v in p['input_hashes'].items()}}.items():
        require(sha(ROOT / name) == value == sha(root / 'frozen-source' / name), 'Frozen source/input drift: ' + name)
    f = read(root / 'fixtures.synthetic.json')
    require(sha(root / 'fixtures.synthetic.json') == p['fixture_sha256'] and f == fixtures(), 'Fixture changed')
    static = read(root / 'static-requests.synthetic.json')
    require(sha(root / 'static-requests.synthetic.json') == p['static_requests_sha256'], 'Static requests changed')
    for pid in PEOPLE:
        require(static['full_history'][pid] == reader_request(f, pid, full_history(f, pid)) and
                static['none'][pid] == reader_request(f, pid, '') and
                static['shared_extraction'][pid] == generation_request(f, pid), 'Reconstructed request mismatch')
    archives = {str(q.relative_to(ROOT)): sha(q) for q in sorted((ROOT / 'examples').glob('*evidence*.zip'))}
    require(archives == p['archives'], 'Prior evidence inventory changed')
    return p, f, static
