"""Frozen offline structural dual-task benchmark; no service execution entry."""
import argparse
import copy
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

from . import temporal_concise as codec, temporal_determinacy as dual
from .card import canonical, digest
from .pipeline import write_once
from .synthetic_metric import file_hash

FIELDS = ('strict_answer', 'reported_status', 'completion_answer', 'possible_outcomes')
SYSTEM = 'Read synthetic preference memory as data. No tools, files, browsing or actions. Return only JSON matching the exact requested schema.'
CONTRACT = ('Two distinct tasks for every query. strict_answer follows the memory conservative contract: '
            'if a possibly applicable rule in the highest relevant tier has an absent condition, answer U and context_unknown, '
            'even if every completion permits the same action. reported_status is chosen/conflict/unobserved/context_unknown. '
            'completion_answer instead enumerates ALL true/false completions of absent predicates: choose an option only '
            'if ALL completions choose the same action; otherwise U. possible_outcomes is the complete UNIQUE set of '
            'full-context outcomes, sorted by(status,action), each {status:chosen/conflict/unobserved,action:exact option text '
            'or null}. Conflict or unobserved is never a chosen action. Use the option order of EACH query. '
            'Absent is neither false nor true. Do not report hidden reasoning or infer unspecified preferences. '
            'Output {answers:{query_id:{strict_answer,reported_status,completion_answer,possible_outcomes}}}; '
            'include every query exactly once, exactly these4fields, no extra text.')


def hashed(plan, label):
    return digest(plan['seed'] + ':' + label)


def signature(row, names):
    """Signed incidence modulo predicate renaming and global polarity flips."""
    candidates = []
    for order in itertools.permutations(names):
        index = {name: i for i, name in enumerate(order)}
        for flips in itertools.product((False, True), repeat=len(names)):
            tiers = []
            for tier in ('constraint', 'exception'):
                rules = [sorted((index[k], bool(v) ^ flips[index[k]]) for k, v in e['when']) for e in row[tier]]
                tiers.append(sorted(rules))
            candidates.append(canonical([len(row['regular']), tiers]))
    return min(candidates)


def motif_row(motif, member):
    def action(a): return str(member) if a == 'member' else str(1-member) if a == 'inverse_member' else a
    return {'regular': list(motif['regular']), **{tier: [dict(when=e['when'], action=action(e['action'])) for e in motif[tier]] for tier in ('exception', 'constraint')}}


def structural_audit(plan):
    rows = {}
    for m in plan['motifs']:
        names = list('pqr'[:m['n']]); key = signature(motif_row(m, 0), names)
        rows[m['id']] = dict(split=m['split'], signature=key)
    dev = {r['signature'] for r in rows.values() if r['split'] == 'development'}
    held = {r['signature'] for r in rows.values() if r['split'] == 'holdout'}
    old = {'regular': ['0'], 'exception': [dict(when=[['p', True]], action='1')],
           'constraint': [dict(when=[['p', True], ['q', True]], action='0')]}
    if dev & held or signature(old, ['p', 'q']) in held: raise ValueError('Structural split overlaps; no redraw')
    if len(dev) != 3 or len(held) != 4: raise ValueError('Frozen structural family count changed')
    return dict(families=rows, development_classes=len(dev), holdout_classes=len(held), disjoint=True,
                heldout_disjoint_from_D0031=True, transformations='all predicate permutations and global per-predicate polarity flips; tier,arity,sharing,relative polarity,regular multiplicity preserved')


def sampled_policy(plan, motif, member):
    """Sample lexical/coordinate nuisance only; never select on scores."""
    fid = motif['id']; pool = plan['sampling']['lexical_pool']; ids = [m['id'] for m in plan['motifs']]
    lexical = sorted(range(len(pool)), key=lambda i: (hashed(plan, 'lexicon:'+str(i)), i))[ids.index(fid)]
    words = pool[lexical]; actions = list(words['actions'])
    if int(hashed(plan, fid+':actions'), 16) & 1: actions.reverse()
    predicates = plan['sampling']['predicates']
    selected = sorted(range(len(predicates)), key=lambda i: (hashed(plan, fid+':predicate:'+str(i)), i))[:motif['n']]
    names = {k: predicates[i] for k, i in zip('pqr', selected)}
    row = motif_row(motif, member)
    for tier in ('exception', 'constraint'):
        row[tier] = [dict(when=[[names[k], bool(v) ^ bool(int(hashed(plan, fid+':flip:'+k), 16) & 1)] for k, v in e['when']], action=actions[int(e['action'])]) for e in row[tier]]
    row['regular'] = [actions[int(a)] for a in row['regular']]; row['domain'] = words['domain']
    policy = dict(scope='仅本份合成记录中的当前局部选择，不代表真人。', unmodeled=0, domains=[row])
    return codec.validate(policy), sorted(names.values()), actions


