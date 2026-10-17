import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from runaway.card import canonical,digest
from runaway.execution_ledger import collect,summarize
from runaway.metric_jobs import score_trials
from runaway.selfplay import SYSTEM
from runaway.synthetic_metric import score_external


ROOT=Path(__file__).resolve().parents[1]


class PilotEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        with zipfile.ZipFile(ROOT/'examples/pilot-evidence.synthetic.zip') as archive:
            for name in archive.namelist():
                path=Path(name)
                if path.is_absolute() or '..' in path.parts:raise AssertionError('Unsafe archive path')
            archive.extractall(cls.root)
        cls.replay=cls.root/'d0015'

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_manifest_and_no_approval_auth_or_real_workspace_artifacts(self):
        manifest=json.loads((self.replay/'manifest.json').read_text())
        for name,want in manifest.items():
            self.assertEqual(hashlib.sha256((self.replay/name).read_bytes()).hexdigest(),want)
            self.assertNotIn('central-agent',name);self.assertNotIn('auth.json',name);self.assertNotIn('unit-plan',name)
        summary=json.loads((self.replay/'report.synthetic.json').read_text())
        self.assertEqual(summary,json.loads((ROOT/'examples/pilot-results.synthetic.json').read_text()))
        self.assertEqual(summary['origin'],'fully_synthetic')
        world=json.loads((self.replay/'metric/world.private.json').read_text());self.assertEqual(world['origin'],'fully_synthetic')

    def test_raw_predictions_reproduce_all_four_degenerate_results(self):
        answers=json.loads((self.replay/'decoder-answers.synthetic.json').read_text())
        self.assertEqual(len(answers),8);self.assertEqual(sum(len(a) for a in answers.values()),192)
        self.assertTrue(all(v=='U' for a in answers.values() for v in a.values()))
        scored=score_trials(self.replay/'metric',self.replay/'trials.private.json',answers)
        for row in scored['rows']:
            q=row['quality'];self.assertEqual((q['correct'],q['planned'],q['missing']),(4,48,0))
            self.assertEqual(q['hard_constraints']['abstentions'],4)
            self.assertEqual(q['hard_constraints']['observed_violations'],0)
            self.assertEqual(q['matched_person_disagreements']['correct'],0)

    def test_raw_service_records_reproduce_controls_and_exact_usage(self):
        jobs=[json.loads(line) for line in (self.replay/'control-reader-jobs.synthetic.jsonl').read_text().splitlines()]
        predictions={}
        for job in jobs:
            request={k:job[k] for k in ('prompt','schema','model')}|{'system':SYSTEM}
            key=digest(canonical(request));response=json.loads((self.replay/'calls'/(key+'.response.json')).read_text())
            predictions.setdefault(job['condition'],{})[job['persona_id']]=response['answer']
        for condition,correct in [('full_history',48),('none',4),('wrong_person_history',42),('delete_exception_history',43)]:
            q=score_external(self.replay/'metric',predictions[condition]);self.assertEqual((q['correct'],q['planned']),(correct,48))
        report=summarize(collect(self.replay));self.assertEqual(report['execution_records'],24)
        self.assertEqual(report['outcomes'],{'completed':24});self.assertEqual(report['executions_missing_usage'],0)
        self.assertEqual(report['known_usage']['input_tokens'],207514)
        self.assertEqual(report['known_usage']['output_tokens'],14575)
        self.assertEqual(report['known_usage']['total_tokens'],222089)


if __name__=='__main__':unittest.main()
