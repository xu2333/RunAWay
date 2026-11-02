"""Reproducible offline case design and fixed-denominator scorer; never calls a model."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('task_scenarios_corpus', HERE / 'corpus.py')
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def encoder_packet(profile):
    """Only one person's raw source; no questions, references or intervention guide."""
    data = corpus.build()
    if type(profile) is not str or profile not in data['sources']:
        raise ValueError('Unexpected person')
    return {'sources': data['sources'][profile]}


def reader_packet(profile, memory):
    """Explicitly supplied memory and own questions; never auto-load authored labels."""
    data = corpus.build()
    if type(profile) is not str or profile not in data['sources'] or type(memory) is not str:
        raise ValueError('Unexpected person/memory')
    return {'memory': memory, 'questions': data['questions'][profile]}


def intervention_packet(profile, case):
    """Edited source and the entire unchanged baseline bank; no author reference."""
    data = corpus.build()
    for mutation in data['mutations']:
        if (mutation['profile'], mutation['case']) == (profile, case):
            return {'sources': mutation['sources'],
                    'questions': data['questions'][profile]}
    raise ValueError('Unexpected person/case')


def score(records, data=None):
    """Exactly two planned reads/person, both orders/case; missing stays in denominator.

    Values are literal option labels or U, never position-dependent A/B. This is
    an evidence calculator, not a model runner or an authenticity verifier.
    """
    data = corpus.build() if data is None else data
    if type(records) is not list:
        raise ValueError('Records must be a list')
    indexed = {}
    for record in records:
        if type(record) is not dict or set(record) != {'profile', 'read_repeat', 'answers'}:
            raise ValueError('Record fields differ')
        pid, repeat, answers = record['profile'], record['read_repeat'], record['answers']
        if type(pid) is not str or pid not in data['sources'] or type(repeat) is not int or repeat not in (0, 1):
            raise ValueError('Unexpected person/read')
        if (pid, repeat) in indexed:
            raise ValueError('Duplicate read; best-of replacement forbidden')
        if type(answers) is not dict:
            raise ValueError('Answers must be a dictionary')
        allowed = {q['id']: list(q['options'].values()) + ['U'] for q in data['questions'][pid]}
        for qid, answer in answers.items():
            if qid not in allowed or type(answer) is not str or answer not in allowed[qid]:
                raise ValueError('Unexpected question/answer; use literal labels or U')
        indexed[pid, repeat] = answers
    result = {'planned_cases': len(data['rows']), 'strict_correct': 0, 'missing_cases': 0,
              'planned_answers': len(data['rows']) * 4, 'missing_answers': 0,
              'by_task': {}, 'known': {'planned': 0, 'correct': 0}, 'unknown': {'planned': 0, 'correct': 0},
              'answers_per_case': 4, 'independent_people': False, 'model_authenticity_verified': False,
              'independent_semantic_acceptance': False}
    for row in data['rows']:
        values = [indexed.get((row['profile'], r), {}).get(q) for r in (0, 1) for q in row['query_ids']]
        reference = row['contract']['reference']
        correct = all(v == reference for v in values)
        missing = sum(v is None for v in values)
        result['strict_correct'] += correct
        result['missing_cases'] += bool(missing)
        result['missing_answers'] += missing
        bucket = result['unknown' if reference == 'U' else 'known']
        bucket['planned'] += 1
        bucket['correct'] += correct
        task = result['by_task'].setdefault(row['contract']['intent'], {'planned': 0, 'correct': 0})
        task['planned'] += 1
        task['correct'] += correct
    return result


