import json
from pathlib import Path
import shutil
import tempfile
import unittest

from runaway.card import canonical, digest
from runaway.execution_ledger import collect, summarize, start_attempt
from runaway.selfplay import Calls, SYSTEM
from runaway.pipeline import write_once


class ExecutionLedgerTests(unittest.TestCase):
    def test_same_request_independent_invocations_count_but_copies_do_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            invoked = []
            def fake(*a, **kw):
                invoked.append(1)
                return '{"answer":1}', {'model_requested':'offline', 'usage':[{'input_tokens':100, 'cached_input_tokens':80, 'output_tokens':10, 'reasoning_output_tokens':8}]}
            for name in ['first', 'second']:
                folder = root / name
                folder.mkdir()
                calls = Calls(folder, fake)
                calls.call('identical', {}, 'offline')
                calls.call('identical', {}, 'offline')  # Cached, no new attempt.
            shutil.copytree(root/'first', root/'copy')
            r = summarize(collect(root))
            self.assertEqual(len(invoked), 2)
            self.assertEqual(r['execution_records'], 2)
            self.assertEqual(r['unique_request_fingerprints'], 1)
            self.assertEqual(r['copied_artifacts_excluded'], 1)
            self.assertEqual(r['known_usage']['total_tokens'], 220)
            self.assertEqual(r['known_usage']['cached_input_tokens'], 160)

    def test_legacy_usage_distinctions_and_format_only_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = {'prompt':'same', 'schema':{}, 'model':'offline', 'system':SYSTEM}
            key = digest(canonical(request))
            for i, (name, tokens) in enumerate([('first',100), ('second',101), ('copy',100)]):
                folder = root/name/'calls';folder.mkdir(parents=True)
                (folder/(key+'.request.json')).write_text(json.dumps(request))
                result = {'answer':{'same':'answer'}, 'request_id':key, 'provenance':{'model_requested':'offline', 'usage':[{'input_tokens':tokens, 'output_tokens':10}], 'elapsed_seconds':1 if tokens==100 else 2}}
                result['sha256'] = digest(canonical(result))
                (folder/(key+'.response.json')).write_text(json.dumps(result, indent=i))
            rows = collect(root);r = summarize(rows)
            self.assertEqual(r['execution_records'],2)
            self.assertEqual(r['copied_artifacts_excluded'],1)
            self.assertEqual(r['known_usage']['total_tokens'],221)
            self.assertTrue(all(x['identity_basis'].startswith('retrospective') for x in rows))
            self.assertTrue(all(x['recorded_at'] is None for x in rows))

    def test_unresolved_intent_blocks_retry_and_has_unknown_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'first';folder.mkdir();calls=Calls(folder, lambda *a,**k:self.fail('must not call backend'))
            request={'prompt':'pending', 'schema':{}, 'model':'offline', 'system':SYSTEM};key=digest(canonical(request))
            write_once(folder/'calls'/(key+'.request.json'),request)
            start_attempt(folder/'calls'/(key+'.attempt.json'),key)
            with self.assertRaisesRegex(ValueError,'Unresolved prior attempt'):calls.call('pending',{},'offline')
            r=summarize(collect(root));self.assertEqual(r['executions_missing_usage'],1)
            self.assertEqual(r['outcomes'],{'unresolved_invocation_intent':1})

    def test_failed_parse_retains_known_usage_and_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'first';folder.mkdir()
            def fake(*a,**k):return 'bad json', {'usage':[{'input_tokens':20,'output_tokens':5}]}
            calls=Calls(folder,fake)
            with self.assertRaises(ValueError):calls.call('invalid',{},'offline')
            self.assertEqual(summarize(collect(root))['known_usage']['total_tokens'],25)
            failure=next((folder/'calls').glob('*.failure.json'));x=json.loads(failure.read_text());x['provenance']['usage'][0]['input_tokens']=200;failure.write_text(json.dumps(x))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):collect(root)

    def test_conflicting_identity_is_not_silently_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'first';folder.mkdir()
            Calls(folder,lambda *a,**k:('{"ok":true}',{'usage':[{'input_tokens':1,'output_tokens':2}]})).call('same',{},'offline')
            shutil.copytree(folder,root/'copy')
            response=next((root/'copy/calls').glob('*.response.json'));x=json.loads(response.read_text());x['answer']={'ok':False};x['sha256']=digest(canonical({k:v for k,v in x.items() if k!='sha256'}));response.write_text(json.dumps(x))
            with self.assertRaisesRegex(ValueError,'Conflicting records'):collect(root)

    def test_unresolved_attempt_consumes_finite_budget_without_fabricated_failure(self):
        from runaway.decision_experiment import LimitedCalls
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);calls=LimitedCalls(root,1,lambda *a,**k:self.fail('must not invoke backend'))
            request={'prompt':'pending','schema':{},'model':'offline','system':SYSTEM};key=digest(canonical(request))
            write_once(root/'calls'/(key+'.request.json'),request)
            start_attempt(root/'calls'/(key+'.attempt.json'),key)
            with self.assertRaisesRegex(ValueError,'including unresolved attempts'):calls.call('different',{},'offline')
            self.assertFalse(list((root/'calls').glob('*.failure.json')))

    def test_normalized_copy_with_different_source_path_is_still_one_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/'first';folder.mkdir()
            Calls(folder,lambda *a,**k:('{"ok":true}',{'usage':[{'input_tokens':1,'output_tokens':2}]})).call('same',{},'offline')
            row=collect(root)[0];copy={**row,'artifacts':[{'path':'a-copied-location','bytes_sha256':row['artifacts'][0]['bytes_sha256']}]}
            r=summarize([row,copy]);self.assertEqual(r['execution_records'],1);self.assertEqual(r['known_usage']['total_tokens'],3);self.assertEqual(r['copied_artifacts_excluded'],1)

    def test_local_guard_block_is_not_a_remote_missing_usage_call(self):
        from runaway.decision_experiment import LimitedCalls
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def fail(*a,**k):raise ValueError('simulated transport error')
            calls=LimitedCalls(root,3,fail)
            with self.assertRaises(ValueError):calls.call('first',{},'offline')
            with self.assertRaises(ValueError):calls.call('blocked',{},'offline')
            r=summarize(collect(root));self.assertEqual(r['execution_records'],2);self.assertEqual(r['locally_blocked_before_backend'],1);self.assertEqual(r['executions_missing_usage'],1)


if __name__ == '__main__': unittest.main()
