"""Run offline fault acceptance and bind a new local proposal. No model calls."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runaway import shared_schema_executor as executor, generation
from runaway.pipeline import write_once


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self.passed = []; self.subcases = 0

    def addSuccess(self, test):
        self.passed.append(test.id()); super().addSuccess(test)

    def addSubTest(self, test, subtest, error):
        self.subcases += 1; super().addSubTest(test, subtest, error)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', required=True)
    args = parser.parse_args(); out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False)
    runtime = executor.runtime_metadata()
    proposal = executor.prepare(out / 'proposed-reader', runtime)
    spec = importlib.util.spec_from_file_location('executor_validation', ROOT / 'tests/test_shared_schema_executor.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    log = io.StringIO(); forbidden_processes = []
    def forbid(*args, **kwargs):
        forbidden_processes.append(True)
        raise AssertionError('Offline acceptance forbids un-intercepted subprocess creation')
    # All allowed CLI paths intercept the bounded transport before subprocess.
    # Runtime metadata above was read before this guard and performs no inference.
    with patch.object(generation.subprocess, 'Popen', side_effect=forbid):
        result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=Result).run(suite)
    write_once(out / 'validation.log', log.getvalue())
    evidence = dict(kind='offline_shared_schema_executor_acceptance',
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    all_checks_passed=result.wasSuccessful() and not forbidden_processes,
                    tests_run=result.testsRun, tests_passed=len(result.passed), test_ids=result.passed,
                    subtests=result.subcases, forbidden_subprocess_attempts=len(forbidden_processes),
                    source_hashes=proposal['source_hashes'], binding_id=proposal['binding_id'],
                    external_model_calls=0, new_token_counts=0,
                    runtime_local_only=runtime,
                    validation_log_sha256=hashlib.sha256(log.getvalue().encode()).hexdigest(),
                    interpretation='Deterministic program records and intercepted CLI only; not model quality or backend reference support.')
    write_once(out / 'offline-acceptance.json', evidence)
    if not evidence['all_checks_passed']:
        raise ValueError('Offline acceptance failed; inspect preserved log. No service entry.')
    final = executor.bind_acceptance(out / 'proposed-reader', evidence)
    executor.preflight(out / 'proposed-reader', require_acceptance=True, check_runtime=True)
    write_once(out / 'approval.template.json', dict(status='not_approved', proposal_id=final['id'],
                calls_max=16, human_source=None,
                note='Template only. Operator must independently verify direct human approval; never fill automatically.'))
    public = {k: v for k, v in evidence.items() if k not in ('runtime_local_only', 'binding_id')}
    public.update(proposal_id=final['id'], binding_id=final['binding_id'],
                  requested_model=executor.MODEL,
                  runtime_versions=dict(python=runtime['python_version'], **{k: v['version'] for k, v in runtime['tools'].items()}),
                  request_ids=[j['request_id'] for stage in executor.STAGES for j in executor.read(out / 'proposed-reader/requests.synthetic.json')[stage]],
                  stage_caps=executor.CAPS, calls_max=16, approved=False, remaining_service_budget=0,
                  source_request_archive_sha256=executor.shared.SOURCE_SHA,
                  previous_archives_unchanged=len(final['old_archives']),
                  service_backend_ref_compatibility='unmeasured', real_person_fidelity_verified=False,
                  native_development_usage='Separate host accounting after natural turn closure; not0.')
    write_once(out / 'public-summary.synthetic.json', public)
    print(json.dumps(dict(status='offline_acceptance_bound', proposal_id=final['id'], tests_passed=len(result.passed),
                          external_model_calls=0, approved=False)))


if __name__ == '__main__':
    main()
