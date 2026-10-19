import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runaway import generation, structural_dual as bench, temporal_concise as codec, temporal_determinacy as dual

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'examples/structural-dual'


class OracleTests(unittest.TestCase):
    def test_oracle_set_regions_does_not_call_production_and_separates_invariant_action(self):
        policy=dict(scope='manual unit',unmodeled=0,domains=[dict(domain='d',regular=['x'],exception=[dict(when=[['p',True]],action='x')],constraint=[dict(when=[['p',True],['q',True]],action='y')])])
        options=dict(A='x',B='y',U='unknown')
        with patch.object(codec,'resolve',side_effect=AssertionError('No production oracle')):
            e=bench.expected_row(policy,'d',{'q':False},options)
            self.assertEqual((e['strict_answer'],e['reported_status'],e['completion_answer']),('U','context_unknown','A'))
            self.assertEqual(e['possible_outcomes'],[dict(status='chosen',action='x')])
            e=bench.expected_row(policy,'d',{},options)
            self.assertEqual((e['completion_answer'],len(e['possible_outcomes'])),('U',2))
            self.assertEqual(bench.expected_row(policy,'absent',{},options)['reported_status'],'unobserved')
        changed=copy.deepcopy(policy);changed['domains'][0]['regular']=['x','y'];changed['domains'][0]['exception']=[];changed['domains'][0]['constraint']=[]
        self.assertEqual(bench.expected_row(changed,'d',{},options)['possible_outcomes'],[dict(status='conflict',action=None)])

    def test_signature_ignores_renaming_and_global_truth_flips_but_keeps_opposed_sharing(self):
        a=dict(regular=['0'],exception=[dict(when=[['p',True]],action='1')],constraint=[dict(when=[['p',True],['q',True]],action='0')])
        b=dict(regular=['x'],exception=[dict(when=[['z',False]],action='y')],constraint=[dict(when=[['w',True],['z',False]],action='x')])
        self.assertEqual(bench.signature(a,['p','q']),bench.signature(b,['z','w']))
        b['constraint'][0]['when'][1][1]=True
        self.assertNotEqual(bench.signature(a,['p','q']),bench.signature(b,['z','w']))


class FrozenBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=json.loads((BASE/'plan.synthetic.json').read_text())

    def test_frozen_split_signatures_and_exact_fixed_census(self):
        audit=bench.structural_audit(self.plan);self.assertTrue(audit['disjoint']);self.assertEqual((audit['development_classes'],audit['holdout_classes']),(3,4))
        for split,planned,pairs in [('development',96,3),('holdout',376,4)]:
            world,expected,policies=bench.build_split(self.plan,split)
            self.assertEqual(sum(len(p['cases']) for p in world['people']),planned)
            self.assertEqual(len(world['people']),pairs*2)
            self.assertEqual(world,json.loads((BASE/(split+'-world.synthetic.json')).read_text()))
            self.assertEqual(expected,json.loads((BASE/(split+'-expected.synthetic.json')).read_text()))
            self.assertEqual(policies,json.loads((BASE/(split+'-policies.synthetic.json')).read_text()))

    def test_program_audit_replays_without_service_or_old_template_oracle(self):
        for split in ('development','holdout'):
            world,expected,policies=bench.build_split(self.plan,split)
            with patch.object(generation,'codex_generate',side_effect=AssertionError('No services')), patch.object(dual,'authored_expected',side_effect=AssertionError('No old template gold')):
                actual,records=bench.audit_split(self.plan,world,expected,policies)
            stored=json.loads((BASE/(split+'-report.synthetic.json')).read_text())
            for report in (stored,):
                for job in report['reader_jobs']:
                    job['whole_memory_lengths']['actual_local_vocabulary_tokens']=None;job['canonical_request_lengths']['actual_local_vocabulary_tokens']=None
                for rows in report['complete_program_output_lengths'].values():
                    for row in rows.values():row['actual_local_vocabulary_tokens']=None
            self.assertEqual(stored,actual);self.assertTrue(actual['passed'])
            self.assertEqual(records,json.loads((BASE/(split+'-program-records.synthetic.json')).read_text()))

    def test_reader_payload_contains_only_memory_public_queries_schema_and_contract(self):
        forbidden=('seed','motifs','gold','expected','program_records','split','family','signature')
        for split in ('development','holdout'):
            report=json.loads((BASE/(split+'-report.synthetic.json')).read_text())
            for job in report['reader_jobs']:
                request=job['request'];payload=json.loads(request['prompt'].split('\nINPUT_JSON:\n',1)[1])
                self.assertEqual(set(payload),{'memory','queries'})
                self.assertFalse(set(payload)&set(forbidden));codec.decode(payload['memory'])
                self.assertEqual(set(request),{'system','prompt','schema'})
                for q in payload['queries']:self.assertEqual(set(q),{'id','task','domain','context','question','answer_options'})
                self.assertEqual(request['schema']['properties']['answers']['required'],[q['id'] for q in payload['queries']])

    def test_source_freeze_precedes_holdout_and_design_denominators_never_change(self):
        initial=json.loads((BASE/'implementation-freeze.json').read_text());entry=json.loads((BASE/'holdout-entry-freeze.json').read_text())
        self.assertEqual(initial['implementation_hashes'],entry['implementation_hashes'])
        self.assertLess(initial['created_at'],entry['entered_at'])
        self.assertEqual(entry['development_report_sha256'],bench.file_hash(BASE/'development-report.synthetic.json'))
        for split in ('development','holdout'):
            r=json.loads((BASE/(split+'-report.synthetic.json')).read_text());self.assertTrue(r['passed'])
            self.assertEqual(r['historical'],dict(planned=0,status='unmeasured'))
            for control in self.plan['controls']:
                for key in ('strict_choice','reported_rule_status','completion_choice','possible_outcomes'):
                    self.assertEqual(r['controls'][control][key]['joint']['planned'],r['planned'])


if __name__=='__main__':unittest.main()
