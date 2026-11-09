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
s=importlib.util.spec_from_file_location('template_readonly_test_engine',ROOT/'benchmarks/guard-template-readonly-v1/engine.py')
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


class GuardTemplateReadonlyTests(unittest.TestCase):
    def execute(self,root,fixture):
        p.prepare(root/'inputs');return e.run(root/'inputs',root/'output',fixture,lambda _: {},simulated=True)

    def test_all_six_requests_are_static_same_task_and_only_reader_material_changes(self):
        values=p.values();self.assertEqual(len(values['static-requests.json']),6)
        self.assertEqual([s['kind']for s in p.slots()],['none','full','read','read','read','read'])
        views=[p.view(s)for s in p.slots()if s['kind']=='read'];self.assertEqual([v['characters']for v in views],[997,768,768,997])
        a,b=[p.request(p.slots()[i])for i in(2,3)]
        self.assertEqual(a['schema'],b['schema']);self.assertEqual(a['system'],b['system'])
        aa=json.loads(a['prompt'].split('READER_INPUT_JSON:\n')[1]);bb=json.loads(b['prompt'].split('READER_INPUT_JSON:\n')[1])
        self.assertEqual(aa['queries'],bb['queries']);self.assertEqual(set(aa),{'material','queries'})
        self.assertEqual(p.up.template_restore(bb['material']),p.old.candidate.dense.parse(p.old.candidate.restore(aa['material'])))
        self.assertNotIn('source_accounting',bb['material'])

    def test_oracle_fixture_completes_six_with82fixed_cases_per_view_not_model_evidence(self):
        with tempfile.TemporaryDirectory()as tmp:fixture=Fixture();result=self.execute(Path(tmp),fixture)
        self.assertEqual((len(fixture.calls),result['status']),(6,'complete'))
        for view in p.VIEWS:self.assertEqual(result['scores']['views'][view]['strict']['joint'],dict(planned=82,correct=82,missing=0))
        self.assertTrue(result['simulated']);self.assertTrue(result['usage_is_fixture_not_billable'])
        self.assertFalse(result['scores']['generation_stability_verified'])

    def test_one_wrong_order_is_kept_and_not_hidden_by_other_three_answers(self):
        with tempfile.TemporaryDirectory()as tmp:result=self.execute(Path(tmp),Fixture('order',4))
        self.assertEqual(result['scores']['views']['flat997']['strict']['joint']['correct'],82)
        self.assertEqual(result['scores']['views']['template768']['strict']['joint']['correct'],81)

    def test_control_failure_stops_before_any_view_and_expires_unused_slots(self):
        with tempfile.TemporaryDirectory()as tmp:fixture=Fixture('control',2);result=self.execute(Path(tmp),fixture)
        self.assertEqual((len(fixture.calls),result['status'],result['unused_slots_expire']),(2,'stopped',4))
        self.assertTrue(result['scope_closed'])

    def test_wire_or_unknown_usage_is_fatal_without_retry_or_replenishment(self):
        for fault in('wire','usage'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory()as tmp:
                fixture=Fixture(fault,3);result=self.execute(Path(tmp),fixture)
                self.assertEqual((len(fixture.calls),result['status'],result['unused_slots_expire']),(3,'stopped',3))

    def test_real_mode_and_prior_closed_scope_refuse_before_creating_output_or_backend(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);p.prepare(root/'inputs');invoke=Mock()
            with self.assertRaises(PermissionError):e.run(root/'inputs',root/'out',invoke,lambda _: {},simulated=False)
            good=dict(approved=True,scope=e.gate.SCOPE,model=p.MODEL,max_new_local_cli_attempts=6,
                manifest_sha256=p.sha(root/'inputs/manifest.json'),exact_source_ref='a'*40)
            for change in({'scope':'heterogeneous_guard_pressure_16_v1'},{'max_new_local_cli_attempts':16},{'exact_source_ref':'main'}):
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


if __name__=='__main__':unittest.main()
