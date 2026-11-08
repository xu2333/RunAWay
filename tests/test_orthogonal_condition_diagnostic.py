import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('orthogonal_tests_engine',ROOT/'benchmarks/orthogonal-condition-diagnostic-v1/engine.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
p=engine.plan


def answer(slot):
    if slot['kind']=='none':return {q['id']:'U'for q in p.questions(slot)}
    rows=[r for r in p.inputs()['rows']if r['person']==slot['profile']]
    return {qid:r['gold']for r in rows for qid in r['query_ids']}


class OrthogonalConditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        p.prepare(cls.root/'packet')
        cls.views=p.views()

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_existing_anchors_and_all_source_messages_are_unchanged(self):
        before=p.old.inputs();after=p.inputs()
        self.assertEqual(before['sources'],after['sources'])
        self.assertEqual(before['rows'],[r for r in after['rows']if r['cohort']!='crossed_time_material'])
        self.assertEqual(len(after['rows']),120)
        self.assertEqual(sum(r['gold']!='U'for r in after['rows']),56)
        for family,bank in before['queries'].items():
            self.assertEqual({q['id']:q for q in bank},{q['id']:q for q in after['queries'][family]if q['id'].startswith('v')})
        self.assertEqual(sum(r['cohort']=='crossed_time_material'and r['gold']=='U'for r in after['rows']),32)

    def test_crossed_facts_are_orthogonal_and_both_orders_have_same_reference(self):
        data=p.inputs()
        for family,bank in data['queries'].items():
            self.assertEqual(len(bank),120);self.assertEqual(len({q['id']for q in bank}),120)
            probes=[q for q in bank if q['id'].startswith('x')]
            self.assertEqual(len(probes),32)
            for q in probes:
                self.assertTrue(('准备时间充裕，材料尚未齐全'in q['scenario'])or('准备时间很紧，材料齐备'in q['scenario']))
                self.assertIn('已经明确允许可撤销模拟',q['scenario'])
            for row in data['rows']:
                if row['family']!=family:continue
                pair=[next(q for q in bank if q['id']==qid)for qid in row['query_ids']]
                self.assertEqual(pair[0]['scenario'],pair[1]['scenario'])
                self.assertEqual(pair[0]['options']['A'],pair[1]['options']['B'])

    def test_views_preserve_all_eight_actual_cards_and_keep_damage_separate(self):
        measured=p.read(p.MEASURED)
        actual=[v for v in self.views if v['method']in p.METHODS]
        self.assertEqual(len(actual),8)
        for view in actual:
            parent=next(r for r in measured['records']if r['slot']==view['parent_slot'])
            self.assertEqual(view['prompt'],parent['artifact']['prompt'])
            self.assertFalse(view['constructed_damage'])
        diagnostic=[v for v in self.views if v['method']in p.DIAGNOSTICS]
        self.assertEqual([v['characters']for v in diagnostic],[831,755])
        self.assertEqual([v['constructed_damage']for v in diagnostic],[False,True])

    def test_schedule_and_all_static_requests_have_no_graph_or_reference_attachment(self):
        slots=p.slots();self.assertEqual(len(slots),24)
        self.assertEqual([s['kind']for s in slots[:4]],['none','none','full','full'])
        self.assertFalse(any(s['kind']=='extract'for s in slots))
        frozen=p.read(self.root/'packet/static-requests.json')
        for slot in slots:
            req=p.request(slot);self.assertEqual(req,frozen[str(slot['slot'])])
            self.assertEqual(req['model'],'gpt-6.1-sol')
            self.assertEqual(set(req['schema']['properties']),{q['id']for q in p.questions(slot)})
            for private in('parent_raw_sha256','reference.private.json','author-evidence','source_accounting','constructed_damage'):
                self.assertNotIn(private,req['prompt'])
            if slot['kind']=='read':
                payload=json.loads(req['prompt'].split('READER_INPUT_JSON:\n',1)[1])
                self.assertEqual(payload['material'],p.view(slot)['prompt'])
                self.assertEqual(payload['queries'],p.questions(slot))
        for view in self.views:
            self.assertEqual(sum(p.parent(s)==p.parent(view)for s in slots if s['kind']=='read'),2)

    def test_person_answer_namespaces_are_not_merged_and_missing_stays_in_denominator(self):
        rows=p.inputs()['rows'];responses={p.parent(s)+(s['read_repeat'],):answer(s)for s in p.slots()if s['kind']=='read'}
        result=engine.score.summarize(rows,responses)
        for method in p.METHODS:self.assertEqual(result['methods'][method]['strict_eight_answers']['joint'],dict(planned=120,correct=120,missing=0))
        slot=next(s for s in p.slots()if s['kind']=='read'and s['method']==p.METHODS[0])
        del responses[p.parent(slot)+(slot['read_repeat'],)]
        result=engine.score.summarize(rows,responses)['methods'][p.METHODS[0]]['strict_eight_answers']['joint']
        self.assertEqual(result,dict(planned=120,correct=60,missing=60))
        always_u={p.parent(s)+(s['read_repeat'],):{q['id']:'U'for q in p.questions(s)}for s in p.slots()if s['kind']=='read'}
        result=engine.score.summarize(rows,always_u)['methods'][p.METHODS[0]]['strict_eight_answers']
        self.assertEqual(result['joint']['correct'],64);self.assertEqual(result['known']['correct'],0)

    def test_packet_is_exclusive_and_rejects_drift_and_symlinks(self):
        packet=self.root/'packet';self.assertTrue(p.verify(packet))
        with self.assertRaises(FileExistsError):p.prepare(packet)
        target=packet/'views.public.json';raw=target.read_bytes()
        try:
            target.write_bytes(raw+b' ')
            with self.assertRaises(ValueError):p.verify(packet,reconstruct=False)
        finally:target.write_bytes(raw)
        with tempfile.TemporaryDirectory()as tmp:
            link=Path(tmp)/'packet';link.symlink_to(packet,target_is_directory=True)
            with self.assertRaises(ValueError):p.verify(link)

    def run_fixture(self,folder,fail_at=None,control_failure=False,guard=True):
        calls=[]
        def invoke(req,out,slot):
            calls.append(slot['slot']);a=answer(slot)
            if control_failure and slot['kind']=='full':a={q['id']:'U'for q in p.questions(slot)}
            usage=[]if slot['slot']==fail_at else[dict(input_tokens=1,output_tokens=1)]
            return json.dumps(a,ensure_ascii=False),dict(backend='codex',model_requested=p.MODEL,usage=usage)
        with patch('runaway.generation.codex_generate',side_effect=AssertionError('No live backend'))as backend:
            result=engine.run(self.root/'packet',folder,invoke,lambda slot:dict(owned_active=guard),simulated=False)
        backend.assert_not_called();return result,calls

    def test_injected_fixture_completes_24_once_and_separates_symbolic_from_reader_scores(self):
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp)/'run';result,calls=self.run_fixture(folder)
            self.assertEqual(calls,list(range(1,25)));self.assertEqual(result['status'],'complete')
            self.assertEqual(result['unused_slots_expire'],0)
            self.assertEqual(result['local_cli_child_intents'],0)
            self.assertEqual(result['scores']['methods'][p.METHODS[1]]['strict_eight_answers']['joint']['correct'],120)
            # A reader returning U despite constructed rule damage is accepted as
            # a diagnostic outcome; no required-error gate is imposed.
            self.assertEqual(result['scores']['constructed_diagnostic'][p.DIAGNOSTICS[1]]['crossed_unknown']['joint']['correct'],16)
            with self.assertRaises(FileExistsError):engine.run(self.root/'packet',folder,None,None,simulated=True)

    def test_unknown_usage_closes_remainder_without_retry_or_replacement(self):
        with tempfile.TemporaryDirectory()as tmp:
            result,calls=self.run_fixture(Path(tmp)/'run',fail_at=5)
            self.assertEqual(calls,list(range(1,6)));self.assertEqual(result['status'],'stopped')
            self.assertEqual(result['unused_slots_expire'],19);self.assertEqual(result['missing_usage'],1)
            for method in p.METHODS:self.assertEqual(result['scores']['methods'][method]['strict_eight_answers']['joint']['missing'],120)

    def test_failed_full_control_stops_before_all_card_reads(self):
        with tempfile.TemporaryDirectory()as tmp:
            result,calls=self.run_fixture(Path(tmp)/'run',control_failure=True)
            self.assertEqual(calls,[1,2,3]);self.assertTrue(result['stop'].startswith('full_control_not_qualified:'))
            self.assertEqual(result['unused_slots_expire'],21)

    def test_inactive_guard_creates_no_invocation_intent(self):
        with tempfile.TemporaryDirectory()as tmp:
            result,calls=self.run_fixture(Path(tmp)/'run',guard=False)
            self.assertEqual(calls,[]);self.assertEqual(result['attempt_reservations'],0)
            self.assertEqual(result['unused_slots_expire'],24)


if __name__=='__main__':unittest.main()