def truth_regions(policy, domain):
    """Independent set algebra oracle; does not call production resolution."""
    row = next((d for d in policy['domains'] if d['domain'] == domain), None)
    if row is None: return [], [()], [], None
    names = sorted({k for tier in ('constraint', 'exception') for e in row[tier] for k, _ in e['when']})
    valuations = list(itertools.product((False, True), repeat=len(names))); tiers = []
    for tier in ('constraint', 'exception', 'regular'):
        rules = [dict(when=[], action=a) for a in row[tier]] if tier == 'regular' else row[tier]
        regions = []
        for rule in rules:
            region = {i for i, values in enumerate(valuations) if all(dict(zip(names, values))[k] == v for k, v in rule['when'])}
            regions.append((region, rule['action']))
        tiers.append(regions)
    return names, valuations, tiers, row


def region_resolve(regions, context):
    names, valuations, tiers, row = regions
    if row is None: return dict(status='unobserved', action=None)
    compatible = {i for i, values in enumerate(valuations) if all(dict(zip(names, values))[k] == v for k, v in context.items() if k in names)}
    for tier in tiers:
        intersects = [(r & compatible, a) for r, a in tier]
        if any(r and r != compatible for r, _ in intersects): return dict(status='context_unknown', action=None)
        chosen = {a for r, a in intersects if r == compatible}
        if chosen: return dict(status='chosen' if len(chosen) == 1 else 'conflict', action=next(iter(chosen)) if len(chosen) == 1 else None)
    return dict(status='unobserved', action=None)


def expected_row(policy, domain, context, options):
    regions = truth_regions(policy, domain); names, valuations, _, _ = regions
    strict = region_resolve(regions, context)
    outcomes = dual.unique_outcomes(region_resolve(regions, dict(zip(names, values))) for values in valuations
        if all(dict(zip(names, values))[k] == v for k, v in context.items() if k in names))
    action = dual.completion_action(outcomes)
    letter = lambda value: 'U' if value is None else next(k for k, v in options.items() if v == value)
    strict_letter = letter(strict['action']); completion_letter = letter(action)
    # Bind action identity through actual option text, independently of option order.
    return dict(strict_answer=strict_letter, reported_status=strict['status'], completion_answer=completion_letter,
                completion_action='U' if action is None else action, possible_outcomes=outcomes)


def build_split(plan, split):
    if split not in ('development', 'holdout'): raise ValueError('Unknown split')
    people = []; expected = {}; policies = {}
    for motif in plan['motifs']:
        if motif['split'] != split: continue
        fid = motif['id']; pair_ids = ['s-'+digest(plan['seed']+':'+fid+':'+str(m))[:12] for m in (0, 1)]
        for member, pid in enumerate(pair_ids):
            policy, names, actions = sampled_policy(plan, motif, member); policies[pid] = policy; cases = []; expected[pid] = {}
            contexts = [{k: v for k, v in zip(names, values) if v is not None} for values in itertools.product((None, False, True), repeat=len(names))]
            for index, (domain, context) in enumerate([(policy['domains'][0]['domain'], c) for c in contexts]+[('未观察的领域', {})]):
                for order in (0, 1):
                    options = dict(zip(('A', 'B'), actions if order == 0 else list(reversed(actions)))); options['U'] = '材料不足，无法判断'
                    key = 'q-'+digest(pid+':'+str(index)+':'+str(order))[:14]; e = expected_row(policy, domain, context, options)
                    mapping = {k: str(actions.index(v)) if k != 'U' else 'U' for k, v in options.items()}
                    e['completion_action'] = mapping[e['completion_answer']]; expected[pid][key] = e
                    text = '；'.join(k+'：'+('未提供' if k not in context else '是' if context[k] else '否') for k in names) if domain != '未观察的领域' else '材料没有这个领域的记录'
                    public = dict(id=key, task='current_choice', domain=domain, context=context, question=f'仅按当前记录比较【{domain}】。{text}。', answer_options=options)
                    strict = e['reported_status']; active_hard = False
                    if domain == policy['domains'][0]['domain']:
                        active_hard = strict == 'chosen' and any(all(context.get(k) == v and k in context for k, v in rule['when']) for rule in policy['domains'][0]['constraint'])
                    tags = ['complete_context' if len(context) == len(names) else 'partial_context', 'hard_constraints']
                    if strict == 'context_unknown': tags.append('unknowns')
                    if strict == 'conflict': tags.append('conflicts')
                    cases.append(dict(public=public, scenario=fid+':'+str(index), key=fid, at=1, context=context,
                        tags=tags, options=mapping, order=order, instruction=None, gold=e['strict_answer'], action=mapping[e['strict_answer']],
                        expected_status=strict, active_hard=active_hard, completion_kind=('unknown_but_determinate' if e['completion_action'] != 'U' else 'unknown_and_indeterminate') if strict == 'context_unknown' else strict))
            people.append(dict(id=pid, pair_id=fid, twin=pair_ids[1-member], target_axes=[fid], family=fid, member=member, source_cutoff=1, cases=cases))
    body = dict(origin='fully_synthetic', purpose='frozen_structural_dual_'+split, people=people, historical_planned=0)
    return {**body, 'id':digest(canonical(body))}, expected, policies


