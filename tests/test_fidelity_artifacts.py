import json
from pathlib import Path
import unittest

from runaway import fidelity_stress as fs

ROOT=Path(__file__).resolve().parents[1]


class PublishedDevelopmentTests(unittest.TestCase):
    def test_sealed_development_calibration_replays_and_has_no_model_claim(self):
        base=ROOT/'examples/fidelity-stress'
        world=json.loads((base/'fixtures.synthetic.json').read_text())
        stored=json.loads((base/'calibration.synthetic.json').read_text())
        summary=json.loads((base/'summary.synthetic.json').read_text())
        self.assertEqual(world['purpose'],'development')
        self.assertEqual(world['origin'],'fully_synthetic')
        computed=fs.calibrate(world)
        # Summing display ratios differs by a few ULPs across Python versions.
        # Only this derived mean allows a tiny absolute tolerance. Counts, raw
        # ratios, errors, contrasts and every other field still compare exactly.
        for name,tasks in computed['controls'].items():
            for task,row in tasks.items():
                wanted=stored['controls'][name][task]['macro_cluster_accuracy']
                self.assertAlmostEqual(row['macro_cluster_accuracy'],wanted,delta=1e-12)
                row['macro_cluster_accuracy']=wanted
        self.assertEqual(computed,stored)
        self.assertEqual(summary['paired_clusters'],6)
        self.assertEqual(summary['people'],12)
        self.assertEqual(summary['external_model_calls'],0)
        self.assertFalse(summary['model_quality_measured'])
        self.assertFalse(summary['real_person_fidelity_verified'])
        self.assertEqual(summary['future_proposal']['status'],'not_approved_not_executed')
        self.assertEqual({p.name for p in base.iterdir()},{'fixtures.synthetic.json','calibration.synthetic.json','summary.synthetic.json'})


if __name__=='__main__':unittest.main()
