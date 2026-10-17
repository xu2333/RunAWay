import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

from runaway.generation import run_bounded, GenerationTimeout, progress_metadata
from runaway.selfplay import Calls


class GenerationDiagnosticsTests(unittest.TestCase):
    def test_timeout_keeps_sanitized_progress_unknown_usage_and_cannot_retry(self):
        code = ('import time,json; '
                'print(json.dumps({"type":"thread.started","thread_id":"01234567-abcd-0123-abcd-012345678901"}),flush=True); '
                'print(json.dumps({"type":"item.completed","item":{"type":"reasoning","text":"PRIVATE-TEXT"}}),flush=True); '
                'time.sleep(10)')
        with tempfile.TemporaryDirectory() as d:
            invocations=[]
            def generate(*a,**kw):
                invocations.append(1); return run_bounded([sys.executable,'-c',code],'',.2)
            calls=Calls(Path(d),generate)
            with self.assertRaises(GenerationTimeout):calls.call('private prompt',{},'mock')
            with self.assertRaisesRegex(ValueError,'not retried'):calls.call('private prompt',{},'mock')
            failure=json.loads(next((Path(d)/'calls').glob('*.failure.json')).read_text())
            progress=failure['provenance']['progress']
            self.assertIsNone(progress['usage']);self.assertEqual(progress['usage_status'],'unknown')
            self.assertEqual(progress['event_counts']['thread.started'],1)
            self.assertEqual(len(progress['observed_cli_thread_ids']),1)
            self.assertNotIn('PRIVATE-TEXT',json.dumps(failure));self.assertNotIn('private prompt',json.dumps(failure))
            self.assertEqual(len(invocations),1)

    @unittest.skipUnless(os.name=='posix','isolated process groups require POSIX')
    def test_descendant_inheriting_output_cannot_hold_cleanup_open(self):
        # Fake local child only: no Codex, network, credentials or model involved.
        code='import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(10)"])'
        started=time.monotonic()
        with self.assertRaises(GenerationTimeout) as caught:
            run_bounded([sys.executable,'-c',code],'',.2)
        self.assertLess(time.monotonic()-started,3)
        self.assertEqual(caught.exception.provenance['cleanup'],'group_kill')

    def test_completed_usage_is_observed_even_when_later_stream_stalls(self):
        progress=progress_metadata(json.dumps({'type':'turn.completed','usage':{'input_tokens':12,'output_tokens':3,'secret':'hidden'}})+'\n', 'private error')
        self.assertEqual(progress['usage'],[{'input_tokens':12,'output_tokens':3}])
        self.assertNotIn('secret',json.dumps(progress));self.assertNotIn('private error',json.dumps(progress))
        result=run_bounded([sys.executable,'-c','import sys; print(sys.stdin.read())'],'中文',2)
        self.assertEqual(result.returncode,0);self.assertEqual(result.stdout,'中文\n')


if __name__=='__main__': unittest.main()
