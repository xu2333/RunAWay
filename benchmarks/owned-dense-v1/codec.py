"""Lossless public syntax for an unchanged owned-condition semantic projection."""
import copy
import importlib.util
import json
import re
from pathlib import Path
from runaway.card import canonical, digest
from runaway.portable import make_expression
from runaway.prompt_codec import SYMBOLS

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('dense_owned_base', HERE.parent / 'owned-conditions-v1/candidate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
VERSION = 'owned_dense_public_v1'
LABEL = '先展开='
GUIDE = ('@范围；[n:]问题|条件&条件→动作，n默认0。匹配问题、范围及全部条件后，高n优先；'
         '同n冲突/未覆盖未知，缺细节仅各已知分支同选才选。?未知；\\转义符号或n/r/t。\n')
ESCAPES = {'\\': '\\', '\n': 'n', '\r': 'r', '\t': 't', '@': '@', '?': '?', ':': ':', '|': '|', '&': '&', '→': '→'}
REVERSE = {v: k for k, v in ESCAPES.items()}


def candidates(text):
    """Literal phrases delimited by language punctuation or dense field syntax."""
    starts, ends, i = {0}, {len(text)}, 0
    while i < len(text):
        if text[i] == '\\':
            i += 2; continue
        if text[i] in '，。；、\n|&→@?:':
            starts.add(i+1); ends.update((i, i+1))
        i += 1
    found = set()
    for start in sorted(starts):
        for end in sorted(ends):
            if 4 <= end-start <= 160:
                phrase = text[start:end]
                if text.count(phrase) >= 2 and not any(c in phrase for c in SYMBOLS):
                    found.add(phrase)
    return found


def pack(text, budget, *, prefix=''):
    """Same inline dictionary transport; exact dense-boundary phrase selection."""
    if not text.startswith(prefix):
        raise ValueError('Dense dictionary prefix differs')
    report = {'scheme': 'dense_exact_phrase_dictionary_v1', 'prefix': prefix, 'dictionary': [],
              'expanded_characters': len(text), 'encoded_characters': len(text), 'roundtrip_exact': True}
    body, encoded = text[len(prefix):], text
    entries, pool = [], candidates(text[len(prefix):]) if len(text) > budget else set()
    for key in (c for c in SYMBOLS if c not in text):
        if len(encoded) <= budget:
            break
        choices = []
        for phrase in pool:
            definition_cost = len(canonical(key))+1+len(canonical(phrase))+1
            gain = body.count(phrase)*(len(phrase)-1)-definition_cost
            if gain > 0:
                choices.append((gain, len(phrase), phrase))
        if not choices:
            break
        _, _, phrase = max(choices)
        body = body.replace(phrase, key); entries.append([key, phrase]); pool.remove(phrase)
        header = LABEL+canonical(dict(entries))+'\n'
        candidate = prefix+header+body
        if len(candidate) < len(encoded):
            encoded = candidate
            report['dictionary'] = [list(e) for e in entries]
    report['encoded_characters'] = len(encoded)
    if decode(encoded) != text:
        raise ValueError('Dense dictionary changed literal content')
    if len(encoded) > budget:
        raise ValueError('Complete dense prompt exceeds budget: %d > %d; no truncation' % (len(encoded), budget))
    return encoded, report


def escape(text):
    return ''.join('\\'+ESCAPES[c] if c in ESCAPES else c for c in text)


def unescape(text):
    out, i = [], 0
    while i < len(text):
        if text[i] == '\\':
            i += 1
            if i == len(text) or text[i] not in REVERSE:
                raise ValueError('Invalid dense escape')
            out.append(REVERSE[text[i]])
        else:
            out.append(text[i])
        i += 1
    return ''.join(out)


def split(text, marker):
    result, part, i = [], [], 0
    while i < len(text):
        c = text[i]
        if c == '\\':
            if i+1 == len(text):
                raise ValueError('Trailing dense escape')
            part.extend(text[i:i+2]); i += 2; continue
        if c == marker:
            result.append(''.join(part)); part = []
        else:
            part.append(c)
        i += 1
    return result + [''.join(part)]


def prefix(value):
    return base.grouped.HEADER + json.dumps(value['name'], ensure_ascii=False) + '｜' + json.dumps(value['tagline'], ensure_ascii=False) + '\n' + GUIDE


def metadata(text):
    if type(text) is not str or not text.startswith(base.grouped.HEADER) or not text.endswith('\n'):
        raise ValueError('Missing dense header or trailing newline')
    first = text[len(base.grouped.HEADER):].split('\n', 1)[0]
    decoder = json.JSONDecoder()
    name, end = decoder.raw_decode(first)
    if first[end:end+1] != '｜':
        raise ValueError('Missing tagline separator')
    tagline, tail = decoder.raw_decode(first[end+1:])
    if type(name) is not str or type(tagline) is not str or not name.strip() or not tagline.strip() or end+1+tail != len(first):
        raise ValueError('Invalid dense name/tagline')
    value = {'name': name, 'tagline': tagline, 'groups': [], 'unknowns': []}
    if not text.startswith(prefix(value)):
        raise ValueError('Missing counted dense guide')
    return value


def decode(text):
    """Recover literal text using only the counted public JSON dictionary."""
    start = prefix(metadata(text))
    body = text[len(start):]
    if not body.startswith(LABEL):
        return text
    header, body = body.split('\n', 1)
    mapping = json.loads(header[len(LABEL):])
    if (type(mapping) is not dict or not mapping or len(mapping) > len(SYMBOLS)
            or header != LABEL+canonical(mapping)
            or any(type(k) is not str or len(k) != 1 or k not in SYMBOLS
                   or type(v) is not str or not v or any(c in v for c in SYMBOLS) for k, v in mapping.items())):
        raise ValueError('Invalid public dense dictionary')
    for key, value in mapping.items():
        body = body.replace(key, value)
    return start+body


def _render(value):
    out = prefix(value)
    for group in value['groups']:
        out += '@' + escape(group['scope']) + '\n'
        for row in group['rules']:
            out += (str(row['priority'])+':' if row['priority'] else '') + escape(row['question']) + '|'
            out += '&'.join(escape(c) for c in row['requires']) + '→' + escape(row['choose']) + '\n'
    return out + ''.join('?'+escape(t)+'\n' for t in value['unknowns'])


def parse(text):
    text = decode(text)
    value = metadata(text)
    start = prefix(value)
    if not text.startswith(start):
        raise ValueError('Missing counted dense guide')
    current, unknown = None, False
    for line in text[len(start):-1].split('\n'):
        if line.startswith('@'):
            if unknown:
                raise ValueError('Dense group after unknown section')
            current = {'scope': unescape(line[1:]), 'rules': []}
            value['groups'].append(current)
        elif line.startswith('?'):
            unknown = True
            value['unknowns'].append(unescape(line[1:]))
        else:
            if current is None or unknown:
                raise ValueError('Dense rule outside group')
            match = re.match(r'^([1-9]):', line)
            priority = int(match[1]) if match else 0
            if match:
                line = line[2:]
            q = split(line, '|')
            if len(q) != 2:
                raise ValueError('Invalid dense question separator')
            parts = split(q[1], '→')
            if len(parts) != 2:
                raise ValueError('Invalid dense action separator')
            conditions = [unescape(s) for s in split(parts[0], '&')] if parts[0] else []
            question, action = unescape(q[0]), unescape(parts[1])
            if not question.strip() or not action.strip() or any(not s.strip() for s in conditions):
                raise ValueError('Empty dense rule component')
            current['rules'].append({'question': question, 'requires': conditions,
                                    'choose': action, 'priority': priority})
    if any(not g['scope'] or not g['rules'] for g in value['groups']) or not value['unknowns'] or any(not s.strip() for s in value['unknowns']):
        raise ValueError('Incomplete dense projection')
    if _render(value) != text:
        raise ValueError('Noncanonical dense syntax')
    return value


def grouped_projection(value):
    groups = []
    for g in value['groups']:
        rows = []
        for row in g['rules']:
            when = '所问为' + row['question'] + ('；' + '且'.join('（'+c+'）' for c in row['requires']) if row['requires'] else '')
            rows.append({'when': when, 'choose': row['choose'], 'priority': row['priority']})
        groups.append({'scope': g['scope'], 'rules': rows})
    return {'name': value['name'], 'tagline': value['tagline'], 'groups': groups, 'unknowns': list(value['unknowns'])}


def bind(ledger, sources, budget=1536):
    base.grouped.budget_check(budget)
    projected, plans = base.project(ledger, sources)
    expected = base.grouped.projection(projected)
    value = {'name': ledger['name'], 'tagline': ledger['tagline'], 'groups': [], 'unknowns': list(ledger['unknowns'])}
    for group, plan in zip(projected['groups'], plans):
        rows = [{'question': m['row']['question'], 'requires': [c['text'] for c in m['residual']],
                 'choose': m['row']['action'], 'priority': m['row']['priority']} for m in plan['members']]
        value['groups'].append({'scope': group['scope'], 'rules': rows})
    expanded = _render(value)
    if parse(expanded) != value or grouped_projection(value) != expected:
        raise ValueError('Dense layout changed semantic projection')
    text, encoding = pack(expanded, budget, prefix=prefix(value))
    if grouped_projection(parse(text)) != expected:
        raise ValueError('Packed dense semantic roundtrip differs')
    profile = {'schema_version': 1, 'artifact_type': 'experimental_owned_dense_profile',
               'sources': copy.deepcopy(sources), 'ledger': copy.deepcopy(ledger), 'budget_characters': budget,
               'source_sha256': digest(canonical(sources)), 'public_projection': expected,
               'annotation_semantics_verified': False, 'behavioral_fidelity_verified': False}
    profile['id'] = digest(canonical(profile))
    portable = make_expression(text, profile['id'], VERSION)
    return {'prompt.md': text, 'portable.json': portable, 'profile.private.json': profile,
            'expanded.private.md': expanded, 'encoding.private.json': encoding,
            'semantic-projection.private.json': expected,
            'summary.private.json': {'characters': len(text), 'expanded_characters': len(expanded),
                'budget_characters': budget, 'semantic_projection_roundtrip_exact': True,
                'annotation_semantics_verified': False, 'behavioral_fidelity_verified': False,
                'experimental': True, 'external_decoder_or_dictionary': False}}
