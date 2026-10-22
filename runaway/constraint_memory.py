"""Experimental source-constraint v2, offline only; not a default extractor.

Annotations must come from sources, never evaluation questions or target labels.
Quote/role checks cannot establish that an annotation faithfully translates prose.
This module checks a bounded finite representation and its internal consequences.
It neither parses arbitrary natural language nor certifies behavioral fidelity.
"""
from itertools import product
from math import prod

from .card import canonical, digest, string
from .profile import exact, validate_sources

VERSION = 'source_constraints_v2'
U = 'U'
HEADER = '偏好仅供暂定参考；当前指令优先，不代表身份事实或行动授权。\n'
GUIDE = ('仅在上述领域与取值内判断；缺条件时遍历所有可能取值及仍相容的准则，'
         '全部同选才选；异选、超出范围或唯一做法未提供时未知。\n')


def _list(value, low, high, name):
    if type(value) is not list or not low <= len(value) <= high:
        raise ValueError(name + ': invalid list size')
    return value


def validate(contract, sources):
    """Exact citations, finite types and chronology, NOT semantic source support."""
    validate_sources(sources)
    exact(contract, ('version', 'name', 'tagline', 'scope', 'features', 'actions',
                     'family', 'observations'), 'constraint contract')
    if contract['version'] != VERSION:
        raise ValueError('Explicit source_constraints_v2 version required')
    string(contract['name'], 'name', 20)
    string(contract['tagline'], 'tagline', 60)
    index = {s['id']: (i, s) for i, s in enumerate(sources['sources'])}

    def anchor(a, user=False):
        exact(a, ('source_id', 'quote'), 'anchor')
        row = index.get(a['source_id'])
        quote = string(a['quote'], 'quote', 4000)
        if row is None or quote not in row[1]['text']:
            raise ValueError('Anchor is not an exact source quote')
        if user and row[1]['role'] != 'user':
            raise ValueError('Commitments and choices require user evidence')
        return row

    def evidence(anchors, user=False):
        return [anchor(a, user) for a in _list(anchors, 1, 16, 'evidence')]

    scope = contract['scope']
    exact(scope, ('id', 'text', 'evidence'), 'scope')
    string(scope['id'], 'scope id', 60)
    string(scope['text'], 'scope text', 300)
    evidence(scope['evidence'], True)
    if not any(scope['text'] in a['quote'] for a in scope['evidence']):
        raise ValueError('Scope text needs verbatim definition evidence')
    features = {}
    for feature in _list(contract['features'], 1, 6, 'features'):
        exact(feature, ('id', 'values', 'evidence'), 'feature')
        key = string(feature['id'], 'feature id', 40)
        if key in features:
            raise ValueError('Duplicate feature')
        values = _list(feature['values'], 2, 8, 'feature values')
        if len(set(values)) != len(values):
            raise ValueError('Duplicate feature value')
        anchors = evidence(feature['evidence'], True)
        for value in values:
            string(value, 'feature value', 120)
            if not any(value in row[1]['text'] and value in a['quote']
                       for row, a in zip(anchors, feature['evidence'])):
                raise ValueError('Feature value needs verbatim definition evidence')
        features[key] = values
    if prod(len(values) for values in features.values()) > 256:
        raise ValueError('Finite state space exceeds256')
    actions = _list(contract['actions'], 2, 2, 'actions')
    if len(set(actions)) != 2 or U in actions:
        raise ValueError('Two distinct actions, excluding reserved U, required')
    for action in actions:
        string(action, 'action', 100)
        if not any(action in row['text'] for row in sources['sources'] if row['role'] == 'user'):
            raise ValueError('Action vocabulary must occur in user sources')

    family = contract['family']
    if family is not None:
        exact(family, ('commitment', 'rules'), 'family')
        evidence(family['commitment'], True)
        ids = set()
        for rule in _list(family['rules'], 1, 16, 'rules'):
            exact(rule, ('id', 'definition', 'any_of', 'evidence'), 'rule')
            key = string(rule['id'], 'rule id', 40)
            if key in ids:
                raise ValueError('Duplicate rule')
            ids.add(key)
            definition = string(rule['definition'], 'definition', 400)
            evidence(rule['evidence'], True)
            if not any(definition in a['quote'] for a in rule['evidence']):
                raise ValueError('Rule meaning must accompany its ID as source text')
            # Bounded DNF: any conjunction true selects actions[1], else actions[0].
            # Empty DNF is false; an empty conjunction is true.
            for clause in _list(rule['any_of'], 0, 32, 'rule clauses'):
                if type(clause) is not dict:
                    raise ValueError('A rule clause must contain feature values')
                for key, value in clause.items():
                    if key not in features or value not in features[key]:
                        raise ValueError('Undefined rule feature or value')
    seen = set()
    for observation in _list(contract['observations'], 1, 64, 'observations'):
        exact(observation, ('id', 'values', 'choice', 'decision', 'contexts',
                            'supersedes'), 'observation')
        key = string(observation['id'], 'observation id', 60)
        if key in seen:
            raise ValueError('Duplicate observation')
        seen.add(key)
        if type(observation['values']) is not dict or set(observation['values']) != set(features):
            raise ValueError('Observation needs complete defined feature values')
        if any(v not in features[k] for k, v in observation['values'].items()):
            raise ValueError('Observation contains undefined feature value')
        if observation['choice'] not in actions:
            raise ValueError('Observation action undefined')
        position, row = anchor(observation['decision'], True)
        if observation['choice'] not in observation['decision']['quote']:
            raise ValueError('Decision quote must contain chosen action')
        evidence(observation['contexts'])
        old_ids = _list(observation['supersedes'], 0, 16, 'supersedes')
        if len(set(old_ids)) != len(old_ids):
            raise ValueError('Duplicate supersedes')
        for sid in old_ids:
            old = index.get(sid)
            if old is None or old[1]['role'] != 'user' or old[0] >= position:
                raise ValueError('Superseded choice must be an earlier user source')
    active = {o['decision']['source_id'] for o in contract['observations']}
    if any(sid in active for o in contract['observations'] for sid in o['supersedes']):
        raise ValueError('Superseded choice cannot remain an active observation')
    return features


