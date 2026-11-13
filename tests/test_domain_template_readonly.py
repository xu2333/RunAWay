"""Static six-read protocol fixtures;no model,grant or fidelity measurement."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('template_readonly_test_engine',ROOT/'benchmarks/domain-template-readonly-v1/engine.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e);p=e.plan


class Fixture:
    def __init__(self,fault=None,at=None):self.fault,self.at,self.calls=fault,at,[]
    def __call__(self,request,folder,slot):
        self.calls.append(slot)
        answer={q['id']:'U'for q in p.questions(slot)}if slot['kind']=='none'else{q:r['gold']for r in p.inputs()['rows']for q in r['query_ids']}
        if slot['slot']==self.at and self.fault in('control','order'):
            r=next(r for r in p.inputs()['rows']if r['gold']!='U');answer[r['query_ids'][1]]='U'
        if slot['slot']==self.at and self.fault=='wire':answer.pop(next(iter(answer)))
        return json.dumps(answer,ensure_ascii=False),dict(backend='offline_fixture',model_requested=p.MODEL,
            usage=None if slot['slot']==self.at and self.fault=='usage'else[dict(input_tokens=0,output_tokens=0)])


class DomainTemplateReadonlyTests(unittest.TestCase):
    def execute(self,root,fixture):
        p.prepare(root/'inputs');return e.run(root/'inputs',root/'output',fixture,lambda _: {},simulated=True)

    def test_all_eight_requests_are_static_same_task_and_only_reader_material_changes(self):
        values=p.values();self.assertEqual(len(values['static-requests.json']),8)
        self.assertEqual([s['kind']for s in p.slots()],['none','full','read','read','read','read','read','read'])
        views=[p.view(s)for s in p.slots()if s['kind']=='read'];self.assertEqual([v['characters']for v in views if v['view']!='domain_dropped'],[1061,767,767,1061])
        self.assertTrue(all(v['characters']<1061 for v in views if v['view']=='domain_dropped'))
        a,b=[p.request(p.slots()[i])for i in(2,3)]
        self.assertEqual(a['schema'],b['schema']);self.assertEqual(a['system'],b['system'])
        aa=json.loads(a['prompt'].split('READER_INPUT_JSON:\n')[1]);bb=json.loads(b['prompt'].split('READER_INPUT_JSON:\n')[1])
        self.assertEqual(aa['queries'],bb['queries']);self.assertEqual(set(aa),{'material','queries'})
        self.assertEqual(p.codec.restore(bb['material']),p.old.old.candidate.dense.parse(p.old.old.candidate.restore(aa['material'])))
        self.assertNotIn('source_accounting',bb['material'])

    def test_oracle_fixture_completes_eight_with94fixed_cases_per_view_not_model_evidence(self):
        with tempfile.TemporaryDirectory()as tmp:fixture=Fixture();result=self.execute(Path(tmp),fixture)
        self.assertEqual((len(fixture.calls),result['status']),(8,'complete'))
        for view in p.VIEWS:self.assertEqual(result['scores']['views'][view]['strict']['joint'],dict(planned=94,correct=94,missing=0))
        self.assertTrue(result['simulated']);self.assertTrue(result['usage_is_fixture_not_billable'])
        self.assertFalse(result['scores']['generation_stability_verified'])

    def test_one_wrong_order_is_kept_and_not_hidden_by_other_three_answers(self):
        with tempfile.TemporaryDirectory()as tmp:result=self.execute(Path(tmp),Fixture('order',4))
        self.assertEqual(result['scores']['views']['flat1061']['strict']['joint']['correct'],94)
        self.assertEqual(result['scores']['views']['domain767']['strict']['joint']['correct'],93)

    def test_control_failure_stops_before_any_view_and_expires_unused_slots(self):
        with tempfile.TemporaryDirectory()as tmp:fixture=Fixture('control',2);result=self.execute(Path(tmp),fixture)
        self.assertEqual((len(fixture.calls),result['status'],result['unused_slots_expire']),(2,'stopped',6))
        self.assertTrue(result['scope_closed'])

    def test_wire_or_unknown_usage_is_fatal_without_retry_or_replenishment(self):
        for fault in('wire','usage'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory()as tmp:
                fixture=Fixture(fault,3);result=self.execute(Path(tmp),fixture)
                self.assertEqual((len(fixture.calls),result['status'],result['unused_slots_expire']),(3,'stopped',5))

    def test_real_mode_and_prior_closed_scope_refuse_before_creating_output_or_backend(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p.prepare(root/'inputs');invoke=Mock()
            with self.assertRaises(PermissionError):e.run(root/'inputs',root/'out',invoke,lambda _: {},simulated=False)
            good=dict(approved=True,scope=e.gate.SCOPE,model=p.MODEL,max_new_local_cli_attempts=8,
                manifest_sha256=p.sha(root/'inputs/manifest.json'),exact_source_ref='a'*40)
            for change in({'scope':'domain_revision_probe14_v1'},{'max_new_local_cli_attempts':14},{'exact_source_ref':'main'}):
                with self.subTest(change=change),self.assertRaises(PermissionError):e.gate.verify(root/'inputs',dict(good,**change),lambda _:True)
            invoke.assert_not_called();self.assertFalse((root/'out').exists())

    def test_view_and_reference_drift_and_boolean_slots_cannot_enter_execution(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p.prepare(root/'inputs');self.assertTrue(p.verify(root/'inputs'))
            (root/'inputs/views.public.json').write_text('{}')
            with self.assertRaises(ValueError):p.verify(root/'inputs')
        slot=dict(p.slots()[0],slot=True)
        with self.assertRaises(ValueError):p.request(slot)
        env=dict(os.environ);env.pop('PYTHONPATH',None)
        with tempfile.TemporaryDirectory()as tmp:
            proc=subprocess.run([sys.executable,'-B',str(p.HERE/'plan.py'),'--out',str(Path(tmp)/'packet')],
                cwd=tmp,env=env,text=True,capture_output=True,timeout=60)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['new_model_calls'],0)

    def test_constructed_diagnostic_removes_only_six_scope_domains(self):
        data=p.inputs();dense=p.old.old.candidate.dense
        original=dense.parse(p.old.old.candidate.restore(data['views']['flat1061']))
        damaged=dense.parse(p.old.old.candidate.restore(data['views']['domain_dropped']))
        self.assertEqual((original['name'],original['tagline'],original['unknowns']),(damaged['name'],damaged['tagline'],damaged['unknowns']))
        self.assertEqual(len(original['groups']),6)
        for a,b in zip(original['groups'],damaged['groups']):
            self.assertEqual(a['rules'],b['rules']);self.assertNotEqual(a['scope'],b['scope'])
            self.assertIn('非负整数',a['scope']);self.assertNotIn('非负整数',b['scope'])
        self.assertNotIn('非负整数',data['views']['domain_dropped'])
        self.assertTrue(p.values()['proposal.json']['damage_is_constructed_not_model_compression'])


if __name__=='__main__':unittest.main()
