"""Reproduce eight offline size/ordered-projection checks, not model fidelity."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('common_factor_offline_codec',HERE/'codec.py')
codec=importlib.util.module_from_spec(spec);spec.loader.exec_module(codec)
SOURCE=ROOT/'benchmarks/source-id-initial-encoding-v1/measured.synthetic.json'


def build():
    raw=SOURCE.read_bytes();fingerprint=hashlib.sha256(raw).hexdigest()
    if fingerprint!=SOURCE.with_suffix('.sha256').read_text().strip():raise ValueError('Inherited evidence differs')
    data=json.loads(raw)
    if data['all_sources_fictional']is not True or data['scientific_source_ref']!='8f5aa0a9440628284b4ba0e9bd9f1f434fa2a1c9':raise ValueError('Only the fixed fictional parents are permitted')
    rows=[]
    for rec in data['records']:
        if rec['kind']!='extract':continue
        if rec['state']!='completed'or rec['artifact']is None:raise ValueError('Fixed valid parent missing')
        result=codec.factor(rec['artifact']['prompt'],768)
        rows.append(dict(person=rec['profile'],method=rec['method'],generation=rec['generation'],parent_slot=rec['slot'],**result))
    if len(rows)!=8:raise ValueError('Exact inherited parent set differs')
    return dict(kind='offline_common_condition_factor_not_model_measurement',source_evidence_sha256=fingerprint,
                cards=rows,all_fit_whole768=True,original_min_characters=min(r['original_characters']for r in rows),
                original_max_characters=max(r['original_characters']for r in rows),
                factored_min_characters=min(r['characters']for r in rows),factored_max_characters=max(r['characters']for r in rows),
                all_ordered_projections_roundtrip_exact=True,model_reader_fidelity_verified=False,
                original_sources_cards_scores_modified=False,new_model_calls=0,production_default_changed=False)


def check():
    path=HERE/'derived.synthetic.json'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=path.with_suffix('.sha256').read_text().strip():raise ValueError('Derived check differs')
    result=build()
    if json.loads(path.read_text())!=result:raise ValueError('Offline factor reconstruction differs')
    return result


if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False,indent=2))
