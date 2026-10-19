"""Single-use 6+2+8 reader executor. Default CLI mode is offline preflight.

Injected backends are mocks, never model-quality evidence. Real execution needs
a separately verified human approval of the final proposal ID. A JSON receipt
records that approval; it cannot authenticate a human by itself.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

from . import generation, shared_schema as shared, temporal_determinacy as dual
from .card import canonical, digest
from .execution_ledger import collect, summarize, start_attempt, usage, checked
from .pipeline import write_once
from .taste_executor import FrozenCalls, ORIGINAL_RUN_BOUNDED, Stopped, atomic

ROOT = Path(__file__).resolve().parents[1]
STAGES = shared.STAGES
CAPS = dict(zip(STAGES, (6, 2, 8)))
MODEL = 'gpt-6.1-sol'
TIMEOUT = 180
INPUTS = ('requests.synthetic.json', 'review-scope.original.json', 'lengths.synthetic.json')
SOURCE = 'examples/structural-dual-evidence.synthetic.zip'
BASE = 'examples/shared-schema/'
SCORES = ('strict_choice', 'reported_rule_status', 'completion_choice', 'possible_outcomes')
read = lambda p: shared.parse_wire(Path(p).read_bytes())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
now = lambda: datetime.now(timezone.utc).isoformat()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_names():
    return [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'runaway').glob('*.py'))] + [
        'tests/test_shared_schema_executor.py', 'scripts/verify_shared_schema_executor.py']


def archives():
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / 'examples').glob('*evidence*.zip'))}


def forbidden_ids(source, archive_names):
    ids = {j['request_id'] for stage in STAGES for j in source['design'][stage]}
    for name in archive_names:
        with zipfile.ZipFile(ROOT / name) as z:
            ids.update(Path(n).name.removesuffix('.request.json') for n in z.namelist() if n.endswith('.request.json'))
    return sorted(ids)


def runtime_metadata():
    """Local version lookups only. No login probe, generation or tokenization."""
    tools = {}
    for name in ('node', 'codex'):
        path = shutil.which(name)
        require(path is not None, 'Missing runtime: ' + name)
        tools[name] = dict(executable=str(Path(path).absolute()),
                           version=subprocess.check_output([path, '--version'], text=True, timeout=5).strip())
    require(int(tools['node']['version'].lstrip('v').split('.')[0]) >= 22, 'Node22+ required')
    return dict(python_executable=str(Path(sys.executable).absolute()), python_version=platform.python_version(),
                tools=tools, external_model_calls=0)


def validate_matrix(jobs, source):
    require(set(jobs) == set(STAGES), 'Stage set changed')
    ids = set()
    for stage in STAGES:
        require(len(jobs[stage]) == CAPS[stage], 'Stage cap/order changed')
        for old, job in zip(source['design'][stage], jobs[stage]):
            require(set(job) == {'person_id', 'source_request_id', 'request_id', 'request'}, 'Job metadata changed')
            require(job['person_id'] == old['person_id'] and job['source_request_id'] == old['request_id'], 'Fixed identity/order changed')
            require(job['request'] == shared.hoist(old['request']), 'Exact hoisted request changed')
            require(set(job['request']) == {'system', 'prompt', 'schema'}, 'Request envelope changed')
            require(job['request_id'] == digest(canonical(job['request'])) and job['request_id'] not in ids, 'Duplicate/changed request ID')
            ids.add(job['request_id'])
    require(len(ids) == 16, 'Fixed16matrix changed')


def prepare(destination, runtime=None):
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = shared.load_source(ROOT / SOURCE)
    jobs = read(ROOT / BASE / 'requests.synthetic.json')
    validate_matrix(jobs, source)
    for src, dst in [('requests.synthetic.json', INPUTS[0]), ('review-scope.synthetic.json', INPUTS[1]),
                     ('measurement.synthetic.json', INPUTS[2])]:
        shutil.copyfile(ROOT / BASE / src, root / dst)
    hashes = {n: sha(ROOT / n) for n in source_names()}
    body = dict(kind='single_use_shared_schema_reader_proposal', proposal_directory=str(root),
                calls_max=16, stage_caps=CAPS, stage_order=list(STAGES), model=MODEL,
                timeout_seconds=TIMEOUT, cleanup_waits_seconds=[2, 2],
                runtime=runtime or runtime_metadata(), source_hashes=hashes,
                input_hashes={n: sha(root / n) for n in INPUTS}, old_archives=archives(),
                forbidden_request_ids=forbidden_ids(source, archives()),
                original_scope_id=read(root / INPUTS[1])['id'],
                request_id_policy='Exact three-key canonical request; model and runtime bound separately, not inserted into payload.',
                stages='All6dev exact plus contrasts/order; then2fixed wrong-person exact manipulated gold and lose target contrast; only then8consumed holdout.',
                budget='16new generation ceiling only; no old balance,retry,repair,fallback,resume or purchases. Not an aggregate HTTP/token/money cap.',
                data_scope='Only exact synthetic memory,public queries,SYSTEM/contract and shared schema. Gold/worlds/code/oldanswers/realdata remain local.',
                approval='Separate independently verified direct human approval of final proposal ID required; receipt is bookkeeping,not authentication.',
                compatibility='First planned development read is compatibility probe; no extra call or inline fallback.',
                denominators=dict(development=96, wrong_person=40, holdout=376, historical=0),
                lengths='Existing exact local vocabulary counts only; no new counts,not service usage.',
                limitations='Consumed synthetic structural families3dev/4holdout,14policies; no new model-quality,compressor,realperson,population orcrossprovider claim.')
    binding_id = digest(canonical(body))
    proposal = dict(body, binding_id=binding_id, acceptance=None)
    proposal['id'] = digest(canonical(proposal))
    write_once(root / 'proposal.json', proposal)
    for name in hashes:
        target = root / 'frozen-source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return proposal


def bind_acceptance(root, evidence):
    root = Path(root)
    p, _, _ = preflight(root)
    require(evidence['all_checks_passed'] is True and evidence['external_model_calls'] == 0,
            'Offline acceptance required')
    require(evidence['binding_id'] == p['binding_id'] and evidence['source_hashes'] == p['source_hashes'], 'Acceptance binding mismatch')
    require(p['acceptance'] is None and not (root / 'execution-intent.json').exists(), 'Already bound/claimed proposal')
    write_once(root / 'executor-acceptance.json', evidence)
    p['acceptance'] = dict(path='executor-acceptance.json', sha256=sha(root / 'executor-acceptance.json'))
    p['id'] = digest(canonical({k: v for k, v in p.items() if k != 'id'}))
    atomic(root / 'proposal.json', p)
    return p


def preflight(root, require_acceptance=False, check_runtime=False):
    require(not sys.flags.optimize, 'Optimized Python unsupported')
    root = Path(root).resolve()
    require(not (root / 'proposal.json').is_symlink(), 'Symlink proposal')
    p = read(root / 'proposal.json')
    require(p['id'] == digest(canonical({k: v for k, v in p.items() if k != 'id'})), 'Proposal hash changed')
    body = {k: v for k, v in p.items() if k not in ('id', 'binding_id', 'acceptance')}
    require(p['binding_id'] == digest(canonical(body)), 'Binding hash changed')
    require(p['proposal_directory'] == str(root), 'Copied/moved proposal forbidden')
    require(p['calls_max'] == 16 and p['stage_caps'] == CAPS and p['stage_order'] == list(STAGES)
            and p['model'] == MODEL and p['timeout_seconds'] == TIMEOUT and p['cleanup_waits_seconds'] == [2, 2]
            and p['denominators'] == dict(development=96, wrong_person=40, holdout=376, historical=0), 'Execution policy changed')
    require(set(p['source_hashes']) == set(source_names()), 'Source set changed')
    for name, expected in p['source_hashes'].items():
        for path in (ROOT / name, root / 'frozen-source' / name):
            require(not path.is_symlink() and sha(path) == expected, 'Frozen source changed: ' + name)
    require(set(p['input_hashes']) == set(INPUTS), 'Input set changed')
    for name, expected in p['input_hashes'].items():
        require(not (root / name).is_symlink() and sha(root / name) == expected, 'Frozen input changed: ' + name)
    for local, public in zip(INPUTS, ('requests.synthetic.json', 'review-scope.synthetic.json', 'measurement.synthetic.json')):
        require(sha(root / local) == sha(ROOT / BASE / public), 'Published input changed')
    require(p['old_archives'] == archives(), 'Prior archive set/hash changed')
    source = shared.load_source(ROOT / SOURCE)
    require(p['forbidden_request_ids'] == forbidden_ids(source, p['old_archives']), 'Old request exclusion changed')
    jobs = read(root / INPUTS[0])
    validate_matrix(jobs, source)
    require(not {j['request_id'] for s in STAGES for j in jobs[s]}.intersection(p['forbidden_request_ids']), 'Old request forbidden')
    scope = read(root / INPUTS[1])
    require(scope['id'] == digest(canonical({k: v for k, v in scope.items() if k != 'id'})) == p['original_scope_id'], 'Original scope changed')
    if p['acceptance'] is not None:
        info = p['acceptance']; path = root / 'executor-acceptance.json'
        require(info['path'] == path.name and not path.is_symlink() and sha(path) == info['sha256'], 'Acceptance evidence changed')
        e = read(path)
        require(e['binding_id'] == p['binding_id'] and e['source_hashes'] == p['source_hashes']
                and e['all_checks_passed'] is True and e['external_model_calls'] == 0, 'Invalid offline acceptance')
    if require_acceptance:
        require(p['acceptance'] is not None, 'Bound offline acceptance required')
    if check_runtime:
        require(runtime_metadata() == p['runtime'], 'Local runtime drifted')
    return p, source, jobs


def selected_world(source, split, ids=None):
    world = source['worlds'][split]
    return dict(world, people=[p for p in world['people'] if ids is None or p['id'] in ids])


def score(source, split, rows, ids=None):
    world = selected_world(source, split, ids)
    gold = {p['id']: source['expected'][split][p['id']] for p in world['people']}
    return dual.score_records(world, rows, gold, tasks=('current_choice', 'joint'))


def complete_gate(scores):
    checks = {k: scores[k]['joint']['planned'] > 0 and scores[k]['joint']['correct'] == scores[k]['joint']['planned'] for k in SCORES}
    for k in ('strict_choice', 'completion_choice'):
        s = scores[k]['joint']
        c = s['matched_domain_contrasts']; o = s['current_scenarios_option_orders_collapsed']
        checks[k + '_contrasts'] = c['planned'] > 0 and c['correct'] == c['planned']
        checks[k + '_option_consistency'] = o['planned'] > 0 and o['consistent'] == o['planned']
    return dict(passed=all(checks.values()), checks=checks)


def wrong_gate(source, jobs, rows):
    ids = [j['person_id'] for j in jobs]
    expected = {pid: source['records']['development']['wrong_person'][pid] for pid in ids}
    scored = score(source, 'development', rows, ids)
    checks = dict(exact_original_manipulated_reference=rows == expected)
    for k in ('strict_choice', 'completion_choice'):
        c = scored[k]['joint']['matched_domain_contrasts']
        checks[k + '_loses_original_target_contrast'] = c['planned'] == 1 and c['correct'] == 0
    return dict(passed=all(checks.values()), checks=checks, target_scores=scored)


def records_checked(out):
    """Retain raw provenance, but never total contradictory token metadata."""
    records = collect(out)
    for row in records:
        counts = row['usage']
        if counts is not None and (counts['cached_input_tokens'] > counts['input_tokens']
                                   or counts['reasoning_output_tokens'] > counts['output_tokens']):
            row['usage'] = None
            row['usage_rejection'] = 'contradictory_input_cache_or_output_reasoning'
        for artifact in row['artifacts']:
            path = Path(out) / artifact['path']
            if path.name.endswith('.failure.json'):
                failure = checked(path)
                if 'raw_bytes_sha256' in failure:
                    raw = path.with_name(row['request_id'] + '.raw.bin')
                    require(not raw.is_symlink() and raw.stat().st_size == failure['raw_bytes_length']
                            and sha(raw) == failure['raw_bytes_sha256'], 'Rejected raw bytes changed')
    return records


class Calls:
    def __init__(self, out, proposal, backend, guard):
        self.out = out; (out / 'calls').mkdir()
        self.p = proposal; self.backend = backend; self.guard = guard
        self.config = {'models': {'reader': MODEL}}
        self.cli = shutil.which('codex'); self.trace = None; self.current_job = None
        self.counts = Counter(); self.stopped = False; self.reason = None
        self.current = None; self.diagnostics = []
        self.update()

    def update(self):
        self.ledger = summarize(records_checked(self.out))
        atomic(self.out / 'status.json', dict(updated_at=now(), stage_attempts=dict(self.counts),
               current=self.current, stopped=self.stopped, stop_reason=self.reason, cap=16, ledger=self.ledger))

    def stop(self, kind, **details):
        self.stopped = True; self.reason = dict(kind=kind, **details); self.current = None
        try:
            self.update()
        except Exception:
            self.ledger = dict(integrity_uncertain=True, known_usage=None, execution_records=None)
            atomic(self.out / 'status.json', dict(stopped=True, stop_reason=self.reason, ledger=self.ledger))

    def observed_runner(self, args, prompt, timeout):
        """Bind exact transport arguments and bytes before unchanged observer."""
        try:
            self.verify_transport(args, prompt, timeout)
        except Exception:
            raise Stopped('Transport rejected locally before backend') from None
        return FrozenCalls.observed_runner(self, args, prompt, timeout)

    def verify_transport(self, args, prompt, timeout):
        self.guard()
        request = self.current_job['request']
        require(timeout == TIMEOUT and prompt == request['prompt'], 'Prompt/deadline changed')
        directory = Path(args[args.index('-C') + 1])
        require({p.name for p in directory.iterdir()} == {'system.txt', 'schema.json'}, 'Unexpected working files')
        require(all(p.is_file() and not p.is_symlink() for p in directory.iterdir()), 'Unsafe working metadata')
        require((directory / 'system.txt').read_text() == request['system'] and read(directory / 'schema.json') == request['schema'], 'System/schema bytes changed')
        expected = [self.cli, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '--json', '-C', str(directory), '-m', MODEL,
                    '--output-schema', str(directory / 'schema.json'), '--enable', 'skip_host_skill_discovery']
        configs = {'model_instructions_file': str(directory / 'system.txt'), 'project_doc_max_bytes': 0,
                   'memories.use_memories': False, 'memories.generate_memories': False,
                   'web_search': 'disabled', 'approval_policy': 'never', 'mcp_servers': {}}
        for k, v in configs.items():
            expected += ['-c', k + '=' + ('{}' if v == {} else json.dumps(v))]
        for name in ('shell_tool', 'shell_snapshot', 'multi_agent', 'multi_agent_v2', 'apps', 'plugins', 'hooks', 'browser_use', 'computer_use', 'image_generation', 'view_image', 'memories', 'skill_search'):
            expected += ['--disable', name]
        expected += ['-']
        require(args == expected, 'Transport argument set/order changed')

    def call(self, stage, job):
        require(not self.stopped, 'Batch already stopped')
        self.guard()
        records = records_checked(self.out)
        require(all(r['outcome'] == 'completed' and r['usage'] is not None for r in records), 'Uncertain prior invocation/usage')
        require(stage in CAPS and len(records) < 16 and self.counts[stage] < CAPS[stage], 'Call budget reached')
        require(self.counts[stage] == len([r for r in records if r['request_id'] in {j['request_id'] for j in self.jobs[stage]}]), 'Stage count drift')
        expected = [(s, j) for s in STAGES for j in self.jobs[s]][len(records)]
        require((stage, job) == expected, 'Fixed request order changed')
        key = job['request_id']; request = job['request']
        require(key == digest(canonical(request)) and key not in self.p['forbidden_request_ids'], 'Request identity forbidden/changed')
        path = self.out / 'calls' / key
        require(not any(self.out.joinpath('calls').glob(key + '.*')), 'Existing attempt/response; no reuse')
        write_once(path.with_suffix('.request.json'), request)
        attempt = start_attempt(path.with_suffix('.attempt.json'), key)
        self.counts[stage] += 1
        self.current = dict(stage=stage, request_id=key, execution_id=attempt['execution_id'])
        self.current_job = job; self.trace = None; provenance = None; raw = None
        split = 'holdout' if stage == 'holdout_jobs' else 'development'
        self.update()
        try:
            self.guard()
            pending = collect(self.out)
            require(len(pending) == len(records) + 1 and sum(r['outcome'] == 'unresolved_invocation_intent' for r in pending) == 1, 'Intent integrity changed')
            raw, provenance = self.backend(request['prompt'], MODEL, timeout=TIMEOUT, schema=request['schema'], system=request['system'])
            self.guard()
            counts = usage(provenance)
            require(counts is not None, 'Unknown/malformed usage')
            require(counts['cached_input_tokens'] <= counts['input_tokens']
                    and counts['reasoning_output_tokens'] <= counts['output_tokens'], 'Contradictory usage')
            require(provenance.get('backend') == 'codex' and provenance.get('model_requested') == MODEL
                    and provenance.get('cli_version') == self.p['runtime']['tools']['codex']['version'], 'Backend/model/runtime identity changed')
            value = shared.parse_wire(raw)
            require(shared.accepts(value, request['schema']), 'Invalid/incomplete wire output')
            # Existing semantics rejects duplicate/unsorted or contradictory outcomes.
            score(self.source, split, {job['person_id']: value['answers']})
            result = dict(answer=value, raw=raw.decode('utf-8') if isinstance(raw, bytes) else raw,
                          provenance=provenance, request_id=key, execution_id=attempt['execution_id'])
            result['sha256'] = digest(canonical(result)); write_once(path.with_suffix('.response.json'), result)
        except Exception as exc:
            provenance = provenance or getattr(exc, 'provenance', None) or self.trace or {}
            # Preserve exact rejected bytes, never substitute a repaired answer.
            raw_info = {}
            if isinstance(raw, (str, bytes)):
                raw_bytes = raw if isinstance(raw, bytes) else raw.encode('utf-8')
                with path.with_suffix('.raw.bin').open('xb') as stream:
                    stream.write(raw_bytes)
                raw_info = dict(raw_bytes_sha256=hashlib.sha256(raw_bytes).hexdigest(), raw_bytes_length=len(raw_bytes))
            elif raw is not None:
                raw_info = dict(non_wire_value_type=type(raw).__name__)
            if raw is not None:
                try:
                    parsed = shared.parse_wire(raw)
                    require(set(parsed) == {'answers'}, 'Wrong diagnostic envelope')
                    diagnostic = score(self.source, split, {job['person_id']: parsed['answers']})
                    self.diagnostics.append(dict(request_id=key, diagnostic=dict(status='scored_raw_not_accepted',
                        sha256=shared.score_fingerprint(diagnostic),
                        fields={k: {n: diagnostic[k]['joint'][n] for n in ('correct', 'planned', 'missing', 'invalid_answers') if n in diagnostic[k]['joint']} for k in SCORES})))
                except Exception:
                    self.diagnostics.append(dict(request_id=key, diagnostic=dict(status='unparseable')))
            failed = dict(error_type=type(exc).__name__, request_id=key, execution_id=attempt['execution_id'], provenance=provenance, **raw_info)
            if getattr(exc, 'backend_invoked', True) is False:
                failed['backend_invoked'] = False
            failed['sha256'] = digest(canonical(failed)); write_once(path.with_suffix('.failure.json'), failed)
            self.stop('call_or_output_failure', stage=stage, error_type=type(exc).__name__)
            raise
        self.current = None; self.update()
        require(self.ledger['executions_missing_usage'] == 0, 'Usage accounting uncertain')
        return value['answers']


def claim(root, out, p, approval, real):
    require(not out.exists(), 'Existing output cannot be resumed')
    require(not out.is_relative_to(root) and not root.is_relative_to(out), 'Output/proposal trees must be separate')
    fd = os.open(root / 'execution-intent.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(dict(proposal_id=p['id'], output=str(out), at=now(),
                       backend_kind='actual_service' if real else 'mock_not_model_quality',
                       human_source=approval.get('human_source') if approval else None,
                       meaning='Single-use invocation intent; crash does not permit retry/resume.'), stream)


def execute(root, out, backend=None, approval=None):
    root = Path(root).resolve(); out = Path(out).resolve(); real = backend is None
    p, source, jobs = preflight(root, require_acceptance=real, check_runtime=real)
    if real:
        require(approval and approval.get('status') == 'approved' and approval.get('proposal_id') == p['id']
                and approval.get('calls_max') == 16 and approval.get('human_source'), 'Separate direct human approval required')
        require(generation.run_bounded is ORIGINAL_RUN_BOUNDED, 'Transport already replaced')
        backend = generation.codex_generate
    claim(root, out, p, approval, real)
    out.mkdir(parents=True, exist_ok=False)
    def guard():
        current, _, _ = preflight(root, require_acceptance=real)
        require(current['id'] == p['id'], 'Proposal identity changed during execution')
        intent = read(root / 'execution-intent.json')
        require(intent['proposal_id'] == p['id'] and intent['output'] == str(out), 'Execution claim changed')
    calls = Calls(out, p, backend, guard); calls.jobs = jobs; calls.source = source
    answers = {s: {} for s in STAGES}; gates = {}; completed = False
    original_runner = generation.run_bounded
    generation.run_bounded = calls.observed_runner
    try:
        for stage in STAGES:
            if stage == 'holdout_jobs':
                atomic(out / 'holdout-entry.json', dict(gates=gates, proposal_id=p['id'], observed_at=now()))
            for job in jobs[stage]:
                answers[stage][job['person_id']] = calls.call(stage, job)
                atomic(out / 'answers.json', answers)
            if stage == 'development_jobs':
                gates[stage] = complete_gate(score(source, 'development', answers[stage]))
            elif stage == 'wrong_person_jobs':
                gates[stage] = wrong_gate(source, jobs[stage], answers[stage])
            if stage in gates:
                atomic(out / 'gates.json', gates)
                if not gates[stage]['passed']:
                    calls.stop('reader_gate_failed', stage=stage); break
        else:
            completed = True
    except Exception as exc:
        if not calls.stopped:
            calls.stop('local_or_checkpoint_failure', error_type=type(exc).__name__)
    finally:
        generation.run_bounded = original_runner
    # Unconditional planned denominators, including entirely unreached stages.
    scores = {s: score(source, 'holdout' if s == 'holdout_jobs' else 'development', answers[s],
                       [j['person_id'] for j in jobs[s]] if s == 'wrong_person_jobs' else None) for s in STAGES}
    family_scores = {}
    for family in sorted({person['family'] for person in source['worlds']['holdout']['people']}):
        ids = [person['id'] for person in source['worlds']['holdout']['people'] if person['family'] == family]
        family_scores[family] = score(source, 'holdout', {pid: rows for pid, rows in answers['holdout_jobs'].items() if pid in ids}, ids)
    report = dict(status='complete' if completed and not calls.stopped else 'stopped', proposal_id=p['id'],
                  binding_id=p['binding_id'], backend_kind='actual_service' if real else 'mock_not_model_quality',
                  gates=gates, scores=scores, consumed_holdout_families=family_scores,
                  calls=calls.ledger, stage_attempts=dict(calls.counts), stop_reason=calls.reason,
                  rejected_output_diagnostics=calls.diagnostics,
                  external_model_calls=calls.ledger.get('execution_records') if real else 0,
                  mock_invocations=calls.ledger.get('execution_records') if not real else 0,
                  historical=dict(planned=0, status='not_measured'),
                  interpretation='All planned denominators retained. Rejected wire is not accepted prediction; separate raw diagnostics do not repair it. Mock scores are program fixtures,not model evidence. Consumed structural families,not fresh holdout.')
    if not (out / 'answers.json').exists():
        write_once(out / 'answers.json', answers)
    write_once(out / 'report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proposal', required=True); parser.add_argument('--run', action='store_true')
    parser.add_argument('--approval'); parser.add_argument('--out'); args = parser.parse_args()
    if args.run:
        if not args.approval or not args.out:
            parser.error('--run requires --approval and --out')
        report = execute(args.proposal, args.out, approval=read(args.approval))
        print(json.dumps(dict(status=report['status'], calls=report['calls'].get('execution_records'))))
    else:
        p, _, _ = preflight(args.proposal, require_acceptance=True, check_runtime=True)
        print(json.dumps(dict(preflight='passed', proposal_id=p['id'], calls_max=16, external_model_calls=0)))


if __name__ == '__main__':
    main()
