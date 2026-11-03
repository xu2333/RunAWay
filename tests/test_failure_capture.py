"""Fake subprocess completions only: no CLI or model service."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from runaway import generation
spec=importlib.util.spec_from_file_location('failure_capture',Path(__file__).resolve().parents[1]/'scripts/capture_codex_failure.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class FailureCaptureTests(unittest.TestCase):
    def failed(self, result):
        def invoke():
            generation.run_bounded(['pinned-cli','exec'], 'PRIVATE_PROMPT', 180)
            raise ValueError('PRIVATE_ERROR')
        with patch.object(generation,'run_bounded',return_value=result) as bounded:
            with self.assertRaises(c.CapturedGenerationFailure) as caught:
                c.capture_once(invoke,model='fixed-model')
            bounded.assert_called_once_with(['pinned-cli','exec'],'PRIVATE_PROMPT',180)
        return caught.exception

    def test_nonzero_exit_preserved_without_private_streams_or_invented_usage(self):
        exc=self.failed(subprocess.CompletedProcess([],7,'PRIVATE_ANSWER','PRIVATE_SECRET'))
        self.assertEqual(exc.provenance['completion']['returncode'],7)
        self.assertIsNone(exc.provenance['usage'])
        self.assertFalse(exc.provenance['cause_established'])
        self.assertNotIn('PRIVATE',str(exc)+json.dumps(exc.provenance))

    def test_completed_usage_and_failed_events_survive_parser_failure(self):
        events=[{'type':'thread.started','thread_id':'a'*32},
                {'type':'turn.completed','usage':{'input_tokens':2,'output_tokens':3,'secret':'PRIVATE'}},
                {'type':'turn.failed','error':{'message':'PRIVATE'}},
                {'type':'item.completed','item':{'text':'PRIVATE'}}]
        exc=self.failed(subprocess.CompletedProcess([],0,'\n'.join(map(json.dumps,events)),''))
        self.assertEqual(exc.provenance['usage'],[{'input_tokens':2,'output_tokens':3}])
        self.assertEqual(exc.provenance['completion']['progress']['event_counts']['turn.failed'],1)
        self.assertNotIn('a'*32,json.dumps(exc.provenance))
        self.assertNotIn('PRIVATE',json.dumps(exc.provenance))
        self.assertFalse(exc.provenance['partial_answer_accepted'])

    def test_existing_timeout_is_not_replaced_or_retried(self):
        exc=generation.GenerationTimeout({'usage':None,'cleanup':'group_kill'})
        with patch.object(generation,'run_bounded',side_effect=exc) as bounded:
            with self.assertRaises(generation.GenerationTimeout) as caught:
                c.capture_once(lambda:generation.run_bounded([], '',180),model='fixed-model')
        self.assertIs(caught.exception,exc);bounded.assert_called_once()

    def test_success_and_arguments_unchanged(self):
        result=subprocess.CompletedProcess([],0,'','')
        with patch.object(generation,'run_bounded',return_value=result) as bounded:
            got=c.capture_once(lambda:generation.run_bounded(['exact'],'data',timeout=17),model='fixed-model')
        self.assertIs(got,result);bounded.assert_called_once_with(['exact'],'data',timeout=17)

    def test_prechild_failure_does_not_invent_completion(self):
        exc=PermissionError('gate')
        def invoke():raise exc
        with self.assertRaises(PermissionError)as caught:c.capture_once(invoke,model='fixed-model')
        self.assertIs(caught.exception,exc)

    def test_patch_restored_after_failure(self):
        original=generation.run_bounded
        self.failed(subprocess.CompletedProcess([],1,'',''))
        self.assertIs(generation.run_bounded,original)

if __name__=='__main__':unittest.main()
