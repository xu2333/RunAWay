"""Actual closed archive integrity and source/card diagnostics;zero new calls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


r = load('pressure_actual_evidence', ROOT / 'scripts/replay_guard_pressure.py')
t = load('pressure_actual_trace', ROOT / 'scripts/inspect_guard_pressure.py')


class GuardPressureEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = r.p.read(r.DEFAULT)
        with patch('runaway.generation.codex_generate', side_effect=AssertionError('No service during replay')) as backend:
            cls.report = r.check()
        backend.assert_not_called()

    def reject(self, data):
        with self.assertRaises((ValueError, KeyError, TypeError, AssertionError)): r.replay(data)

    def test_closed_archive_rebuilds164_fixed_cases_and_four_answers_usage_and_counters(self):
        report = self.report
        self.assertEqual(report['summary'], self.data['status']['scores'])
        self.assertEqual(report['actual_attempts'], self.data['status']['attempt_reservations'])
        self.assertEqual(report['actual_children'], self.data['status']['local_cli_child_intents'])
        self.assertEqual(report['known_usage'], self.data['status']['known_usage'])
        self.assertEqual(len(report['all_case_transitions']), 164)
        self.assertEqual(sum(report['paired_budget_transitions'].values()), 164)
        for method in r.p.METHODS:
            cell = report['summary']['methods'][method]
            self.assertEqual([cell['strict'][k]['planned'] for k in ('joint', 'known', 'unknown')], [164, 72, 92])
            self.assertEqual(set(cell['per_generation']), {'0'})
            self.assertEqual([v['joint']['planned'] for v in cell['per_person'].values()], [82, 82])
        for cell in report['all_case_transitions']:
            self.assertTrue(all(len(cell[m]['answers']) == 4 for m in r.p.METHODS))
        self.assertFalse(report['generation_stability_verified'])

    def test_exact_sources_questions_reference_navigation_and_implementation_cannot_change(self):
        for name in r.p.FILES:
            data = copy.deepcopy(self.data); data['prepared_files'][name] = {}; self.reject(data)
        for key in ('scientific_source_ref', 'input_manifest_sha256'):
            data = copy.deepcopy(self.data); data[key] = 'foreign'; self.reject(data)

    def test_raw_answer_edit_is_not_hidden_by_updating_its_value_hash(self):
        data = copy.deepcopy(self.data)
        if not data['records']: self.assertTrue(data['status']['stop']); return
        data['records'][0]['raw'] = str(data['records'][0]['raw']) + 'altered'; self.reject(data)
        pair = next(((x, row) for x in self.data['records'] if x['kind'] in ('full', 'read') and x['state'] == 'completed'
            for row in r.p.inputs()['rows'] if row['person'] == x['profile'] and row['gold'] != 'U'
            and all(r.e.parse_answer(x['raw']).get(q) == row['gold'] for q in row['query_ids'])), None)
        if pair:
            rec, row = pair; data = copy.deepcopy(self.data)
            rec = next(x for x in data['records'] if x['slot'] == rec['slot'])
            answer = r.e.parse_answer(rec['raw']); answer[row['query_ids'][0]] = 'U'
            rec['raw'] = json.dumps(answer, ensure_ascii=False); rec['raw_value_sha256'] = r.p.digest(rec['raw'])
            self.reject(data)

    def test_person_method_budget_generation_and_exact_request_routing_are_frozen(self):
        if not self.data['records']: self.assertTrue(self.data['status']['stop']); return
        for fault in ('profile', 'method', 'budget', 'generation', 'request'):
            data = copy.deepcopy(self.data)
            rec = next((x for x in data['records'] if x['kind'] in ('extract', 'read')), data['records'][0])
            if fault == 'request':
                rec['request']['prompt'] += 'source supplement'; rec['request_sha256'] = r.p.digest(rec['request'])
                rec['execution_record']['request_sha256'] = rec['request_sha256']
            else: rec[fault] = 'foreign'; rec['execution_record'][fault] = 'foreign'
            self.reject(data)

    def test_fixed_denominators_usage_and_boolean_child_flags_cannot_be_changed(self):
        for method in r.p.METHODS:
            data = copy.deepcopy(self.data); data['status']['scores']['methods'][method]['strict']['joint']['planned'] -= 1
            self.reject(data)
        for fault in ('attempt', 'child_bool', 'usage', 'open'):
            data = copy.deepcopy(self.data)
            if fault == 'attempt': data['status']['attempt_reservations'] -= 1
            elif fault == 'child_bool': data['status']['local_cli_child_intents'] = True
            elif fault == 'usage': data['status']['known_usage']['total_tokens'] = data['status']['known_usage'].get('total_tokens', 0) + 1
            else: data['status']['scope_closed'] = False
            self.reject(data)

    def test_private_fields_and_unsupported_personal_stability_claims_are_rejected(self):
        for key in r.FALSE_CLAIMS:
            data = copy.deepcopy(self.data); data[key] = True; self.reject(data)
        data = copy.deepcopy(self.data); data['human_authorization'] = 'private'; self.reject(data)
        if self.data['records']:
            data = copy.deepcopy(self.data); data['records'][0]['machine_path'] = 'private'; self.reject(data)

    def test_original_model_card_cannot_be_replaced_by_a_repaired_card(self):
        rec = next((x for x in self.data['records'] if x['artifact']), None)
        if rec is None:
            self.assertTrue(self.data['status']['stop'] or self.data['status']['invalid_products']); return
        data = copy.deepcopy(self.data)
        next(x for x in data['records'] if x['slot'] == rec['slot'])['artifact']['prompt'] += 'repair'
        self.reject(data)

    def test_missing_budget_products_are_never_counted_as_observed_choice_recovery(self):
        good = dict(correct=True, missing=False); wrong = dict(correct=False, missing=False); absent = dict(correct=False, missing=True)
        for low, high, label in ((good, good, 'both_retained'), (wrong, good, 'only1536retained'),
            (good, wrong, 'only768retained'), (wrong, wrong, 'both_observed_fail'),
            (absent, good, 'only768missing'), (good, absent, 'only1536missing'), (absent, absent, 'both_missing')):
            self.assertEqual(r.budget_transition(low, high), label)

    def test_unknown_false_certainty_different_choice_and_missing_remain_distinct(self):
        for gold, values, label in (('a', [None, 'U'], 'missing'), ('a', ['U'] * 4, 'all_unknown_from_known'),
            ('a', ['a', 'U'], 'intermittent_unknown_from_known'), ('a', ['b', 'U'], 'mixed_unknown_and_different_choice'),
            ('a', ['a', 'b'], 'different_choice_from_known'), ('U', ['a', 'U'], 'choice_when_reference_unknown')):
            self.assertEqual(r.loss_kind(gold, values), label)

    def test_literal_action_navigation_is_not_a_semantic_verdict_or_new_layout_claim(self):
        value = dict(name='fixture', tagline='literal', unknowns=['unknown'], groups=[dict(scope='scope', rules=[
            dict(question='method', requires=['explicit necessary prerequisite for this project'], choose='short label', priority=0)])])
        diag = r.literal_action_diagnostic(value)
        self.assertEqual(len(diag['full_names_not_exact_action_fields']), 12)
        self.assertFalse(diag['exact_literal_difference_is_semantic_loss'])
        self.assertTrue(diag['option_matching_does_not_prove_unprompted_full_action_reconstruction'])
        plain = r.p.candidate.dense._render(value)
        self.assertEqual(r.layout_scheme(plain), 'dense')
        probe = r.template_capacity_probe()
        self.assertEqual(probe['new_model_calls'], 0)
        self.assertTrue(probe['not_model_extraction_or_reader_fidelity'])
        for row in probe['rows']:
            self.assertLessEqual(row['characters'], 768)
            self.assertFalse(row['authorized16uses_this_layout'])
            restored = r.template_restore(row['prompt'])
            original = r.p.candidate.dense.parse(r.p.candidate.base.bind(r.p.corpus.graph(row['person']),
                r.p.inputs()['sources'][row['person']], 16000)['prompt.md'])
            self.assertEqual(restored, original)
            self.assertTrue(all(a in row['prompt'] for spec in r.p.corpus.SPECS for a in spec[9:11]))
            for damage in ('guide', 'missing_field', 'trailing_line'):
                text = row['prompt']
                if damage == 'guide': text = text.replace('范围必需', '忽略范围前提', 1)
                elif damage == 'missing_field':
                    lines = text.splitlines(); i = next(i for i, line in enumerate(lines) if line.startswith('@'))
                    lines[i] = lines[i].rsplit('|', 1)[0]; text = '\n'.join(lines) + '\n'
                else: text += '@unresolved\n'
                with self.subTest(damage=damage), self.assertRaises(ValueError): r.template_restore(text)
            unsupported = copy.deepcopy(restored); unsupported['groups'][0]['rules'][2]['choose'] = 'different'
            with self.assertRaises(ValueError): r.template_render(unsupported)
            with self.assertRaises(ValueError): r.template_render(restored, 300)
        original = next((x for x in self.data['records'] if x['slot']==14 and x['state']=='completed'),None)
        if original:
            # Development view of an actual budget-rejected graph,not a repaired
            # original result and not an LLM reading measurement.
            view = r.template_slot_probe(self.data,14)
            self.assertEqual((view['diagnostic_flat_characters'],view['characters']),(997,768))
            self.assertFalse(view['reader_tested']);self.assertFalse(view['original_observation_replaced'])

    def test_trace_retains_complete_source_episode_and_every_original_read_order(self):
        cell = self.report['all_case_transitions'][0]; method = r.p.METHODS[0]
        before = r.p.digest(self.data)
        value = t.trace(self.data, self.report, cell['person'], cell['case'], method)
        self.assertEqual(len(value['complete_related_source_episodes']), 8)
        self.assertEqual({s['role'] for s in value['complete_related_source_episodes']}, {'user', 'assistant', 'tool'})
        self.assertEqual(len(value['public_queries']), 2)
        self.assertEqual(value['answers_by_read_and_order'], [cell[method]['answers'][:2], cell[method]['answers'][2:]])
        self.assertEqual(value['new_service_calls'], 0); self.assertEqual(r.p.digest(self.data), before)

    def test_valid_card_trace_preserves_original_graph_and_invalid_coordinates_reject(self):
        rec = next((x for x in self.data['records'] if x['artifact']), None)
        if rec:
            cell = next(c for c in self.report['all_case_transitions'] if c['person'] == rec['profile'])
            value = t.trace(self.data, self.report, rec['profile'], cell['case'], rec['method'])
            self.assertEqual(value['original_public_card'], rec['artifact']['prompt'])
            self.assertIsNotNone(value['deterministically_resolved_graph'])
            self.assertIsNotNone(value['compiled_active_rows'])
        for person, case, method in (('foreign', '0_new_boundary', r.p.METHODS[0]),
            (r.p.PROFILES[0], 'foreign', r.p.METHODS[0]), (r.p.PROFILES[0], '0_new_boundary', 'foreign')):
            with self.assertRaises(ValueError): t.trace(self.data, self.report, person, case, method)


if __name__ == '__main__': unittest.main()