def score_transitions(baseline_records, intervention_records):
    """Require original AND changed-source references over both reads/orders.

    The 40 author-declared transitions are dependent on the baseline endpoints,
    not 40 additional independent people or observed memory-damage recoveries.
    """
    data = corpus.build()
    baseline = score(baseline_records, data)  # Validate records before indexing.
    if type(intervention_records) is not list:
        raise ValueError('Intervention records must be a list')
    rows = {(r['profile'], r['case']): r for r in data['rows']}
    indexed = {}
    for record in intervention_records:
        if type(record) is not dict or set(record) != {'profile', 'case', 'read_repeat', 'answers'}:
            raise ValueError('Intervention record fields differ')
        pid, case, repeat = record['profile'], record['case'], record['read_repeat']
        if type(pid) is not str or type(case) is not str or (pid, case) not in rows or type(repeat) is not int or repeat not in (0, 1):
            raise ValueError('Unexpected intervention person/case/read')
        key = pid, case, repeat
        if key in indexed:
            raise ValueError('Duplicate intervention read')
        answers = record['answers']
        if type(answers) is not dict:
            raise ValueError('Intervention answers must be a dictionary')
        allowed = {q['id']: list(q['options'].values()) + ['U'] for q in data['questions'][pid]}
        for qid, answer in answers.items():
            if qid not in allowed or type(answer) is not str or answer not in allowed[qid]:
                raise ValueError('Unexpected intervention question/answer')
        indexed[key] = answers
    original = {(r['profile'], r['read_repeat']): r['answers'] for r in baseline_records}
    result = {'planned_transitions': 40, 'strict_both_correct': 0, 'missing_transitions': 0,
              'planned_intervention_answers': 800, 'missing_intervention_answers': 0,
              'planned_target_answers': 160, 'missing_target_answers': 0,
              'non_target_preservation': {'planned_case_interventions': 160, 'strict_both_correct': 0, 'missing': 0},
              'baseline': baseline, 'independent_evidence': False,
              'source_edits_are_compressor_damage': False, 'model_authenticity_verified': False,
              'semantic_transitions_independently_verified': False}
    for mutation in data['mutations']:
        pid, case = mutation['profile'], mutation['case']
        row = rows[pid, case]
        before = [original.get((pid, repeat), {}).get(q) for repeat in (0, 1) for q in row['query_ids']]
        after = [indexed.get((pid, case, repeat), {}).get(q) for repeat in (0, 1) for q in row['query_ids']]
        missing = sum(v is None for v in after)
        full_ids = [q['id'] for q in data['questions'][pid]]
        result['missing_intervention_answers'] += sum(
            q not in indexed.get((pid, case, repeat), {}) for repeat in (0, 1) for q in full_ids)
        result['strict_both_correct'] += (all(v == row['contract']['reference'] for v in before) and
                                          all(v == mutation['contract']['reference'] for v in after))
        result['missing_transitions'] += any(v is None for v in before + after)
        result['missing_target_answers'] += missing
        for other in data['rows']:
            if other['profile'] != pid or other['case'] == case:
                continue
            old_values = [original.get((pid, repeat), {}).get(q) for repeat in (0, 1) for q in other['query_ids']]
            new_values = [indexed.get((pid, case, repeat), {}).get(q) for repeat in (0, 1) for q in other['query_ids']]
            preservation = result['non_target_preservation']
            preservation['strict_both_correct'] += all(v == other['contract']['reference'] for v in old_values + new_values)
            preservation['missing'] += any(v is None for v in old_values + new_values)
    return result


def fixtures(data):
    """Declared reference/witness vectors calibrate scoring, not model behaviour."""
    result = {k: [] for k in ('author_reference', 'all_unknown', 'declared_fault', 'paired_person')}
    for pid in data['sources']:
        own = [r for r in data['rows'] if r['profile'] == pid]
        paired = {r['case']: r for r in data['rows'] if r['profile'] == data['pairs'][pid]}
        for repeat in (0, 1):
            for kind in result:
                answers = {}
                for row in own:
                    value = {'author_reference': row['contract']['reference'], 'all_unknown': 'U',
                             'declared_fault': row['contract']['contrasts'][0]['predicted_answer'],
                             'paired_person': paired[row['case']]['contract']['reference']}[kind]
                    answers.update({q: value for q in row['query_ids']})
                result[kind].append({'profile': pid, 'read_repeat': repeat, 'answers': answers})
    return result


