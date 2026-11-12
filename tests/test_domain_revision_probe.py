"""Source-domain challenges and finite comparison controller;zero services."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('domain_probe_tests_engine',ROOT/'benchmarks/domain-revision-probe-v1/engine.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e);p=e.plan

class DomainRevisionProbeTests(unittest.TestCase):
    def test_existing_source_is_unchanged_not_a_new_holdout(self):
        data=p.inputs();self.assertEqual(set(data['sources']),{'rivet'})
        self.assertEqual(data['sources']['rivet'],p.old.inputs()['sources']['rivet'])
        self.assertEqual(len(data['sources']['rivet']['sources']),48)
        self.assertFalse(p.values()['proposal.json']['approved'])

    def test_all82old_anchors_and164old_questions_stay_byte_equivalent(self):
        before=p.old.inputs();now=p.inputs()
        self.assertEqual(now['rows'][:82],[r for r in before['rows']if r['person']=='rivet'])
        self.assertEqual(now['queries']['rivet'][:164],before['queries']['rivet'])
        self.assertEqual((len(now['rows']),sum(r['personal_known']for r in now['rows'])),(94,36))

    def test_twelve_new_challenges_only_change_one_numeric_fact(self):
        data=p.inputs();queries={q['id']:q for q in data['queries']['rivet']}
        self.assertEqual(len(queries),188)
        self.assertEqual(len({p.digest({k:q[k]for k in('scenario','options')})for q in queries.values()}),188)
        for row in data['rows'][82:]:
            self.assertEqual(row['gold'],'U');self.assertEqual(row['family'],'declared_numeric_domain')
            anchor=next(r for r in data['rows']if r['case']==row['case'].split('_')[0]+'_below_boundary')
            for qid,oldid in zip(row['query_ids'],anchor['query_ids']):
                q,old=queries[qid],queries[oldid]
                self.assertEqual(q['options'],old['options'])
                normalize=lambda t:re.sub(r'余量=-?\d+(?:\.\d+)?','余量=NUMBER',t)
                self.assertEqual(normalize(q['scenario']),normalize(old['scenario']))
                self.assertNotIn('非负整数',q['scenario'])
        self.assertTrue(all(x['independently_adjudicated']is False for x in data['domain_evidence']))

    def test_source_only_extractors_do_not_receive_questions_or_feedback(self):
        data=p.inputs()
        for slot in p.slots():
            req=p.request(slot)
            if slot['kind']=='read':self.assertIsNone(req);continue
            self.assertEqual(req['model'],p.MODEL)
            if slot['kind']=='extract':
                self.assertNotIn('domain_00_',req['prompt']);self.assertNotIn('gold',req['prompt'])
                for q in data['queries']['rivet']:self.assertNotIn(q['scenario'],req['prompt'])
                for source in data['sources']['rivet']['sources']:self.assertIn(source['text'],req['prompt'])
                self.assertEqual(req['schema'],(p.old.candidate.base if slot['method']=='current'else p.revision).schema(data['sources']['rivet']))

    def test_four_independent_parents_two_reads_each_and_balanced_order(self):
        slots=p.slots();self.assertEqual((len(slots),sum(s['kind']=='extract'for s in slots),sum(s['kind']=='read'for s in slots)),(14,4,8))
        ex=[s for s in slots if s['kind']=='extract']
        self.assertEqual([s['method']for s in ex],['current','condition_revision','condition_revision','current'])
        self.assertEqual(len({p.parent(s)for s in ex}),4)
        self.assertTrue(all(s['budget']==1536 for s in slots if s['kind']in('extract','read')))
        bad=copy.deepcopy(slots[0]);bad['slot']=True
        with self.assertRaises(ValueError):p.request(bad)

    def fixture_answers(self):
        return {q:r['gold']for r in p.inputs()['rows']for q in r['query_ids']}

    def test_eight_answers_required_and_a_single_loss_is_visible(self):
        rows=p.inputs()['rows'];a=self.fixture_answers();cards={p.parent(s):'fixture'for s in p.slots()if s['kind']=='extract'}
        responses={p.parent(s)+('card',s['read_repeat']):dict(a)for s in p.slots()if s['kind']=='read'}
        report=e.score.summarize(rows,responses,cards)
        self.assertEqual(report['methods']['condition_revision']['strict']['joint']['correct'],94)
        key=next(k for k in responses if k[1]=='condition_revision');known=next(r for r in rows if r['gold']!='U')
        responses[key][known['query_ids'][0]]='U'
        changed=e.score.summarize(rows,responses,cards)
        self.assertEqual(changed['methods']['condition_revision']['strict']['joint']['correct'],93)
        self.assertEqual(changed['paired_transitions']['baseline_only_retained'],1)
        self.assertTrue(all(len(c['current']['answers'])==8 for c in changed['all_case_transitions']))

    def test_missing_parent_is_not_unknown_or_a_recovery(self):
        report=e.score.summarize(p.inputs()['rows'],{}, {})
        for m in p.METHODS:
            cell=report['methods'][m]['strict']['joint'];self.assertEqual(cell,dict(planned=94,correct=0,missing=94))
        self.assertEqual(report['paired_transitions']['both_missing'],94)

    def test_freeze_verification_rejects_reference_drift_and_extra_files(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)/'packet';p.prepare(root);self.assertTrue(p.verify(root))
            f=root/'reference.private.json';f.write_text('[]')
            with self.assertRaises(ValueError):p.verify(root)
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)/'packet';p.prepare(root);(root/'extra').write_text('x')
            with self.assertRaises(ValueError):p.verify(root)

    def test_real_engine_refuses_absent_or_wrong_finite_grant(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)/'packet';p.prepare(root)
            with self.assertRaises(PermissionError):e.run(root,Path(tmp)/'out',lambda *a:None,lambda *a:{},simulated=False)
            approval=dict(approved=True,scope=e.gate.SCOPE,model=p.MODEL,max_new_local_cli_attempts=14,manifest_sha256=p.sha(root/'manifest.json'),exact_source_ref='a'*40)
            with self.assertRaises(PermissionError):e.run(root,Path(tmp)/'out',lambda *a:None,lambda *a:{},simulated=False,approval=approval,verify_human_grant=lambda a:False)
            self.assertFalse((Path(tmp)/'out').exists())

    def test_failing_new_domain_control_stops_before_any_extraction(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)/'packet';p.prepare(root);seen=[]
            def invoke(req,folder,slot):
                seen.append(slot['kind']);answer=self.fixture_answers()if slot['kind']=='full'else{q:'U'for q in self.fixture_answers()}
                if slot['kind']=='full':
                    row=p.inputs()['rows'][82];q=row['query_ids'][0]
                    answer[q]=next(x['options']['A']for x in p.inputs()['queries']['rivet']if x['id']==q)
                return json.dumps(answer,ensure_ascii=False),dict(model_requested=p.MODEL,usage=[dict(input_tokens=0,output_tokens=0)])
            result=e.run(root,Path(tmp)/'out',invoke,lambda slot:dict(owned_active=True),simulated=True)
            self.assertEqual(seen,['none','full']);self.assertTrue(result['stop'].startswith('full_control_not_qualified'))
            self.assertEqual(result['unused_slots_expire'],12)
            self.assertEqual(result['scores']['methods']['current']['strict']['joint']['missing'],94)

    def test_preparation_cli_runs_outside_checkout_without_pythonpath(self):
        env={k:v for k,v in os.environ.items()if k!='PYTHONPATH'}
        with tempfile.TemporaryDirectory()as tmp:
            proc=subprocess.run([sys.executable,'-B',str(p.HERE/'plan.py'),'--out',str(Path(tmp)/'packet')],cwd=tmp,env=env,capture_output=True,text=True,timeout=60)
            self.assertEqual(proc.returncode,0,proc.stderr);self.assertFalse(json.loads(proc.stdout)['approved'])
            self.assertTrue(p.verify(Path(tmp)/'packet'))

if __name__=='__main__':unittest.main()
