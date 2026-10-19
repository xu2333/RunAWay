"""Optional concise current-policy encoding. D-0028 evidence covers consumed synthetic policies only."""
import itertools
import json
import re
from . import temporal as t
from .card import canonical, digest, string
from .text_integrity import require_intact

HEADER = '仅所列当前偏好，无历史；当前要求优先，不授权行动。硬>例外>常规；同层冲突或条件未明则未知。未列/空=无证据；首组=常规，多项=等强冲突；&须全满足，!为否定。未建模>0可能不全。\n'
J = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def policy(artifact):
    rows = []
    for domain, rule in t.effective(artifact).items():
        row = {'domain': domain, 'regular': list(dict.fromkeys(e['action'] for e in rule['regular']))}
        for kind in ('exception', 'constraint'):
            row[kind] = [{'when': [[l['predicate'], l['equals']] for l in e['when_all']], 'action': e['action']} for e in rule[kind]]
        rows.append(row)
    return {'scope': artifact['extraction']['scope'], 'unmodeled': len(artifact['extraction']['unmodeled']), 'domains': rows}


def validate(p):
    if not isinstance(p, dict) or set(p) != {'scope', 'unmodeled', 'domains'}: raise ValueError('Policy fields changed')
    string(p['scope'], 'scope', 300)
    if type(p['unmodeled']) is not int or not 0 <= p['unmodeled'] <= 1000: raise ValueError('Invalid unmodeled count')
    if not isinstance(p['domains'], list) or len(p['domains']) > 300: raise ValueError('Invalid domains')
    seen = set()
    for d in p['domains']:
        if not isinstance(d, dict) or set(d) != {'domain', 'regular', 'exception', 'constraint'}: raise ValueError('Invalid domain fields')
        string(d['domain'], 'domain', 200)
        if d['domain'] in seen: raise ValueError('Duplicate domain')
        seen.add(d['domain'])
        if not isinstance(d['regular'], list) or len(d['regular']) > 300: raise ValueError('Invalid defaults')
        for action in d['regular']: string(action, 'action', 200)
        if len(set(d['regular'])) != len(d['regular']): raise ValueError('Duplicate default')
        for tier in ('exception', 'constraint'):
            if not isinstance(d[tier], list) or len(d[tier]) > 300: raise ValueError('Invalid rules')
            for e in d[tier]:
                if not isinstance(e, dict) or set(e) != {'when', 'action'}: raise ValueError('Invalid rule fields')
                string(e['action'], 'action', 200)
                if not isinstance(e['when'], list) or not 1 <= len(e['when']) <= 12: raise ValueError('Invalid conjunction')
                names = set()
                for literal in e['when']:
                    if not isinstance(literal, list) or len(literal) != 2 or type(literal[1]) is not bool: raise ValueError('Invalid literal')
                    string(literal[0], 'predicate', 100)
                    if literal[0] in names: raise ValueError('Duplicate predicate')
                    names.add(literal[0])
    return p


def encode(artifact, budget_chars=768, count=None, budget_tokens=None, domains=None):
    if type(budget_chars) is not int or budget_chars < 1: raise ValueError('Positive whole character budget required')
    if budget_tokens is not None and (count is None or type(budget_tokens) is not int or budget_tokens < 1): raise ValueError('Actual tokenizer required')
    p = validate(policy(artifact))
    order = [d['domain'] for d in p['domains']]
    if domains is not None:
        if not isinstance(domains, list) or any(not isinstance(d, str) or d not in order for d in domains) or len(set(domains)) != len(domains):
            raise ValueError('Select unique observed domains explicitly')
        by_domain = {d['domain']: d for d in p['domains']}
        p['domains'] = [by_domain[d] for d in domains]
    text = HEADER + '范围:' + J(p['scope']) + '\n未建模:' + str(p['unmodeled']) + '\n'
    for d in p['domains']:
        line = J(d['domain']) + '=' + J(d['regular'])
        for tag, tier in (('例外', 'exception'), ('硬', 'constraint')):
            for e in d[tier]: line += ';' + tag + '[' + '&'.join(('' if v else '!') + J(k) for k, v in e['when']) + ']=' + J(e['action'])
        text += line + '\n'
    units = count(text) if count else None
    if units is not None and (type(units) is not int or units < 0): raise ValueError('Invalid tokenizer count')
    ok = len(text) <= budget_chars and (budget_tokens is None or units <= budget_tokens)
    return {'status': 'experimental_unvalidated' if ok else 'budget_blocked', 'text': text if ok else None, 'characters': len(text), 'actual_tokens': units, 'policy_sha256': digest(canonical(p)), 'budget_chars': budget_chars, 'budget_tokens': budget_tokens,
            'scope_limit': 'Current effective-policy behavior only; no history, provenance, updateable event graph or real-person/model fidelity claim. Private original artifact remains necessary.'}


