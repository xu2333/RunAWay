"""Fail-closed grant validation; no service or credential handling.

The trusted host must verify the literal user grant, source/CI pin, one-use
execution intent, runtime and cumulative counters. This helper never accepts
a preparation flag or a previous scope as authority.
"""
import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('direct768_gate_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
SCOPE = 'fresh_direct768_54_v1'


def verify(root, approval=None, verify_human_grant=None):
    if type(approval) is not dict or approval.get('approved') is not True or not callable(verify_human_grant):
        raise PermissionError('A new exact human54grant and trusted host verification are required; zero calls')
    expected = dict(scope=SCOPE, model=p.MODEL, max_new_local_cli_attempts=54,
                    manifest_sha256=p.sha(Path(root) / 'manifest.json'))
    if any(approval.get(k) != v for k, v in expected.items()) or type(approval.get('max_new_local_cli_attempts')) is not int:
        raise PermissionError('Grant scope, model, cap or manifest differs')
    if re.fullmatch('[0-9a-f]{40}', str(approval.get('exact_source_ref', ''))) is None:
        raise PermissionError('An exact published source and CI pin are required')
    p.verify(root)
    if verify_human_grant(approval) is not True:
        raise PermissionError('Trusted host did not verify the new grant and execution conditions')
    return True


if __name__ == '__main__':
    raise SystemExit('No approved host is attached. Preparation is not execution authority; zero model calls.')
