import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from runaway import support_extract as s
from runaway.choice_reader import make_request

SOURCES={'schema_version':1,'sources':[
 {'id':'q1','episode_id':'e1','role':'user','text':'只改本地副本，4%分错，可立即恢复，不外发。'},
 {'id':'a1','episode_id':'e1','role':'assistant','text':'我建议逐项确认。'},
 {'id':'u1','episode_id':'e1','role':'user','text':'我选默认自动处理。'},
 {'id':'q2','episode_id':'e2','role':'user','text':'同样4%分错，但对外发送后无法撤回。'},
 {'id':'u2','episode_id':'e2','role':'user','text':'我仍选默认自动处理。'}]}
ANSWER={'name':'揣着撤销键的团子','tagline':'先让小车跑，记得哪段路有回头。','branches':[
 {'when':'本地副本4%错误且可立即恢复、不外发','choose':'默认自动处理','priority':0,'decisions':[{'source_id':'u1','quote':'我选默认自动处理。'}],'contexts':[{'source_id':'q1','quote':SOURCES['sources'][0]['text']}],'supersedes':[]},
 {'when':'4%错误的对外结果不能撤回','choose':'默认自动处理','priority':1,'decisions':[{'source_id':'u2','quote':'我仍选默认自动处理。'}],'contexts':[{'source_id':'q2','quote':SOURCES['sources'][3]['text']}],'supersedes':[]}],
 'unknowns':['未覆盖的错误率与用途未知。']}

class SupportExtractionTests(unittest.TestCase):
    def test_equal_action_branches_not_generalized(self):
        files=s.bind(ANSWER,SOURCES);text=files['prompt.md'];self.assertIn('4%错误的对外结果不能撤回',text);self.assertIn('本地副本4%错误',text)
        self.assertEqual(text.count('我选默认自动处理'),2);self.assertLessEqual(len(text),768)
        self.assertNotIn('source_id',text);self.assertFalse(files['summary.private.json']['semantic_support_verified'])

    def test_assistant_and_inexact_decision_anchors_rejected(self):
        for anchor in [{'source_id':'a1','quote':'我建议逐项确认。'},{'source_id':'u1','quote':'没有这段话'}]:
            answer=copy.deepcopy(ANSWER);answer['branches'][0]['decisions']=[anchor]
            with self.assertRaises(ValueError):s.bind(answer,SOURCES)

    def test_no_truncation_and_no_budget_bool(self):
        overflow=copy.deepcopy(ANSWER);overflow['unknowns']=[''.join(chr(0x4e00+i*160+j) for j in range(160)) for i in range(4)]
        with self.assertRaisesRegex(ValueError,'no truncation'):s.bind(overflow,SOURCES,300)
        with self.assertRaises(ValueError):s.bind(ANSWER,SOURCES,True)
        self.assertEqual(s.render(ANSWER),s.bind(ANSWER,SOURCES)['prompt.md'])

    def test_supersession_must_point_backward_to_user(self):
        answer=copy.deepcopy(ANSWER);answer['branches'][0]['supersedes']=['u2']
        with self.assertRaises(ValueError):s.bind(answer,SOURCES)
        answer['branches'][0]['supersedes']=['a1']
        with self.assertRaises(ValueError):s.bind(answer,SOURCES)
        answer=copy.deepcopy(ANSWER);answer['branches'][1]['supersedes']=['u1'];s.bind(answer,SOURCES)

    def test_unknown_only_narrative_can_export_conservatively(self):
        answer={'name':'未填写的小书签','tagline':'空白不是我的新偏好。','branches':[],'unknowns':['没有足够的明确选择证据。']}
        self.assertEqual(s.bind(answer,SOURCES)['summary.private.json']['branches'],0)

    def test_cli_prepare_import_and_preflight_flags(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);source=folder/'sources.json';answer=folder/'answer.json';source.write_text(json.dumps(SOURCES));answer.write_text(json.dumps(ANSWER));out=folder/'out'
            run=lambda *args:subprocess.run([sys.executable,'-B','-m','runaway','distill','--input',str(source),*args],capture_output=True,text=True)
            prep=run('--prepare');self.assertEqual(prep.returncode,0,prep.stderr);self.assertEqual(json.loads(prep.stdout)['schema'],s.SCHEMA)
            result=run('--answer',str(answer),'--out',str(out));self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['model_calls'],0)
            self.assertTrue((out/'portable.json').exists());self.assertNotEqual(run('--answer',str(answer),'--out',str(out)).returncode,0)
            self.assertNotEqual(run('--prepare','--backend','codex').returncode,0)

    def test_one_call_generation_and_failure_preserved(self):
        called=[]
        def backend(prompt,model,**kwargs):called.append((prompt,model,kwargs));return json.dumps(ANSWER),{'backend':'fixture'}
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'success';summary=s.generate(SOURCES,out,'fixture-model',backend=backend)
            self.assertEqual(summary['model_calls'],1);self.assertEqual(len(called),1)
            def failed(*args,**kwargs):raise ValueError('failed fixture')
            out=Path(folder)/'failure'
            with self.assertRaises(ValueError):s.generate(SOURCES,out,'fixture-model',backend=failed)
            self.assertFalse((out/'portable.json').exists());self.assertFalse(json.loads((out/'failure.private.json').read_text())['automatic_retry'])

    def test_multichoice_schema_and_no_private_metadata(self):
        qs=[{'id':'q01','scenario':'选哪一项？','options':{'A':'甲','B':'乙','C':'丙','D':'丁'}}]
        request=make_request('材料',qs,as_of='2026-04-01')
        self.assertEqual(request['schema']['properties']['q01']['enum'],['A','B','C','D','U'])
        body=json.loads(request['prompt'].split('\nREADER_INPUT_JSON:\n')[1]);self.assertEqual(set(body),{'material','queries'})
        bad=copy.deepcopy(qs);bad[0]['gold']='A'
        with self.assertRaises(ValueError):make_request('材料',bad)
        with self.assertRaises(ValueError):make_request('材料',[qs[0],qs[0]])

if __name__=='__main__':unittest.main()
