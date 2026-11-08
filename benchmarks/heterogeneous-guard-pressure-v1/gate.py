"""A new exact16grant is necessary; this module supplies no service backend."""
import importlib.util
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pressure_gate_plan', HERE / 'plan.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
SCOPE = 'heterogeneous_guard_pressure_16_v1'


def verify(root, approval=None, verify_human_grant=None):
    if type(approval) is not dict or approval.get('approved') is not True or not callable(verify_human_grant):
        raise PermissionError('New exact16grant and trusted host verification required;zero calls')
    expected = dict(scope=SCOPE, model=p.MODEL, max_new_local_cli_attempts=16,
                    manifest_sha256=p.sha(Path(root) / 'manifest.json'))
    if any(approval.get(k) != v for k, v in expected.items()) or type(approval.get('max_new_local_cli_attempts')) is not int:
        raise PermissionError('Grant scope,model,cap or manifest differs')
    if re.fullmatch('[0-9a-f]{40}', str(approval.get('exact_source_ref', ''))) is None:
        raise PermissionError('Exact published source and successful CI required')
    p.verify(root)
    if verify_human_grant(approval) is not True: raise PermissionError('Trusted host rejected grant')
    return True