def render(artifact, budget_chars, domains=None, count=None, budget_tokens=None):
    """The same whole-domain export contract as the readable format."""
    encoded = encode(artifact, budget_chars, count, budget_tokens, domains)
    order = list(t.effective(artifact))
    wanted = order if domains is None else domains
    return {'status': 'budget_blocked' if encoded['status'] == 'budget_blocked' else 'candidate_unvalidated',
            'text': encoded['text'], 'required_characters': encoded['characters'], 'required_tokens': encoded['actual_tokens'],
            'budget_characters': budget_chars, 'budget_tokens': budget_tokens,
            'included_domains': wanted, 'omitted_domains': [d for d in order if d not in wanted],
            'source_unmodeled_spans': len(artifact['extraction']['unmodeled']),
            'historical_reconstruction_supported': False, 'source_semantic_fidelity_verified': False,
            'model_quality_measured': False, 'delivery_format': 'concise',
            'interpretation': 'Exact concise current-policy grammar tested only on D-0028 consumed synthetic policies. Source interpretation, real-person and cross-provider fidelity remain unverified. Whole prompt only; no truncation, subset selection or retry.'}


def decode(text):
    require_intact(text, 'encoded policy')
    if len(text) > 128000 or not text.startswith(HEADER) or not text.endswith('\n'): raise ValueError('Wrong policy envelope')
    lines = text[len(HEADER):-1].split('\n')
    if len(lines) < 2 or not lines[0].startswith('范围:') or not re.fullmatch(r'未建模:(0|[1-9][0-9]{0,3})', lines[1]): raise ValueError('Invalid metadata')
    p = {'scope': json.loads(lines[0][3:]), 'unmodeled': int(lines[1][4:]), 'domains': []}; decoder = json.JSONDecoder()
    for line in lines[2:]:
        domain, i = decoder.raw_decode(line); d = {'domain': domain, 'regular': [], 'exception': [], 'constraint': []}
        if line[i:i+1] != '=': raise ValueError('Missing default delimiter')
        d['regular'], i = decoder.raw_decode(line, i + 1)
        while i < len(line):
            if line[i:i+3] == ';例外': tier = 'exception'; i += 3
            elif line[i:i+2] == ';硬': tier = 'constraint'; i += 2
            else: raise ValueError('Invalid rule marker')
            if line[i:i+1] != '[': raise ValueError('Missing condition group')
            i += 1; literals = []
            while True:
                value = line[i:i+1] != '!'
                if not value: i += 1
                word, i = decoder.raw_decode(line, i); literals.append([word, value])
                if line[i:i+1] == ']': i += 1; break
                if line[i:i+1] != '&': raise ValueError('Invalid conjunction delimiter')
                i += 1
            if line[i:i+1] != '=': raise ValueError('Missing rule action')
            action, i = decoder.raw_decode(line, i + 1); d[tier].append({'when': literals, 'action': action})
        p['domains'].append(d)
    return validate(p)


def resolve(p, domain, context):
    validate(p)
    if not isinstance(context, dict) or any(not isinstance(k, str) or type(v) is not bool for k, v in context.items()): raise ValueError('Boolean context required')
    d = next((d for d in p['domains'] if d['domain'] == domain), None)
    if d is None: return {'status': 'unobserved', 'action': None}
    for tier in ('constraint', 'exception', 'regular'):
        rows = [{'when': [], 'action': a} for a in d[tier]] if tier == 'regular' else d[tier]
        selected = []; unknown = False
        for e in rows:
            if any(k in context and context[k] != v for k, v in e['when']): continue
            if any(k not in context for k, _ in e['when']): unknown = True
            else: selected.append(e['action'])
        if unknown: return {'status': 'context_unknown', 'action': None}
        if selected:
            actions = set(selected)
            return {'status': 'chosen' if len(actions) == 1 else 'conflict', 'action': next(iter(actions)) if len(actions) == 1 else None}
    return {'status': 'unobserved', 'action': None}


def prove(artifact):
    encoded = encode(artifact); decoded = decode(encoded['text']); expected = policy(artifact)
    if decoded != expected: raise ValueError('Policy did not round trip')
    cases = 0; domains = []
    for d in decoded['domains']:
        names = list(dict.fromkeys(k for tier in ('exception', 'constraint') for e in d[tier] for k, _ in e['when']))
        if len(names) > 8: raise ValueError('Exhaustive proof limited to8predicates/domain; never silently sample')
        for values in itertools.product((None, False, True), repeat=len(names)):
            context = {k: v for k, v in zip(names, values) if v is not None}; old = t.resolve(artifact, d['domain'], context); new = resolve(decoded, d['domain'], context)
            if new != {k: old[k] for k in ('status', 'action')}: raise ValueError('Current-policy behavior changed')
            cases += 1
        domains.append({'domain': d['domain'], 'predicates': len(names), 'partial_contexts': 3**len(names)})
    absent = 'unobserved-test'
    while any(d['domain'] == absent for d in decoded['domains']): absent += '-'
    if resolve(decoded, absent, {}) != {'status': 'unobserved', 'action': None}: raise ValueError('Unlisted domain behavior changed')
    return {'policy_round_trip': True, 'all_relevant_true_false_missing_contexts_equal': True, 'partial_contexts': cases, 'unlisted_domain_equal': True, 'domains': domains, 'external_model_calls': 0, 'not_model_quality': True}
