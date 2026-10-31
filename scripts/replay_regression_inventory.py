"""Reproduce232source-bound observations; never turn coverage into a pass."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'benchmarks/regression-inventory-v1'
METHOD_SHA = 'a60978565bf8a726eccb4969ac025c6d08aad10a706066d7f8d7d68bae0cb4dc'
LOCK_SHA = '8d889df935b54b3630d3c9356d42f2fb2499b7e1f37a03713d7fa037a87643b2'
COVERAGE_SHA = '07e1a9396a7fdbf251e5f7f27d5f3af343e34a454c3fcc093e8f6e82b1ca1a6a'
REQUIREMENTS_VALUE_SHA = 'd0acc1108a205889b8d0d55b9caecfed8a16c6071b77835a77a396567bef9047'
OBSERVATIONS_VALUE_SHA = '693699212508d172c21c9d348e15ba61da67d068b65550a5b02e011ff49ee38a'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


old = load('inventory_old_archive', ROOT / 'benchmarks/regression-progress-v1/check.py')
world = load('inventory_world_archive', ROOT / 'scripts/replay_remaining_world_frontier.py')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha_bytes(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def replay(data):
    require(data['kind'] == 'actual_source_bound_inventory_completion_not_regression_pass', 'Wrong inventory')
    require(data['all_sources_fictional'] is True, 'Fiction boundary differs')
    for key in ('independent_semantic_acceptance', 'new_service_authority', 'project_endpoint_proved', 'private_transport_envelope_bytes_published'):
        require(data[key] is False, 'Unsupported inventory claim')
    require(data['method_source_sha256'] == sha_bytes(data['method_source_utf8']) == METHOD_SHA, 'Original method bytes differ')
    require(data['method_lock_sha256'] == LOCK_SHA, 'Method lock differs')
    require(old.digest(data['requirements']) == REQUIREMENTS_VALUE_SHA, 'Original232case requirements differ')
    require(old.digest(data['observations']) == OBSERVATIONS_VALUE_SHA, 'First chronological observations differ')
    # Parse archival code as data; never execute code supplied by a JSON file.
    original_tree = ast.parse(data['method_source_utf8'])
    published_tree = ast.parse((ROOT / 'benchmarks/regression-progress-v1/prototype/policy_scope.py').read_text())
    def functions(tree):
        return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
    def literals(tree):
        return {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ('REVISION', 'RULES')}
    require(functions(original_tree) == functions(published_tree) and literals(original_tree) == literals(published_tree), 'Published method differs from archived method')
    require(hashlib.sha256((HERE / 'coverage.py').read_bytes()).hexdigest() == data['coverage_function_sha256'] == COVERAGE_SHA, 'Frozen assessor differs')
    assessor = load('inventory_frozen_assessor', HERE / 'coverage.py')
    old.check()
    world.check()
    studies = old.read(ROOT / 'benchmarks/regression-progress-v1/observed.synthetic.json')['studies']
    new = world.engine.plan.read(world.DEFAULT)
    expected_people = {'h17', 'h42', 'h68', 'h93', 'j16', 'j62', 'j85'}
    require(set(data['contexts']) == expected_people, 'Context people differ')
    verified = {}
    for pid, context in data['contexts'].items():
        if pid.startswith('h'):
            study_id = 'h17' if pid == 'h17' else 'remaining_h'
            study = studies[study_id]
            records = [r for r in study['records'] if r['person'] == pid]
            er = next(r for r in records if r['group'] == 'extract')
            rr = min([r for r in records if r['group'].startswith('candidate') and r['state'] == 'completed'], key=lambda r: r['slot'])
            source, queries = study['sources'][pid], study['queries']
        else:
            study_id = 'remaining_world_frontier'
            records = [r for r in new['records'] if r['profile'] == pid]
            reads = [r for r in records if r['kind'] == 'read' and r['budget'] == 1536 and r['state'] == 'completed']
            rr = min(reads, key=lambda r: r['slot'])
            er = next(r for r in records if r['kind'] == 'extract' and world.engine.plan.parent(r) == world.engine.plan.parent(rr))
            source, queries = new['sources'][pid], new['queries']['j']
        require(context['study_id'] == study_id and context['extraction_execution_id'] == er['execution_id']
                and context['reading_execution_id'] == rr['execution_id'], 'First chronological observation differs')
        require(sha_bytes(context['source_file_utf8']) == context['source_file_sha256'], 'Original source bytes differ')
        require(json.loads(context['source_file_utf8']) == source, 'Source JSON value differs')
        require(sha_bytes(context['artifact_file_utf8']) == context['artifact_file_sha256'], 'Original artifact bytes differ')
        artifact = json.loads(context['artifact_file_utf8'])
        answer = old.parse_answer(er['raw'])
        prompt = old.policy.bind(answer, source, 1536)['prompt.md']
        require(artifact['prompt'] == prompt and artifact['characters'] == len(prompt) <= 1536, 'Bound prompt differs')
        require(artifact['source_sha256'] == old.digest(source), 'Artifact source differs')
        require(artifact.get('extraction_answer_sha256', artifact.get('answer_sha256')) == old.digest(answer), 'Artifact extraction differs')
        expected_extract = {'model': old.MODEL, 'system': old.grouped.SYSTEM, **old.policy.make_request(source, 1536)}
        require(er['request'] == expected_extract and old.digest(expected_extract) == er['request_sha256'], 'Locked extraction request differs')
        if pid.startswith('h'):
            expected_read = old.request(study, rr['group'], pid, {pid: artifact})
        else:
            expected_read = world.engine.plan.request(world.engine.plan.slots()[rr['slot']-1], {world.engine.plan.parent(er): answer})
            require(er['card'] == artifact, 'New artifact differs')
        require(rr['request'] == expected_read and old.digest(expected_read) == rr['request_sha256'], 'Actual card reader differs')
        require(rr['original_response_envelope_sha256'] == context['original_read_response_envelope_sha256'], 'Native envelope provenance differs')
        read_answer = old.parse_answer(rr['raw'])
        old.choice_reader.decode_response(queries, read_answer, answer_format='text', reader_mode='standard')
        verified[pid] = (context, er, rr, read_answer, {q['id']: q for q in queries})
    requirements = data['requirements']
    require(len(requirements) == 232 and {r['profile'] for r in requirements} == expected_people, 'Required inventory differs')
    for case in requirements:
        require(case['method_sha256'] == METHOD_SHA and case['method_lock_sha256'] == LOCK_SHA, 'Required method differs')
        context, er, rr, answer, queries = verified[case['profile']]
        require(case['source_sha256'] == context['source_file_sha256'], 'Required source differs')
        require(case['extraction_request_sha256'] == er['request_sha256'], 'Required request differs')
        require(case['query_pair_sha256'] == old.digest([queries[q] for q in case['query_ids']]), 'Both frozen option orders differ')
    def verifier(row, case):
        context, er, rr, answer, queries = verified[case['profile']]
        return (row['producer_artifact_sha256'] == context['artifact_file_sha256']
                and row['read_raw_response_sha256'] == context['original_read_response_envelope_sha256']
                and row['evidence_id'] == rr['execution_id']+':'+case['case_id']
                and all(q in answer for q in case['query_ids']))
    result = assessor.assess(requirements, data['observations'], verifier)
    require(result == data['assessment'], 'Recorded coverage assessment differs')
    require(result['structurally_bound_observed_cases'] == 232 and not result['rejected_observations'], 'Missing or rejected bindings')
    require(len(result['disputed_cases_retained']) == 3, 'Disputed cases lost')
    return {**result, 'new_model_calls': 0, 'independent_semantic_acceptance': False,
            'private_envelope_hashes_are_provenance_not_reconstructed_bytes': True}


def check():
    path = HERE / 'observed.synthetic.json'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == (HERE / 'observed.synthetic.sha256').read_text().strip(), 'Inventory checksum differs')
    return replay(old.read(path))


if __name__ == '__main__':
    print(json.dumps(check(), ensure_ascii=False, indent=2))
