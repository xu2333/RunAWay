"""Post-hoc specificity denominators, request comparability and evidence guards."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('specificity_test', ROOT / 'scripts/audit_memory_specificity.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture():
    rows, responses = [], {}
    for person, choice in (('one', 'A choice'), ('two', 'B choice')):
        values = {}
        for case, gold in (('opposite', choice), ('shared', 'same choice'), ('unknown', 'U')):
            ids = [case + '_ab', case + '_ba']
            rows.append(dict(person=person, case=case, query_ids=ids, gold=gold))
            values.update({q: gold for q in ids})
        for generation in (0, 1):
            for repeat in (0, 1):
                responses[person, generation, repeat] = dict(values)
    return rows, responses, ('one', 'two')


class MemorySpecificityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        before = {name: (ROOT / 'benchmarks' / config[0] / 'measured.synthetic.json').read_bytes()
                  for name, config in m.STUDIES.items()}
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service')) as backend:
            cls.actual = {name: m.audit(name) for name in m.STUDIES}
            backend.assert_not_called()
        for name, value in before.items():
            if (ROOT / 'benchmarks' / m.STUDIES[name][0] / 'measured.synthetic.json').read_bytes() != value:
                raise AssertionError('Original evidence changed')

    def test_actual_fresh_contrast_and_shared_unknowns_stay_separate(self):
        result = self.actual['fresh']['subsets']['all']
        self.assertEqual(result['own']['all'], dict(total=64, correct=64, missing=0))
        self.assertEqual(result['other_card_rescore']['all'], dict(total=192, correct=96, missing=0))
        self.assertEqual(result['other_card_rescore']['known'], dict(total=144, correct=48, missing=0))
        self.assertEqual(result['other_card_rescore']['unknown'], dict(total=48, correct=48, missing=0))
        self.assertEqual(result['other_card_rescore']['contrast_known'], dict(total=96, correct=0, missing=0))
        self.assertEqual(result['own_on_unique_contrast'], dict(total=48, correct=48, missing=0))

    def test_actual_partial_primary_does_not_pool_complete_anchors(self):
        result = self.actual['partial']['subsets']
        primary = result['primary']
        self.assertEqual(primary['other_card_rescore']['all'], dict(total=144, correct=112, missing=0))
        self.assertEqual(primary['other_card_rescore']['contrast_known'], dict(total=32, correct=0, missing=0))
        self.assertEqual(primary['own_on_unique_contrast'], dict(total=16, correct=16, missing=0))
        self.assertEqual(result['anchors']['own']['all']['total'], 16)
        self.assertEqual(result['all']['other_card_rescore']['all'], dict(total=192, correct=128, missing=0))
        for study in self.actual.values():
            self.assertEqual(study['reused_card_reader_records'], 16)
            self.assertTrue(study['original_replay_verified'])
            self.assertFalse(study['new_independent_trials'])
            self.assertFalse(study['recipient_identity_routing_verified'])
            self.assertEqual(study['new_model_calls'], 0)

    def test_shared_choices_and_unknowns_do_not_count_as_person_contrast(self):
        result = m.matrix(*fixture())
        other = result['other_card_rescore']
        self.assertEqual(other['all'], dict(total=6, correct=4, missing=0))
        self.assertEqual(other['contrast_known'], dict(total=2, correct=0, missing=0))
        self.assertEqual(result['contrast_unique_recipient_cases'], 2)
        self.assertEqual(result['own_on_unique_contrast']['correct'], 2)
        self.assertEqual(result['ordered_mismatched_pairs'], 2)

    def test_one_wrong_order_or_missing_answer_fails_the_planned_case(self):
        rows, answers, profiles = fixture()
        answers['one', 1, 1]['opposite_ba'] = 'B choice'
        del answers['two', 0, 0]['unknown_ab']
        result = m.matrix(rows, answers, profiles)
        self.assertEqual(result['own']['all'], dict(total=6, correct=4, missing=1))
        self.assertEqual(result['own']['unknown'], dict(total=2, correct=1, missing=1))
        missing = next(c for c in result['cells'] if c['recipient'] == c['donor'] == 'two' and c['case'] == 'unknown')
        self.assertIsNone(missing['answers_by_parent'][0][0])

    def test_duplicate_foreign_and_misaligned_references_are_refused(self):
        rows, answers, profiles = fixture()
        variants = [rows + [rows[0]], [{**r, 'person': 'foreign'} if i == 0 else r for i, r in enumerate(rows)],
                    rows[:-1], [{**r, 'query_ids': ['changed_ab', 'changed_ba']} if i == 0 else r for i, r in enumerate(rows)]]
        for changed in variants:
            with self.assertRaises(ValueError):
                m.matrix(changed, answers, profiles)
        with self.assertRaises(ValueError):
            m.matrix([], {}, profiles)

    def test_contract_allows_only_the_exact_parent_material_to_differ(self):
        queries = [dict(id='q', scenario='same question', options=dict(A='a', B='b'))]
        parents = {('one', 0): 'first card', ('two', 0): 'second card'}
        records = [dict(profile=p, generation_repeat=0, request=dict(model='fixed', system='same system', schema={},
                    prompt='same prefix\nREADER_INPUT_JSON:\n' + json.dumps(dict(material=text, queries=queries))))
                   for (p, _), text in parents.items()]
        self.assertEqual(len(m.common_contract(records, queries, parents)), 64)
        for fault in ('model', 'system', 'schema', 'prefix', 'material', 'queries', 'extra_payload'):
            changed = copy.deepcopy(records)
            request = changed[0]['request']
            if fault in ('model', 'system', 'schema'):
                request[fault] = 'recipient-specific'
            elif fault == 'prefix':
                request['prompt'] = 'recipient-specific' + request['prompt']
            else:
                prefix, raw = request['prompt'].split('\nREADER_INPUT_JSON:\n')
                payload = json.loads(raw)
                if fault == 'extra_payload': payload['recipient'] = 'one'
                else: payload[fault] = 'changed'
                request['prompt'] = prefix + '\nREADER_INPUT_JSON:\n' + json.dumps(payload)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                m.common_contract(changed, queries, parents)

    def test_modified_evidence_is_rejected_before_any_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'benchmarks/fresh-decision-v1/measured.synthetic.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"changed":true}')
            with patch.object(m, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Pinned original evidence changed'):
                m.audit('fresh')

    def test_own_and_off_diagonal_cells_preserve_every_recipient_case(self):
        for study in self.actual.values():
            for subset in study['subsets'].values():
                cells = subset['cells']
                self.assertEqual(len(cells), subset['own']['all']['total'] * 4)
                self.assertEqual(len(subset['matrix']), 16)
                self.assertEqual(subset['ordered_mismatched_pairs'], 12)
                self.assertTrue(all(len(c['answers_by_parent']) == 2 and all(len(g) == 4 for g in c['answers_by_parent']) for c in cells))
                self.assertEqual(subset['other_card_rescore']['all']['total'], subset['own']['all']['total'] * 3)


if __name__ == '__main__':
    unittest.main()
