"""Damage controls for the separately measured repeat;no inference or new labels."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('single_repeat_measured_test', ROOT / 'scripts/replay_single_pass_repeat.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
EXPECTED = {'actual_original_attempts': 45, 'actual_original_children': 45, 'missing_original_usage': 0, 'unused_slots_expire': 0, 'known_original_usage': {'input_tokens': 511725, 'output_tokens': 26385, 'cached_input_tokens': 101376, 'cache_write_input_tokens': 0, 'reasoning_output_tokens': 3026, 'total_tokens': 538110}, 'joint': {'card': {'joint': {'planned': 64, 'correct': 64, 'missing': 0}, 'known': {'planned': 24, 'correct': 24, 'missing': 0}, 'unknown': {'planned': 40, 'correct': 40, 'missing': 0}, 'personal_known': {'planned': 24, 'correct': 24, 'missing': 0}, 'preference': {'planned': 60, 'correct': 60, 'missing': 0}, 'execution': {'planned': 4, 'correct': 4, 'missing': 0}, 'untyped': {'planned': 0, 'correct': 0, 'missing': 0}}, 'tail': {'joint': {'planned': 64, 'correct': 48, 'missing': 0}, 'known': {'planned': 24, 'correct': 8, 'missing': 0}, 'unknown': {'planned': 40, 'correct': 40, 'missing': 0}, 'personal_known': {'planned': 24, 'correct': 8, 'missing': 0}, 'preference': {'planned': 60, 'correct': 44, 'missing': 0}, 'execution': {'planned': 4, 'correct': 4, 'missing': 0}, 'untyped': {'planned': 0, 'correct': 0, 'missing': 0}}}, 'per_generation': {'0': {'card': {'joint': {'planned': 64, 'correct': 64, 'missing': 0}, 'known': {'planned': 24, 'correct': 24, 'missing': 0}, 'unknown': {'planned': 40, 'correct': 40, 'missing': 0}, 'personal_known': {'planned': 24, 'correct': 24, 'missing': 0}, 'preference': {'planned': 60, 'correct': 60, 'missing': 0}, 'execution': {'planned': 4, 'correct': 4, 'missing': 0}, 'untyped': {'planned': 0, 'correct': 0, 'missing': 0}}, 'tail': {'joint': {'planned': 64, 'correct': 48, 'missing': 0}, 'known': {'planned': 24, 'correct': 8, 'missing': 0}, 'unknown': {'planned': 40, 'correct': 40, 'missing': 0}, 'personal_known': {'planned': 24, 'correct': 8, 'missing': 0}, 'preference': {'planned': 60, 'correct': 44, 'missing': 0}, 'execution': {'planned': 4, 'correct': 4, 'missing': 0}, 'untyped': {'planned': 0, 'correct': 0, 'missing': 0}}}, '1': {'card': {'joint': {'planned': 64, 'correct': 64, 'missing': 0}, 'known': {'planned': 24, 'correct': 24, 'missing': 0}, 'unknown': {'planned': 40, 'correct': 40, 'missing': 0}, 'personal_known': {'planned': 24, 'correct': 24, 'missing': 0}, 'preference': {'planned': 60, 'correct': 60, 'missing': 0}, 'execution': {'planned': 4, 'correct': 4, 'missing': 0}, 'untyped': {'planned': 0, 'correct': 0, 'missing': 0}}, 'tail': {'joint': {'planned': 64, 'correct': 48, 'missing': 0}, 'known': {'planned': 24, 'correct': 8, 'missing': 0}, 'unknown': {'planned': 40, 'correct': 40, 'missing': 0}, 'personal_known': {'planned': 24, 'correct': 8, 'missing': 0}, 'preference': {'planned': 60, 'correct': 44, 'missing': 0}, 'execution': {'planned': 4, 'correct': 4, 'missing': 0}, 'untyped': {'planned': 0, 'correct': 0, 'missing': 0}}}}, 'characters': [439, 542, 519, 448, 454, 473, 508, 457]}


class SinglePassRepeatEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = r.p.read(r.DEFAULT)

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError, TypeError, AssertionError)):
            r.replay(data)

    def test_measured_counts_keep_all_generations_missing_and_reported_usage(self):
        self.assertIsNotNone(EXPECTED)
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            out = r.check()
        backend.assert_not_called()
        for key in ('actual_original_attempts', 'actual_original_children', 'missing_original_usage', 'unused_slots_expire'):
            self.assertEqual(out[key], EXPECTED[key])
        self.assertEqual(out['known_original_usage'], EXPECTED['known_original_usage'])
        self.assertEqual(out['summary']['joint'], EXPECTED['joint'])
        self.assertEqual(out['summary']['per_generation'], EXPECTED['per_generation'])
        self.assertEqual([card['characters'] for card in out['cards']], EXPECTED['characters'])
        self.assertEqual(out['summary']['planned_unique_person_cases_per_view'], 64)
        self.assertEqual(out['summary']['joint_answers_per_case'], 8)
        self.assertEqual(out['summary']['fictional_people'], 4)
        self.assertEqual(sum(s['actual_calls'] for s in out['usage_by_stage'].values()), out['actual_original_attempts'])
        self.assertEqual(sum(s['known_total_tokens'] for s in out['usage_by_stage'].values()), out['known_original_usage']['total_tokens'])

    def test_prepared_source_reference_questions_and_dependency_versions_are_fixed(self):
        for name in ('sources.json', 'reference.private.json', 'queries.public.json',
                     'author-evidence.private.json', 'implementation-sha256.json'):
            data = copy.deepcopy(self.data)
            data['prepared_files'][name] = {}
            self.reject(data)
        for field in ('input_manifest_sha256', 'scientific_source_ref'):
            data = copy.deepcopy(self.data)
            data[field] = 'foreign'
            self.reject(data)

    def test_identical_request_does_not_allow_relabeling_another_generation(self):
        data = copy.deepcopy(self.data)
        rec = next(x for x in data['records'] if x['kind'] == 'extract')
        rec['generation_repeat'] = 1 - rec['generation_repeat']
        rec['execution_record']['generation_repeat'] = rec['generation_repeat']
        self.reject(data)
        data = copy.deepcopy(self.data)
        rec = next(x for x in data['records'] if x['kind'] == 'read')
        rec['read_repeat'] = 1 - rec['read_repeat']
        rec['execution_record']['read_repeat'] = rec['read_repeat']
        self.reject(data)

    def test_raw_graph_and_public_card_cannot_be_manually_repaired(self):
        for fault in ('raw', 'graph', 'card'):
            data = copy.deepcopy(self.data)
            rec = next(x for x in data['records'] if x['artifact'] is not None)
            if fault == 'raw':
                rec['raw'] += 'changed'
            elif fault == 'graph':
                value = r.e.parse_answer(rec['raw'])
                value['name'] = '人工替换'
                rec['raw'] = json.dumps(value, ensure_ascii=False)
                rec['raw_value_sha256'] = r.p.digest(rec['raw'])
            else:
                rec['artifact']['prompt'] += '人工补充'
            self.reject(data)

    def test_own_character_matched_tail_cannot_be_replaced_by_a_card(self):
        data = copy.deepcopy(self.data)
        tail = next(x for x in data['records'] if x['kind'] == 'read' and x['view'] == 'tail')
        card = next(x for x in data['records'] if x['kind'] == 'read' and x['view'] == 'card'
                    and x['profile'] == tail['profile'] and x['generation_repeat'] == tail['generation_repeat'])
        tail['request'] = copy.deepcopy(card['request'])
        tail['request_sha256'] = r.p.digest(tail['request'])
        tail['execution_record']['request_sha256'] = tail['request_sha256']
        self.reject(data)

    def test_one_answer_cannot_be_changed_while_preserving_a_successful_endpoint(self):
        data = copy.deepcopy(self.data)
        rec = next(x for x in data['records'] if x['kind'] == 'read' and x['view'] == 'card')
        row = next(x for x in r.p.inputs()['rows'] if x['person'] == rec['profile'] and x['gold'] != 'U')
        answers = r.e.parse_answer(rec['raw'])
        q = row['query_ids'][1]
        answers[q] = row['gold'] if answers[q] == 'U' else 'U'
        rec['raw'] = json.dumps(answers, ensure_ascii=False)
        rec['raw_value_sha256'] = r.p.digest(rec['raw'])
        self.reject(data)

    def test_joint_denominator_cannot_be_shrunk_or_hidden_by_one_generation(self):
        for fault in ('joint', 'generation', 'closed'):
            data = copy.deepcopy(self.data)
            if fault == 'joint':
                data['status']['scores']['joint']['card']['joint']['planned'] -= 1
            elif fault == 'generation':
                data['status']['scores']['per_generation']['0']['card']['joint']['correct'] -= 1
            else:
                data['status']['scope_closed'] = False
            self.reject(data)

    def test_usage_attempts_and_child_ledger_cannot_be_rewritten(self):
        for fault in ('usage', 'attempt', 'child'):
            data = copy.deepcopy(self.data)
            if fault == 'usage':
                data['status']['known_usage']['total_tokens'] += 1
            elif fault == 'attempt':
                data['status']['attempt_reservations'] -= 1
            else:
                data['records'][0]['local_cli_child_intent'] = False
            self.reject(data)

    def test_two_synthetic_generations_do_not_certify_population_or_real_user_fidelity(self):
        for field in r.FALSE_CLAIMS:
            data = copy.deepcopy(self.data)
            data[field] = True
            self.reject(data)
        data = copy.deepcopy(self.data)
        data['host_authorization'] = 'Private fields are never accepted'
        self.reject(data)
        data = copy.deepcopy(self.data)
        data['records'][0]['provider_credentials'] = 'Private fields are never accepted'
        self.reject(data)


if __name__ == '__main__':
    unittest.main()
