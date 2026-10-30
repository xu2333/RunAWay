"""Local wire compatibility only; no claim about model generation or fidelity."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('when_wire_candidate_test', ROOT / 'benchmarks/wire-contract-v1/candidate.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
spec = importlib.util.spec_from_file_location('when_wire_archive', ROOT / 'scripts/replay_compression_stability.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)
from runaway.constraint_extract import check, parse_answer


class WhenWireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archive.engine.plan.read(archive.DEFAULT)

    def test_only_when_length_constraints_change_not_source_prompt_or_binder(self):
        source = self.data['sources']['h68']
        original = candidate.base.make_request(source, 768)
        actual = candidate.make_request(source, 768)
        self.assertEqual(actual['prompt'], original['prompt'])
        expected = copy.deepcopy(original['schema'])
        field = expected['properties']['groups']['items']['properties']['rules']['items']['properties']['when']
        field.update(minLength=1, maxLength=120)
        self.assertEqual(actual['schema'], expected)

    def test_all10actually_valid_extractions_remain_wire_valid_and_render_identically(self):
        records = [r for r in self.data['records'] if 'card' in r]
        self.assertEqual(len(records), 10)
        for rec in records:
            source = self.data['sources'][rec['profile']]
            answer = parse_answer(rec['raw'])
            req = candidate.make_request(source, rec['budget'])
            check(answer, req['schema'])
            self.assertEqual(candidate.bind(answer, source, rec['budget'])['prompt.md'], rec['card']['prompt'])

    def test_observed_empty_when_was_wire_valid_but_candidate_rejects_without_repair(self):
        rec = next(r for r in self.data['records'] if r['slot'] == 6)
        source, answer = self.data['sources']['h68'], parse_answer(rec['raw'])
        before = copy.deepcopy(answer)
        check(answer, candidate.base.make_request(source, 768)['schema'])
        self.assertTrue(any(rule['when'] == '' for g in answer['groups'] for rule in g['rules']))
        with self.assertRaises(ValueError):
            check(answer, candidate.make_request(source, 768)['schema'])
        self.assertEqual(answer, before)

    def test_wire_alignment_does_not_fix_the806character_product_or_whitespace(self):
        rec = next(r for r in self.data['records'] if r['slot'] == 15)
        source, answer = self.data['sources']['h68'], parse_answer(rec['raw'])
        req = candidate.make_request(source, 768)
        check(answer, req['schema'])
        with self.assertRaises(ValueError):
            candidate.bind(answer, source, 768)
        altered = copy.deepcopy(answer)
        altered['groups'][0]['rules'][0]['when'] = ' '
        check(altered, req['schema'])
        with self.assertRaises(ValueError):
            candidate.bind(altered, source, 768)


if __name__ == '__main__':
    unittest.main()
