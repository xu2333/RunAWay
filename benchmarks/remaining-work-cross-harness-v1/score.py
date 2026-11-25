"""Validate the qualitative ratings and recount matched pairs, offline."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ('old', 'new')
TIMING_CASES = {'greenhouse', 'listening', 'puzzle', 'caption'}

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def aggregate(root):
    spec = load(root/'protocol.json')
    cases = {c['id']:c for c in spec['cases']}
    raw = load(root/'observations.json')
    records = {r['slot']:r for r in raw}
    assert len(records) == len(raw) == 54
    assert set(records) == {c['slot'] for c in spec['slots']}
    stopped = set()
    for slot in spec['slots']:
        r = records[slot['slot']]
        if slot['client'] in stopped:
            assert r.get('missing') == 'not attempted after client failure'
        elif r.get('missing'):
            assert r['missing'] == 'client failure'
            stopped.add(slot['client'])
    for row in raw:
        assert row['slot'] == '-'.join([row['client'],row['case'],row['arm']])
        if row.get('missing'):
            assert row['strict_pass'] is False and 'answer' not in row
            continue
        answer = row['answer']
        assert sha256(answer.encode()).hexdigest() == row['answer_sha256']
        assert len(row['clauses']) == len(cases[row['case']]['assess_separately'])
        for clause in row['clauses']:
            assert clause['mark'] in ('pass','contradicted','partial_or_omitted')
            assert clause['quotes'] and all(q and q in answer for q in clause['quotes'])
        assert row['local_project_redacted'] == (row['answer_sha256'] != row['original_answer_sha256'])
        assert row['task_answer'] == (row['genuine'] != 'unassessable')
        assert row['genuine'] in ('intact','weakened','removed','unassessable')
        assert row['next_action_usable'] in ('yes','partial','no')
        assert not row['scheduling_gate'] or row['extra_gate']
        assert bool(row['thread_bindings']) == (row['case']=='thread')
        if row['thread_bindings']:
            assert set(row['thread_bindings']) == {'issuer','material'}
            assert all(type(v) is bool for v in row['thread_bindings'].values())
        if row['case'] == 'type':
            assert row['sample_storage'] in {'explicit_unknown','instruction_only_or_silent','asserted_done','asserted_undone_or_redo','inconsistent'}
            assert type(row['known_print_progress']) is bool and type(row['release_and_signatures']) is bool
            assert (row['sample_storage']=='explicit_unknown') == (row['clauses'][3]['mark']=='pass')
        else:
            assert all(row[k] is None for k in ('sample_storage','known_print_progress','release_and_signatures'))
        assert row['strict_pass'] == (all(c['mark']=='pass' for c in row['clauses'])
            and row['genuine']=='intact' and not any(row[k] for k in
            ('extra_gate','scheduling_gate','forced_immediacy','material_conflict')))
    def record(client,case,arm):
        return records['-'.join([client,case,arm])]
    result = {}
    for arm in ARMS:
        group = [r for r in raw if r['arm']==arm]
        present = [r for r in group if not r.get('missing')]
        focus = [r['thread_bindings'] for r in present if r['case']=='thread']
        specimens = [r for r in present if r['case']=='type']
        result[arm] = dict(
            storage=dict(Counter(r['sample_storage'] for r in specimens)),
            known_progress=sum(r['known_print_progress'] for r in specimens),
            original_release=sum(r['release_and_signatures'] for r in specimens),
            joint=sum(r['sample_storage']=='explicit_unknown' and r['known_print_progress'] and r['release_and_signatures'] for r in specimens),
            first_reel_backup=sum(r['clauses'][0]['mark']=='pass' for r in present if r['case']=='reels'),
            downgrades=[r['slot'] for r in present if r['unsupported_downgrade']],
            redo=[r['slot'] for r in present if r['unconditional_redo']],
            no_handoff=[r['slot'] for r in present if not r['task_answer']],
            timing_assessable=sum(r['task_answer'] for r in present if r['case'] in TIMING_CASES),
            returns=len(present), missing=len(group)-len(present),
            both=sum(all(b.values()) for b in focus),
            issuer=sum(b['issuer'] for b in focus), material=sum(b['material'] for b in focus),
            waiting_on_time=sum(r['scheduling_gate'] for r in present if r['case'] in TIMING_CASES),
            extra_gates=sum(bool(r['extra_gate']) for r in present),
            immediate=sum(r['forced_immediacy'] for r in present),
            genuine=dict(Counter(r['genuine'] for r in present)),
            strict={cl:sum(r['strict_pass'] for r in group if r['client']==cl) for cl in spec['clients']},
            all_three=[c for c in cases if all(record(cl,c,arm)['strict_pass'] for cl in spec['clients'])])
    # Each pair is one client and one card, even when several facets are checked.
    for arm in ARMS:
        focal = {}
        for client in spec['clients']:
            fold = record(client, 'foldout', arm)
            thread = record(client, 'thread', arm)
            specimen = record(client, 'type', arm)
            checks = {}
            for name, row, fields in (
                ('remaining_work', fold, ('first_three_secured', 'two_remaining', 'can_continue_with_material')),
                ('scoped_release', thread, ('authorized_threading', 'restricted_punching', 'no_global_hold')),
            ):
                checks[name] = False
                if row.get('missing'):
                    continue
                for key in fields:
                    facet = row['focus'][key]
                    assert facet['mark'] in ('pass','partial_or_omitted','contradicted')
                    assert facet['quotes'] and all(q and q in row['answer'] for q in facet['quotes'])
                checks[name] = all(row['focus'][key]['mark']=='pass' for key in fields)
            checks['specimen'] = (not specimen.get('missing') and
                specimen['sample_storage']=='explicit_unknown' and
                specimen['known_print_progress'] and specimen['release_and_signatures'])
            checks['joint'] = all(checks.values())
            focal[client] = checks
        result[arm]['focal_by_client'] = focal
    pairs=Counter()
    gates=Counter()
    for cl in spec['clients']:
        for case in cases:
            a,b=(record(cl,case,arm) for arm in ARMS)
            state='missing' if a.get('missing') or b.get('missing') else f"{int(a['strict_pass'])} to {int(b['strict_pass'])}"
            pairs[state]+=1
            gate_state='missing' if state=='missing' else f"{int(bool(a['extra_gate']))} to {int(bool(b['extra_gate']))}"
            gates[gate_state]+=1
    result['pairs']=dict(pairs)
    result['gate_pairs']=dict(gates)
    former=load(root.parent/'completion-evidence-cross-harness-v1/observations.json')
    sentinels=[r for r in former if r['arm']=='new' and r['strict_pass']]
    assert len(sentinels)==20
    result['previous_20']={arm:[r['slot'].rsplit('-',1)[0] for r in sentinels if record(r['client'],r['case'],arm)['strict_pass']] for arm in ARMS}
    return result

if __name__ == '__main__':
    print(json.dumps(aggregate(HERE),indent=2))