def records_for(world, policies, control):
    result = {}
    for p in world['people']:
        pid = p['id']; policy = copy.deepcopy(policies[p['twin'] if control == 'wrong_person' else pid]); d = policy['domains'][0]
        if control == 'default_only': d['exception'] = []; d['constraint'] = []
        if control == 'flip_first_literal':
            tier = 'constraint' if d['constraint'] else 'exception'; k, v = d[tier][0]['when'][0]; d[tier][0]['when'][0] = [k, not v]
        names = sorted({k for tier in ('constraint', 'exception') for e in d[tier] for k, _ in e['when']})
        result[pid] = {}
        for c in p['cases']:
            context = dict(c['context'])
            if control in ('assume_missing_false', 'assume_missing_true'):
                context = {**{k:control == 'assume_missing_true' for k in names}, **context}
            view = dual.completion_view(policy, c['public']['domain'], context); strict = view['strict']; outcomes = view['possible_outcomes']
            if control == 'invariant_action_loses_unknown' and strict['status'] == 'context_unknown' and view['completion_action'] is not None:
                strict = dict(status='chosen', action=view['completion_action'])
            if control == 'conflict_reported_unobserved':
                if strict['status'] == 'conflict': strict = dict(status='unobserved', action=None)
                outcomes = dual.unique_outcomes(dict(status='unobserved', action=None) if r['status'] == 'conflict' else r for r in outcomes)
            if control == 'drop_completion_branch' and len(outcomes) > 1: outcomes = outcomes[:1]
            options = c['public']['answer_options']; letter = lambda a: 'U' if a is None else next(k for k, v in options.items() if k != 'U' and v == a)
            result[pid][c['public']['id']] = dict(strict_answer=letter(strict['action']), reported_status=strict['status'],
                completion_answer=letter(dual.completion_action(outcomes)), possible_outcomes=outcomes)
        if control == 'missing_first_query': del result[pid][min(result[pid])]
    return result


def schema_for(world_person):
    item = dict(type='object', properties={
        'strict_answer':dict(type='string', enum=['A','B','U']),
        'reported_status':dict(type='string', enum=['chosen','conflict','unobserved','context_unknown']),
        'completion_answer':dict(type='string', enum=['A','B','U']),
        'possible_outcomes':dict(type='array', minItems=1, maxItems=4, items=dict(type='object', properties={'status':dict(type='string',enum=['chosen','conflict','unobserved']), 'action':dict(type=['string','null'])}, required=['status','action'], additionalProperties=False))}, required=list(FIELDS), additionalProperties=False)
    properties = {c['public']['id']: item for c in world_person['cases']}
    return dict(type='object', properties={'answers':dict(type='object',properties=properties,required=list(properties),additionalProperties=False)}, required=['answers'], additionalProperties=False)


def measure(text, count=None):
    return dict(characters=len(text), utf8_bytes=len(text.encode()), actual_local_vocabulary_tokens=count(text) if count else None)


