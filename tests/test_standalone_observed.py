"""Recorded ablation source/checkpoint consistency, with zero new service calls."""
import copy
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('standalone_latent_checker_test',ROOT/'benchmarks/standalone-latent-v1/check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)

class StandaloneObservedTests(unittest.TestCase):
 def test_actual_recorded_ablation_and_original_cards_reproduce(self):
  data=check.s.read(ROOT/'benchmarks/standalone-latent-v1/observed.synthetic.json');r=check.validate(data);self.assertGreater(r['actual_calls'],0);self.assertLessEqual(r['actual_calls'],19);self.assertEqual(check.verify_exports(data)['unchanged_portable_cards_verified'],6)
 def test_adding_decoder_back_or_repairing_card_is_rejected(self):
  data=check.s.read(ROOT/'benchmarks/standalone-latent-v1/observed.synthetic.json');bad=copy.deepcopy(data);record=bad['executions'][0];request=check.s.request_for(data['world'],record['group'],record['person'],data['products']);request['prompt']=data['world']['decoder_contract']+request['prompt'];record['request_id']=check.s.digest(check.s.canonical(request))
  with self.assertRaisesRegex(ValueError,'request'):check.validate(bad)
  bad=copy.deepcopy(data);bad['products']['u06k']['prompt.md']+='rule definition appended'
  with self.assertRaisesRegex(ValueError,'products'):check.validate(bad)

if __name__=='__main__':unittest.main()
