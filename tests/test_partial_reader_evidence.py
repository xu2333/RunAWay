import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]


class PartialReaderEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        with zipfile.ZipFile(ROOT/'examples/partial-reader-evidence.synthetic.zip') as z:
            if any(not n.startswith('d0031/') or '..' in Path(n).parts for n in z.namelist()):raise ValueError('Unsafe evidence member')
            z.extractall(cls.temp.name)
        cls.base=Path(cls.temp.name)/'d0031'

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def replay(self,optimized=False):
        return subprocess.run([sys.executable,*(['-O'] if optimized else []),'-B',str(ROOT/'scripts/replay_partial_reader_evidence.py'),'--base',str(self.base)],capture_output=True,text=True)

    def test_actual_two_calls_and_original_failure_replay_from_frozen_source(self):
        result=self.replay();self.assertEqual(result.returncode,0,result.stderr)
        actual=json.loads(result.stdout);stored=json.loads((self.base/'report.synthetic.json').read_text())
        self.assertEqual(actual['actual_memory_token_recounts'],0);self.assertEqual(actual['actual_request_envelope_recounts'],0)
        actual['actual_memory_token_recounts']=2;actual['actual_request_envelope_recounts']=2;actual['checks']['actual_tokenizer_recounted']=True
        self.assertEqual(actual,stored);self.assertEqual(stored,json.loads((ROOT/'examples/partial-reader-results.synthetic.json').read_text()))
        self.assertFalse(stored['strict_target_passed']);self.assertEqual(stored['status'],'complete')
        self.assertEqual(stored['calls']['execution_records'],2);self.assertEqual(stored['calls']['known_usage']['total_tokens'],17567)
        self.assertEqual(stored['scores']['current_choice']['correct'],34)
        self.assertEqual(stored['scores']['context_slices']['partial_context']['correct'],18)
        self.assertEqual(stored['scores']['context_slices']['complete_context']['correct'],16)
        self.assertEqual(stored['scores']['current_choice']['missing'],0)
        self.assertIsNone(stored['scores']['historical_reconstruction']['correct']);self.assertEqual(stored['scores']['historical_reconstruction']['planned'],0)
        self.assertIsNone(stored['scores']['state_preservation']['correct'])
        self.assertEqual(stored['paired_statistical_units'],1);self.assertFalse(stored['real_person_fidelity_verified'])

    def test_posthoc_invariance_does_not_rewrite_contract_or_infer_hidden_reasoning(self):
        r=json.loads((self.base/'report.synthetic.json').read_text());a=r['posthoc_completion_analysis']
        self.assertTrue(a['primary_scores_and_failure_target_unchanged']);self.assertTrue(a['model_reasoning_not_observed'])
        self.assertEqual(a['groups']['decision_changing_missing'],{'planned':12,'strict_contract_correct':12,'missing':0})
        self.assertEqual(a['groups']['invariant_but_strict_unknown'],{'planned':4,'strict_contract_correct':2,'missing':0})
        self.assertEqual(a['groups']['known_action_despite_missing'],{'planned':4,'strict_contract_correct':4,'missing':0})
        self.assertEqual(a['unique_failed_person_scenarios'],1);self.assertEqual(len(a['failed_answers']),2)
        self.assertEqual({e['prediction'] for e in a['failed_answers']},{'A','B'})
        for e in a['failed_answers']:
            self.assertEqual(e['gold'],'U');self.assertEqual(e['predicted_action'],'0')
            self.assertTrue(e['action_invariant_across_missing_completions']);self.assertEqual(len(e['completions']),2)
            self.assertEqual({c['action'] for c in e['completions']},{'0'})
        self.assertFalse(r['strict_target_passed'])

    def test_manifest_and_explicit_withheld_private_input_boundary(self):
        manifest=json.loads((self.base/'manifest.json').read_text());contract=json.loads((self.base/'contract.synthetic.json').read_text())
        self.assertEqual(len(manifest),67)
        self.assertEqual(set(manifest),{str(p.relative_to(self.base)) for p in self.base.rglob('*') if p.is_file() and p.name!='manifest.json'})
        self.assertEqual(len(contract['source_hashes']),51);self.assertEqual(len(contract['input_hashes']),5)
        self.assertEqual(set(contract['withheld_private_input_hashes']),{'executor-acceptance.json'})
        self.assertEqual(len(contract['withheld_private_input_hashes']['executor-acceptance.json']),64)
        for name,sha in manifest.items():
            data=(self.base/name).read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),sha)
            self.assertNotIn('approval',name);self.assertNotIn('execution-intent',name)
            if not name.startswith('frozen-source/'):
                for private in ('/Users/','human_source','access_token','refresh_token'):self.assertNotIn(private,data.decode())
        for name,sha in contract['input_hashes'].items():self.assertEqual(hashlib.sha256((self.base/contract['input_aliases'][name]).read_bytes()).hexdigest(),sha)
        for name,input_name in contract['auxiliary_input_aliases'].items():self.assertEqual(hashlib.sha256((self.base/'frozen-source'/name).read_bytes()).hexdigest(),contract['input_hashes'][input_name])

    def test_tampered_raw_usage_and_answer_identity_are_rejected(self):
        path=next((self.base/'calls').glob('*.response.json'));original=path.read_bytes()
        try:
            d=json.loads(original);d['provenance']['usage'][0]['input_tokens']+=1;path.write_text(json.dumps(d))
            self.assertNotEqual(self.replay().returncode,0)
        finally:path.write_bytes(original)
        path=self.base/'answers.synthetic.json';original=path.read_bytes()
        try:
            d=json.loads(original);answers=d[next(iter(d))];key=next(iter(answers));answers[key]='U' if answers[key]!='U' else 'A';path.write_text(json.dumps(d))
            self.assertNotEqual(self.replay().returncode,0)
        finally:path.write_bytes(original)

    def test_rescoring_failure_as_pass_or_modifying_gold_is_rejected(self):
        for name in ('raw-report.synthetic.json','gold.synthetic.json'):
            path=self.base/name;original=path.read_bytes()
            try:
                d=json.loads(original)
                if name.startswith('raw-report'):
                    d['strict_target_passed']=True;d['scores']['current_choice']['correct']=36
                else:d[next(iter(d))][0]['gold']='A'
                path.write_text(json.dumps(d));self.assertNotEqual(self.replay().returncode,0)
            finally:path.write_bytes(original)

    def test_optimized_mode_cannot_skip_replay(self):
        result=self.replay(True);self.assertNotEqual(result.returncode,0);self.assertIn('Evidence replay requires assertions enabled',result.stderr)


if __name__=='__main__':unittest.main()
