import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runaway import shared_schema as shared, generation

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'examples/shared-schema'
SOURCE=ROOT/'examples/structural-dual-evidence.synthetic.zip'


class ReferenceProofTests(unittest.TestCase):
    def request(self):
        item=dict(type='object',properties={'v':dict(type='string',enum=['A','U'])},required=['v'],additionalProperties=False)
        answers=dict(type='object',properties={'id-1':item,'id-2':copy.deepcopy(item)},required=['id-1','id-2'],additionalProperties=False)
        return dict(system='same',prompt='same',schema=dict(type='object',properties={'answers':answers},required=['answers'],additionalProperties=False))

    def test_exact_expansion_including_all_id_constraints(self):
        old=self.request();before=copy.deepcopy(old);new=shared.hoist(old)
        self.assertEqual(old,before);self.assertEqual(shared.expanded(new['schema']),old['schema'])
        for response,want in [({'answers':{'id-1':{'v':'A'},'id-2':{'v':'U'}}},True),({'answers':{'id-1':{'v':'A'}}},False),({'answers':{'id-1':{'v':'X'},'id-2':{'v':'U'}}},False)]:
            self.assertEqual(shared.accepts(response,old['schema']),want)
            self.assertEqual(shared.accepts(response,new['schema']),want)
        bad=copy.deepcopy(new);bad['schema']['properties']['answers']['required'].pop()
        with self.assertRaises(ValueError):shared.prove(old,bad)
        bad=copy.deepcopy(new);bad['prompt']='different'
        with self.assertRaises(ValueError):shared.prove(old,bad)

    def test_heterogeneous_fields_bad_refs_and_cycles_fail_closed(self):
        old=self.request();old['schema']['properties']['answers']['properties']['id-2']['required']=[]
        with self.assertRaises(ValueError):shared.hoist(old)
        new=shared.hoist(self.request())
        for bad_ref in ['https://example.invalid/schema','#/$defs/unknown']:
            bad=copy.deepcopy(new['schema']);bad['properties']['answers']['properties']['id-1']['$ref']=bad_ref
            with self.assertRaises(ValueError):shared.expanded(bad)
        bad=copy.deepcopy(new['schema']);bad['$defs']['answer']={'$ref':'#/$defs/answer'}
        with self.assertRaises(ValueError):shared.expanded(bad)
        bad=copy.deepcopy(new['schema']);bad['properties']['answers']['properties']['id-1']['type']='object'
        with self.assertRaises(ValueError):shared.expanded(bad)

    def test_wire_parser_does_not_normalize_duplicate_keys_invalid_utf8_or_nan(self):
        for wire in [b'{"a":1,"a":2}',b'{"a":NaN}',b'{}\xff']:
            with self.assertRaises((ValueError,UnicodeError)):shared.parse_wire(wire)
        self.assertEqual(shared.parse_wire(' \n{"a":null}\t'),{'a':None})

    def test_score_fingerprint_uses_exact_counts_instead_of_macro_roundoff(self):
        a=dict(correct=2,planned=3,paired_clusters=[dict(correct=2,planned=3)]*3,macro_cluster_accuracy=0.6666666666666668)
        b=dict(a,macro_cluster_accuracy=0.6666666666666666)
        self.assertEqual(shared.score_fingerprint(a),shared.score_fingerprint(b))
        self.assertNotEqual(shared.score_fingerprint(a),shared.score_fingerprint(dict(b,correct=1)))


class FrozenVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=shared.load_source(SOURCE);cls.requests=json.loads((BASE/'requests.synthetic.json').read_text());cls.report=json.loads((BASE/'report.synthetic.json').read_text())

    def test_all16requests_replay_with_exact_recorded_counts_not_estimates(self):
        counts={}
        for row in self.report['whole_request_lengths']:
            old=next(j for stage in shared.STAGES for j in self.source['design'][stage] if j['request_id']==row['source_request_id'])
            new=next(j for stage in shared.STAGES for j in self.requests[stage] if j['request_id']==row['request_id'])
            counts[shared.canonical(old['request'])]=row['before']['actual_local_vocabulary_tokens']
            counts[shared.canonical(new['request'])]=row['after']['actual_local_vocabulary_tokens']
        with patch.object(generation,'codex_generate',side_effect=AssertionError('No service')):
            variants,report=shared.make_variant(self.source,lambda text:counts[text])
        self.assertEqual(variants,self.requests);self.assertEqual(report,self.report)
        self.assertEqual(len(report['proofs']),16)
        self.assertEqual(report['totals']['before']['actual_local_vocabulary_tokens'],142763)
        self.assertLess(report['totals']['after']['actual_local_vocabulary_tokens'],142763)

    def test_every_acceptance_and_score_decision_matches_without_missing_repairs(self):
        audit=self.report['audit'];self.assertTrue(audit['all_score_signatures_equal']);self.assertEqual(audit['case_count'],590)
        for row in audit['cases']:
            self.assertEqual(row['old_accepted'],row['new_accepted'])
            if row['case']=='mutation:missing_query':
                self.assertFalse(row['old_accepted']);self.assertEqual(row['score']['strict_missing'],1);self.assertEqual(row['score']['completion_missing'],1)
            if row['case']=='mutation:illegal_strict_answer':
                self.assertFalse(row['old_accepted']);self.assertEqual(row['score']['strict_invalid'],1)
            if row['case']=='mutation:duplicate_outcome':
                self.assertTrue(row['old_accepted']);self.assertEqual(row['score']['status'],'rejected')
        self.assertEqual(self.report['backend_compatibility'],'unmeasured')

    def test_original_ids_prompts_payloads_and_model_independence_are_preserved(self):
        ids=set()
        for stage in shared.STAGES:
            self.assertEqual(len(self.requests[stage]),len(self.source['design'][stage]))
            for old,new in zip(self.source['design'][stage],self.requests[stage]):
                self.assertEqual(old['request']['prompt'],new['request']['prompt']);self.assertEqual(old['request']['system'],new['request']['system'])
                self.assertEqual(shared.expanded(new['request']['schema']),old['request']['schema'])
                self.assertNotEqual(old['request_id'],new['request_id']);ids.add(new['request_id'])
        self.assertEqual(len(ids),16)
        self.assertEqual(self.report['new_external_model_calls'],0)

    def test_invalid_utf8_fixture_hash_binds_the_actual_original_bytes(self):
        job=self.requests['development_jobs'][0];pid=job['person_id'];rows=self.source['records']['development']['intact_dual_program'][pid]
        raw=next(wire for name,wire in shared.corruptions(dict(answers=rows)) if name=='invalid_utf8')
        case=next(c for c in self.report['audit']['cases'] if c['request_id']==job['request_id'] and c['case']=='mutation:invalid_utf8')
        self.assertEqual(case['wire_sha256'],hashlib.sha256(raw).hexdigest())


if __name__=='__main__':unittest.main()