def artifacts():
    data = corpus.build()
    interventions = []
    for mutation in data['mutations']:
        baseline = data['sources'][mutation['profile']]
        changed = mutation['sources']
        changed_entries = [(a, b) for a, b in zip(baseline['sources'], changed['sources']) if a != b]
        if len(changed_entries) != 1 or changed_entries[0][0]['role'] != 'user':
            raise ValueError('Intervention must change exactly one user message')
        before, after = changed_entries[0]
        if before['id'] != mutation['source_id'] or before['text'].replace(mutation['before'], mutation['after'], 1) != after['text']:
            raise ValueError('Intervention is not the declared exact span edit')
        interventions.append({**{k: mutation[k] for k in ('profile', 'case', 'operation', 'source_id', 'before', 'after')},
                              'baseline_source_sha256': digest(baseline), 'modified_source_sha256': digest(changed),
                              'modified_sources': changed, 'author_contract': mutation['contract'],
                              'unchanged_full_question_packet_sha256': digest(data['questions'][mutation['profile']]),
                              'semantic_transition_independently_verified': False})
    outcomes = {k: score(v, data) for k, v in fixtures(data).items()}
    if {k: v['strict_correct'] for k, v in outcomes.items()} != {
            'author_reference': 40, 'all_unknown': 12, 'declared_fault': 0, 'paired_person': 8}:
        raise ValueError('Authored fixture discrimination changed')
    unique_forms = {digest(q) for packet in data['questions'].values() for q in packet}
    design = {'version': 'task_scenarios_v1', 'status': 'offline_authored_calibration_only',
              'profiles': 8, 'dependent_template_families': 4,
              'source_messages': sum(len(s['sources']) for s in data['sources'].values()),
              'primary_cases': len(data['rows']), 'known': 28, 'unknown': 12,
              'unique_public_forms': len(unique_forms), 'person_form_combinations': 80,
              'planned_reads_per_person': 2, 'answers_per_case': 4, 'planned_answers': 160,
              'tasks': dict(collections.Counter(r['contract']['intent'] for r in data['rows'])),
              'source_interventions': len(interventions), 'authored_changed_reference_transitions': 40,
              'planned_intervention_answer_slots': 800,
              'intervention_questions_equal_full_baseline_packet': True,
              'source_interventions_are_compressor_damage': False,
              'counterfactual_answer_transitions_semantically_verified': False,
              'model_calls': 0, 'new_service_authority': False, 'real_person_data': False,
              'semantic_reference_independently_accepted': False, 'independent_holdout': False,
              'existing_benchmarks_or_defaults_changed': False,
              'source_sha256': {p: digest(s) for p, s in data['sources'].items()},
              'canonical_source_characters': {
                  p: len(json.dumps(s, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
                  for p, s in data['sources'].items()},
              'question_sha256': {p: digest(q) for p, q in data['questions'].items()}}
    return {'sources.synthetic.json': data['sources'], 'questions.public.json': data['questions'],
            'author-reference.synthetic.json': {'rows': data['rows'], 'pairs': data['pairs']},
            'source-interventions.synthetic.json': interventions,
            'design.json': design, 'fixture-calibration.json': outcomes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write reviewed fictional artifacts locally; no service calls')
    parser.add_argument('--score', type=Path, help='Score local literal-label records, without sending or authenticating them')
    parser.add_argument('--transitions', type=Path, help='With --score, require correct baseline and changed-source answers')
    args = parser.parse_args()
    if args.transitions and not args.score:
        parser.error('--transitions requires --score baseline records')
    if args.write and args.score:
        parser.error('--write and --score are separate operations')
    if args.score:
        baseline = json.loads(args.score.read_text(encoding='utf-8'))
        result = (score_transitions(baseline, json.loads(args.transitions.read_text(encoding='utf-8')))
                  if args.transitions else score(baseline))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    outputs = artifacts()
    for name, value in outputs.items():
        path = HERE / name
        text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
        if args.write:
            path.write_text(text, encoding='utf-8')
        elif path.read_text(encoding='utf-8') != text:
            raise ValueError('Artifact drift: ' + name)
    print(json.dumps({'design': outputs['design.json'],
                      'fixture_correct_not_model_scores': {k: v['strict_correct'] for k, v in outputs['fixture-calibration.json'].items()}},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
