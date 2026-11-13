"""No real invocation without an exact fresh eight-attempt grant."""
import importlib.util
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('domain_readonly_gate_plan',HERE/'plan.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
SCOPE='domain_template_readonly8_v1'


def verify(root,approval=None,verify_human_grant=None):
    if type(approval)is not dict or approval.get('approved')is not True or not callable(verify_human_grant):
        raise PermissionError('New exact eight-attempt grant and trusted verifier required')
    expected=dict(scope=SCOPE,model=p.MODEL,max_new_local_cli_attempts=8,manifest_sha256=p.sha(Path(root)/'manifest.json'))
    if any(approval.get(k)!=v for k,v in expected.items())or type(approval.get('max_new_local_cli_attempts'))is not int:
        raise PermissionError('Grant scope,model,cap or manifest differs')
    if re.fullmatch('[0-9a-f]{40}',str(approval.get('exact_source_ref','')))is None:raise PermissionError('Exact source and CI pin required')
    p.verify(root)
    if verify_human_grant(approval)is not True:raise PermissionError('Trusted host did not verify grant')
    return True
