import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from runaway import temporal_stress as stress, temporal_concise as codec, generation

ROOT=Path(__file__).resolve().parents[1]


class PartialContextCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report,cls.world,cls.memories=stress.calibrate()

    def test_authored_transition_table_distinguishes_missing_false_and_restore_times(self):
        for member in (0,1):
            self.assertEqual(stress.gold(5,None,False,member),('U','context_unknown',False))
            self.assertEqual(stress.gold(5,False,None,member),('0','chosen',False))
            self.assertEqual(stress.gold(7,True,True,member),(str(1-member),'chosen',False))
            self.assertEqual(stress.gold(8,True,True,member),(str(member),'chosen',True))
            self.assertEqual(stress.gold(9,True,True,member),('U','unobserved',False))
            self.assertEqual(stress.gold(10,True,True,member),(str(member),'chosen',True))
            self.assertEqual(stress.gold(11,False,None,member),('U','conflict',False))
            self.assertEqual(stress.gold(12,False,None,member),('0','chosen',False))
            self.assertEqual(stress.gold(6,True,None,member),('U','context_unknown',False))
        self.assertTrue(all('未提供' in c['public']['question'] for p in self.world['people'] for c in p['cases'] if len(c['context'])<2))

    def test_fixed_denominators_and_control_losses_are_reproducible_not_model_samples(self):
        r=self.report;self.assertTrue(r['passed']);self.assertEqual(r['graph_truth_table_checks'],432)
        self.assertEqual(r['paired_statistical_units'],1);self.assertFalse(r['model_quality_measured'])
        for row in r['controls'].values():
            self.assertEqual([row['scores'][k]['planned'] for k in ('current_choice','historical_reconstruction','joint')],[36,396,432])
            self.assertEqual(row['scores']['current_choice']['current_scenarios_option_orders_collapsed']['planned'],18)
            self.assertEqual(row['scores']['current_choice']['matched_domain_contrasts']['planned'],1)
        wrong=r['controls']['wrong_person']['scores']['current_choice']
        self.assertEqual(wrong['matched_domain_contrasts']['correct'],0)
        self.assertEqual(wrong['correct'],28)
        self.assertEqual(r['controls']['delete_hard']['scores']['current_choice']['hard_constraints']['observed_violations'],4)
        self.assertEqual(r['controls']['missing_snapshot']['scores']['joint']['missing'],36)
        self.assertEqual(r['controls']['wrong_cutoff']['scores']['current_choice']['correct'],36)
        self.assertEqual(r['controls']['wrong_cutoff']['scores']['historical_reconstruction']['correct'],360)

    def test_action_only_and_complete_context_only_false_passes_have_explicit_witnesses(self):
        wrong=self.report['controls']['assume_missing_false'];erased=self.report['controls']['erase_conflict']
        self.assertEqual(wrong['context_slices']['complete_context'],dict(correct=192,planned=192))
        self.assertEqual(wrong['context_slices']['partial_context'],dict(correct=148,planned=240))
        self.assertEqual(wrong['counterexamples'][0]['gold_status'],'context_unknown')
        self.assertEqual(wrong['counterexamples'][0]['predicted_status'],'chosen')
        self.assertEqual(erased['scores']['joint']['correct'],432)
        self.assertEqual(erased['state_scores']['joint']['correct'],420)
        e=erased['counterexamples'][0]
        self.assertEqual((e['gold_answer'],e['prediction'],e['gold_status'],e['predicted_status']),('U','U','conflict','unobserved'))
        current=self.report['controls']['current_only']
        self.assertEqual(current['scores']['historical_reconstruction']['correct'],136)
        self.assertEqual(current['state_scores']['historical_reconstruction']['correct'],0)
        self.assertEqual(current['scores']['historical_reconstruction']['missing'],0)

    def test_whole_payload_lengths_include_wrapper_and_all_snapshot_grammars(self):
        for name,memories in self.memories.items():
            for pid,text in memories.items():
                lengths=self.report['controls'][name]['whole_memory_lengths'][pid]
                self.assertEqual(lengths,dict(characters=len(text),utf8_bytes=len(text.encode()),actual_tokens=None))
                value=json.loads(text);self.assertEqual(value['note'],stress.BUNDLE_NOTE)
                if name not in ('current_only','missing_snapshot'):self.assertEqual(len(value['snapshots']),12)
                for snapshot in value.get('snapshots',{}).values():
                    self.assertTrue(snapshot.startswith(codec.HEADER));codec.decode(snapshot)
        self.assertGreater(self.report['controls']['timestamped_snapshots']['whole_memory_lengths']['partial-0']['characters'],self.report['controls']['current_only']['whole_memory_lengths']['partial-0']['characters'])

    def test_saved_public_fixture_replays_without_service_or_token_estimation(self):
        with patch.object(generation,'codex_generate',side_effect=AssertionError('No service calls')):
            actual,world,memories=stress.calibrate()
        base=ROOT/'examples/temporal-partial-context'
        stored=json.loads((base/'report.synthetic.json').read_text());stored['tokenizer']=actual['tokenizer']
        for source in stored['source_lengths'].values():
            for lengths in source.values():lengths['actual_tokens']=None
        for row in stored['controls'].values():
            for lengths in row['whole_memory_lengths'].values():lengths['actual_tokens']=None
        self.assertEqual(stored,actual)
        self.assertEqual(json.loads((base/'world.synthetic.json').read_text()),world)
        self.assertEqual(json.loads((base/'memories.synthetic.json').read_text()),memories)
        with tempfile.TemporaryDirectory() as temporary:
            saved=stress.save(Path(temporary)/'new');self.assertEqual(saved,actual)
            with self.assertRaises(FileExistsError):stress.save(Path(temporary)/'new')
        with self.assertRaises(ValueError):stress.calibrate(count=lambda _:None)


if __name__=='__main__':unittest.main()