def jobs_for(plan, world, policies, count=None):
    jobs = []
    for p in world['people']:
        memory = codec.serialize(policies[p['id']]); payload = dict(memory=memory, queries=[c['public'] for c in p['cases']])
        request = dict(system=SYSTEM, prompt=CONTRACT+'\nINPUT_JSON:\n'+canonical(payload), schema=schema_for(p))
        limits = plan['reader_contract']['budgets']; lengths = measure(memory, count); envelope = measure(canonical(request), count)
        if lengths['characters'] > limits['whole_memory_characters_max'] or envelope['utf8_bytes'] > limits['canonical_request_utf8_bytes_max']: raise ValueError('Frozen request length gate failed')
        if count and lengths['actual_local_vocabulary_tokens'] > limits['whole_memory_local_vocabulary_tokens_max']: raise ValueError('Frozen memory token gate failed')
        jobs.append(dict(person_id=p['id'], request_id=digest(canonical(request)), request=request, whole_memory_lengths=lengths, canonical_request_lengths=envelope))
    return jobs


def audit_split(plan, world, expected, policies, count=None):
    records = {name:records_for(world, policies, name) for name in plan['controls']}
    scores = {name:dual.score_records(world, rows, expected_records=expected, tasks=('current_choice','joint')) for name, rows in records.items()}
    n = sum(len(p['cases']) for p in world['people']); keys = ('strict_choice','reported_rule_status','completion_choice','possible_outcomes')
    checks = dict(intact_all_fields=all(scores['intact_dual_program'][k]['joint']['correct'] == n for k in keys),
        every_control_detected=all(any(scores[name][k]['joint']['correct'] < n for k in keys) for name in plan['controls'][1:]),
        invariant_action_preserved_status_lost=scores['invariant_action_loses_unknown']['completion_choice']['joint']['correct'] == n and scores['invariant_action_loses_unknown']['reported_rule_status']['joint']['correct'] < n,
        conflict_hidden_in_both_choices=scores['conflict_reported_unobserved']['strict_choice']['joint']['correct'] == scores['conflict_reported_unobserved']['completion_choice']['joint']['correct'] == n and scores['conflict_reported_unobserved']['reported_rule_status']['joint']['correct'] < n,
        missing_denominator_fixed=all(scores['missing_first_query'][k]['joint']['missing'] == len(world['people']) and scores['missing_first_query'][k]['joint']['planned'] == n for k in keys))
    groups = {}; family = {}
    for p in world['people']:
        for c in p['cases']:
            groups[c['completion_kind']] = groups.get(c['completion_kind'],0)+1
        family.setdefault(p['family'],[]).append(p['id'])
    discrimination = {}
    for control in ('assume_missing_false','assume_missing_true','drop_completion_branch'):
        selected = [(p,c) for p in world['people'] for c in p['cases'] if c['completion_kind']=='unknown_and_indeterminate']
        errors = sum(records[control][p['id']][c['public']['id']]['possible_outcomes'] != expected[p['id']][c['public']['id']]['possible_outcomes'] for p,c in selected)
        discrimination[control] = dict(errors=errors, planned=len(selected)); checks[control+'_changing_subset_detected'] = errors > 0
    jobs = jobs_for(plan, world, policies, count)
    costs = {control:{p['id']:measure(canonical(dict(answers=rows[p['id']])),count) for p in world['people']} for control,rows in records.items()}
    report = dict(passed=all(checks.values()), checks=checks, planned=n, historical=dict(planned=0,status='unmeasured'),
        family_pairs=len(family), people=len(world['people']), correlated_cases=True, groups=groups,
        controls=scores, changing_missing_sensitivity=discrimination,
        families={fid:{name:{k:dual.score_records(dict(world,people=[p for p in world['people'] if p['id'] in ids]), {pid:rows[pid] for pid in ids}, {pid:expected[pid] for pid in ids}, tasks=('current_choice','joint'))[k]['joint']['correct'] for k in keys} for name,rows in records.items()} for fid,ids in family.items()},
        complete_program_output_lengths=costs, reader_jobs=jobs, external_model_calls=0, experimental_service_tokens=0)
    return report, records


def implementation_hashes(root):
    files = sorted((root/'runaway').glob('*.py')) + [root/'tests/test_structural_dual.py']
    return {str(p.relative_to(root)):file_hash(p) for p in files}


