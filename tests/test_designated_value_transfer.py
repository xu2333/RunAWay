import json
import runpy
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

STUDY = Path(__file__).resolve().parents[1] / 'benchmarks/designated-value-transfer-v1'


class BranchTransferTest(unittest.TestCase):
    def test_disclosure_and_independent_reads(self):
        run = runpy.run_path(str(STUDY / 'compare.py'))
        materials = json.loads(subprocess.check_output(['node', STUDY / 'materials.mjs', 'requests'], text=True))
        old = materials['original']
        self.assertTrue(materials['current'].endswith(old))
        added = materials['current'][:-len(old)]
        signed, unsigned = (materials['tasks'][key] for key in ('signed', 'unsigned'))
        self.assertEqual(signed.replace('已签发', '未签发'), unsigned)
        self.assertIn('雾铃邮差', old.split('SOURCE_JSON:')[1])
        for literal in ('雾铃邮差', '桥下回声', '值班台', '音头'):
            self.assertNotIn(literal, added)
        for task in (signed, unsigned):
            self.assertNotIn('雾铃邮差', task)
            self.assertNotIn(task, old)
        schedule = list(run['reads']())
        self.assertEqual(Counter((card, branch) for card, branch, _ in schedule),
                         Counter({(card, branch): 2 for card in run['ORDER'] for branch in materials['tasks']}))
        self.assertEqual(len(set(schedule)), 16)

    def test_joint_score_rejects_wrong_fallback_and_displaced_edit(self):
        score = runpy.run_path(str(STUDY / 'score.py'))['score']
        correct = dict(素材名='桥下回声', 起点秒=4, 终点秒=12, 倍速=1)
        check = lambda row: score(json.dumps(row, ensure_ascii=False), 'unsigned')
        self.assertTrue(check(correct)['joint'])
        for change, field in ((dict(素材名='雾铃邮差'), 'selected_name'),
                              (dict(起点秒=0, 终点秒=8), 'retained_tail'),
                              (dict(倍速=1.5), 'original_speed'), (dict(倍速=True), 'original_speed')):
            result = check({**correct, **change})
            self.assertFalse(result[field])
            self.assertFalse(result['joint'])
        duplicate = json.dumps(correct, ensure_ascii=False)[:-1] + ', "倍速":1}'
        self.assertFalse(score(duplicate, 'unsigned')['joint'])

    def test_closed_early_keeps_all_scheduled_rows_and_disallows_reentry(self):
        run = runpy.run_path(str(STUDY / 'compare.py'))
        report = runpy.run_path(str(STUDY / 'score.py'))['report']
        def fail_extraction(*args, **kwargs):
            raise ValueError('fixture')
        with tempfile.TemporaryDirectory() as temp, patch.dict(run['prior'], codex_generate=fail_extraction):
            dest = Path(temp) / 'run'
            with self.assertRaisesRegex(ValueError, 'fixture'):
                run['run'](dest)
            self.assertEqual(json.loads((dest / 'closed.json').read_text())['failed_stage'], 'original-1')
            results = report(dest)
            self.assertEqual(len(results), 4)
            self.assertEqual(sum(x is None for c in results.values() for x in c['reads'].values()), 16)
            with self.assertRaises(FileExistsError):
                run['run'](dest)