def _action(rule, state, actions):
    enabled = any(all(state[k] == v for k, v in clause.items())
                  for clause in rule['any_of'])
    return actions[int(enabled)]


def compile_contract(contract, sources):
    """Retain every compatible policy. Never select an author's hidden policy."""
    features = validate(contract, sources)
    observed = {}
    for o in contract['observations']:
        state = tuple(o['values'][k] for k in features)
        observed.setdefault(state, set()).add(o['choice'])
    consistent = all(len(v) == 1 for v in observed.values())
    family = contract['family']
    checks = [] if family is None else [
        {'rule_id': r['id'], 'contradicts_observation_ids': [o['id'] for o in contract['observations']
            if _action(r, o['values'], contract['actions']) != o['choice']]}
        for r in family['rules']]
    compatible = {row['rule_id'] for row in checks if not row['contradicts_observation_ids']}
    rules = [] if family is None else [r for r in family['rules'] if r['id'] in compatible]
    consistent = consistent and (family is None or bool(rules))
    return {'version': VERSION, 'contract_sha256': digest(canonical(contract)),
            'source_sha256': digest(canonical(sources)),
            'compatible_rule_ids': [r['id'] for r in rules],
            'rule_filter_trace': checks,
            'internally_consistent': consistent,
            'mode': 'closed_source_family' if family is not None else 'observations_only',
            'status': 'candidate_unvalidated', 'quote_role_structure_checked': True,
            'semantic_translation_verified': False, 'behavioral_fidelity_verified': False}


def decide(contract, sources, *, scope, values, offered):
    """Offline finite-contract consequence, not an LLM answer or semantic score.

    The caller must map question prose to scope/features. That mapping is unverified.
    Unknown feature keys/values and scopes are not silently ignored.
    """
    compiled = compile_contract(contract, sources)
    def outcome(choice, reason):
        return {'choice': choice, 'reason': reason, 'status': 'candidate_unvalidated',
                'semantic_translation_verified': False, 'behavioral_fidelity_verified': False}
    unknown = lambda reason: outcome(U, reason)
    if not compiled['internally_consistent']:
        return unknown('inconsistent_evidence')
    if scope != contract['scope']['id']:
        return unknown('outside_scope')
    features = {f['id']: f['values'] for f in contract['features']}
    if type(values) is not dict or any(k not in features or v not in features[k]
                                       for k, v in values.items()):
        return unknown('undefined_feature_value')
    completions = [dict(zip(features, row)) for row in product(
        *[[values[k]] if k in values else vs for k, vs in features.items()])]
    family = contract['family']
    choices = set()
    if family is not None:
        rules = [r for r in family['rules'] if r['id'] in compiled['compatible_rule_ids']]
        choices = {_action(r, state, contract['actions']) for r in rules for state in completions}
    else:
        for state in completions:
            found = {o['choice'] for o in contract['observations'] if o['values'] == state}
            if not found:
                return unknown('unobserved_without_family_commitment')
            choices.update(found)
    if len(choices) != 1:
        return unknown('compatible_alternatives_disagree')
    choice = next(iter(choices))
    if choice not in offered:
        return unknown('known_action_not_offered')
    return outcome(choice, 'annotated_constraint_entailment' if family else 'observed_coverage')


def render(contract, sources, budget=512):
    """Render meanings, not external candidate numbers. Never truncate to fit.

    This is a candidate representation of annotations, not automatic NL extraction.
    All definitions and inference instructions count toward the whole-card budget.
    """
    if type(budget) is not int or not 300 <= budget <= 16000:
        raise ValueError('budget must be300–16000 whole Unicode characters')
    compiled = compile_contract(contract, sources)
    if not compiled['internally_consistent']:
        raise ValueError('Inconsistent evidence: no portable inference card')
    text = HEADER + contract['name'] + '｜' + contract['tagline'] + '\n'
    text += contract['scope']['text'].rstrip('。') + '。'
    text += '各项仅限：' + '；'.join('／'.join(f['values']) for f in contract['features']) + '。\n'
    family = contract['family']
    if family is not None:
        text += '来源保证采用同一稳定准则；与有效决定相容的可能准则仅剩：'
        text += '或'.join('「' + r['definition'] + '」' for r in family['rules']
                        if r['id'] in compiled['compatible_rule_ids'])
        text += '均为满足准则选' + contract['actions'][1] + '，否则选' + contract['actions'][0] + '。\n'
    else:
        text += '来源未保证有限准则集合；只保留以下实际观察：'
        text += '；'.join('、'.join(o['values'][f['id']] for f in contract['features'])
                         + '→' + o['choice'] for o in contract['observations']) + '。\n'
        text += '没有观察的完整组合未知，不从样本推出准则。\n'
    text += GUIDE
    if len(text) > budget:
        raise ValueError('Complete card exceeds budget: ' + str(len(text)) + '>' + str(budget))
    return text