def execute_offline(design, out, count=None, tokenizer=None):
    """One local lifecycle. No retry, resampling or model execution code."""
    design = Path(design); plan = json.loads(design.read_text()); out = Path(out); out.mkdir(parents=True,exist_ok=False)
    root = Path(__file__).resolve().parents[1]; hashes = implementation_hashes(root)
    write_once(out/'plan.synthetic.json', plan); write_once(out/'structural-audit.synthetic.json', structural_audit(plan))
    receipt = dict(design_sha256=file_hash(design), implementation_hashes=hashes, phase='implementation_frozen_before_any_draw',
                   created_at=datetime.now(timezone.utc).isoformat(), external_model_calls=0)
    with (design.parent/'generation-intent.json').open('x') as handle:
        json.dump(dict(receipt,output=str(out.resolve())),handle,indent=2)
    write_once(out/'implementation-freeze.json', receipt)
    completed = {}
    for split in ('development','holdout'):
        if implementation_hashes(root) != hashes: raise ValueError('Implementation changed after freeze; stop version')
        if split == 'holdout': write_once(out/'holdout-entry-freeze.json', dict(
            development_report_sha256=file_hash(out/'development-report.synthetic.json'),
            implementation_hashes=hashes, entered_at=datetime.now(timezone.utc).isoformat()))
        world, expected, policies = build_split(plan, split)
        report, records = audit_split(plan, world, expected, policies, count)
        completed[split] = (world, policies, report)
        for name, data in [('world',world),('expected',expected),('policies',policies),('report',report),('program-records',records)]:
            write_once(out/(split+'-'+name+'.synthetic.json'), data)
        write_once(out/(split+'-receipt.json'),dict(implementation_hashes_match=True,passed=report['passed'],planned=report['planned'],holdout_consumed=split=='holdout'))
        if not report['passed']: raise ValueError(split+' calibration gate failed; keep failure and stop, no redraw')
    dev, policies, dev_report = completed['development']; held_report = completed['holdout'][2]
    selected = [p for p in dev['people'] if p['family'] == 'overlap_exception_conflict']
    swapped = dict(policies, **{p['id']:policies[p['twin']] for p in selected})
    wrong_jobs = jobs_for(plan,dict(dev,people=selected),swapped,count)
    service_design = dict(status='design_only_not_authorized_not_executable',calls_max=16,
        stages={'development_intact':6,'development_wrong_person':2,'holdout_intact':8},
        development_jobs=dev_report['reader_jobs'],wrong_person_jobs=wrong_jobs,holdout_jobs=held_report['reader_jobs'],
        gates='Development intact all4fields exact per family,contrasts and option consistency exact; wrong-person responses all4fields match manipulated-policy reference and lose original target contrast. Any failure stops before holdout. Holdout reported by4structural families,original strict task and completion task separate. No sample selection or change from outcomes.',
        stop='Any transport,timeout,parse/schema,identity,usage,freeze or budget error stops all remaining calls. Zero retry/repair/resampling; no old requests or budgets.180seconds plus2+2cleanup proposed; model,runtime,isolation,exact bound proposal and direct approval still required before execution.',
        approval=False,model=None,external_model_calls=0,interpretation='Not a compressor comparison or real-person claim. Program-audited holdout is consumed,not a fresh reusable holdout. Actual payloads omit gold and latent structures.')
    write_once(out/'service-design.synthetic.json',service_design)
    write_once(out/'completion.json', dict(status='complete_offline_structural_audit',holdout_status='consumed_program_audit_not_fresh_reusable_holdout',
        tokenizer=tokenizer or dict(kind='not_measured'),external_model_calls=0,experimental_service_tokens=0,
        native_chat_usage='Separate host development accounting; not0.', model_quality_measured=False))
    return dict(status='complete_offline_structural_audit',external_model_calls=0)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--design',required=True); parser.add_argument('--out',required=True); parser.add_argument('--tokenizer'); args=parser.parse_args(); model=None
    try:
        count=None; metadata=None
        if args.tokenizer:
            plan=json.loads(Path(args.design).read_text())
            if file_hash(args.tokenizer) != plan['reader_contract']['tokenizer_sha256']: raise ValueError('Tokenizer changed')
            import llama_cpp
            model=llama_cpp.Llama(model_path=args.tokenizer,vocab_only=True,n_gpu_layers=0,verbose=False)
            count=lambda text:len(model.tokenize(text.encode(),add_bos=False,special=False))
            metadata=dict(kind='existing_local_vocabulary_only',sha256=file_hash(args.tokenizer),model_inference=False)
        print(json.dumps(execute_offline(args.design,args.out,count,metadata)))
    finally:
        if model is not None:model.close()
