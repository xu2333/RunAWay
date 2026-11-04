"""Unmeasured source-ID enum request constraint; original binder unchanged."""
import copy,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
LOCATOR=HERE/'locator.private.json'
ROOT=Path(json.loads(LOCATOR.read_text())['repository_root'])if LOCATOR.exists()else HERE.parents[1]
spec=importlib.util.spec_from_file_location('source_id_enum_original',ROOT/'benchmarks/source-id-review-v1/reviewer.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
VERSION,SCHEMA,bind,legacy=base.VERSION,base.SCHEMA,base.bind,base.legacy
METHOD_ID='source-id-enum-v1'

def _restrict(schema,ids):
 if isinstance(schema,list):return [_restrict(v,ids)for v in schema]
 if not isinstance(schema,dict):return copy.deepcopy(schema)
 result={k:_restrict(v,ids)for k,v in schema.items()}
 if schema.get('type')=='object'and set(schema.get('properties',{}))=={'source_id'}:
  result['properties']['source_id']['enum']=list(ids)
 return result

def make_request(sources,draft,budget=1536):
 request=base.make_request(sources,draft,budget)
 ids=[source['id']for source in sources['sources']]
 request['schema']=_restrict(request['schema'],ids)
 return request
