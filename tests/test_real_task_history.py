"""Synthetic software fixtures only; no personal-fidelity observations."""
import copy
import json
import unittest

from runaway.real_task_history import paired_requests, score_deliveries as score, validate_case


def score_deliveries(cases, requests, judgments):
    return score(cases, requests, {j["slot"]: j["deliverable"] for j in judgments}, judgments)


def fixture():
    return {
        'case_id': 'fixture', 'analysis_role': 'primary',
        'messages': [
            {'ordinal': 1, 'role': 'user', 'text': 'For this fictional project, retain event order.'},
            {'ordinal': 2, 'role': 'user', 'text': 'Also keep timing.'},
            {'ordinal': 3, 'role': 'assistant', 'text': 'A sample acquisition setup is available.'},
            {'ordinal': 4, 'role': 'user', 'text': 'Describe the next recording plan.'},
        ],
        'current_start': 3, 'task_ordinal': 4,
        'current_audit': {'reviewed_ordinals': [3, 4], 'explicit_target_cue': False,
                          'indirect_cue_note': 'Acquisition context may already encourage careful recording.'},
        'constraints': [{'id': 'ordered', 'criterion': 'Preserve order and timing.',
                         'scope_status': 'applicable_not_retracted', 'scope_note': 'Same fictional project.',
                         'anchors': [{'ordinal': 1, 'quote': 'retain event order'},
                                     {'ordinal': 2, 'quote': 'keep timing'}]}],
        'quality_gate': 'Produce an actionable recording plan.',
    }


def judgment(slot, quality=True, status='met'):
    return {'slot': slot, 'deliverable': 'Record ordered, timed events.', 'quality_pass': quality,
            'quality_reason': 'Synthetic fixture judgment, not a model result.',
            'ratings': {'ordered': {'status': status, 'reason': 'Fixture explanation.',
                                     'excerpts': ['ordered, timed events'] if status != 'unclear' else []}}}


class RealTaskHistoryTests(unittest.TestCase):
    def test_pairs_preserve_all_messages_and_exclude_reference_fields(self):
        case = fixture()
        requests = paired_requests([case])
        self.assertEqual(len(requests), 4)
        payloads = [json.loads(r['prompt'].split('INPUT_JSON:\n')[1]) for r in requests]
        self.assertTrue(all(p['current'] == payloads[0]['current'] for p in payloads))
        self.assertEqual(len(payloads[1]['history']), 2)
        self.assertNotIn('history', payloads[0])
        self.assertNotIn('criterion', json.dumps(payloads))
        self.assertNotIn('quality_gate', json.dumps(payloads))
        self.assertEqual([r['condition'] for r in requests],
                         ['no_history', 'available_text_history', 'available_text_history', 'no_history'])

    def test_future_outcome_is_rejected(self):
        case = fixture()
        case['messages'].append({'ordinal': 5, 'role': 'assistant', 'text': 'Actual later answer.'})
        with self.assertRaisesRegex(ValueError, 'stop_at_actual_user_task'):
            validate_case(case)

    def test_anchor_must_be_earlier_owner_text(self):
        for ordinal in (3, 4, 99):
            case = fixture()
            case['constraints'][0]['anchors'][0]['ordinal'] = ordinal
            with self.assertRaisesRegex(ValueError, 'earlier_owner_anchor'):
                validate_case(case)

    def test_altered_quote_and_literal_current_leakage_rejected(self):
        case = fixture()
        case['constraints'][0]['anchors'][0]['quote'] = 'invented preference'
        with self.assertRaisesRegex(ValueError, 'exact_anchor_quote'):
            validate_case(case)
        case = fixture()
        case['messages'][-1]['text'] += ' retain event order'
        with self.assertRaisesRegex(ValueError, 'literal_current_leakage'):
            validate_case(case)

    def test_audit_cannot_skip_current_assistant_context(self):
        case = fixture()
        case['current_audit']['reviewed_ordinals'] = [4]
        with self.assertRaisesRegex(ValueError, 'audit_all_current_messages'):
            validate_case(case)
        case = fixture()
        case['current_audit']['explicit_target_cue'] = True
        with self.assertRaisesRegex(ValueError, 'explicit_current_cue'):
            validate_case(case)

    def test_missing_and_unclear_remain_in_denominator(self):
        cases = [fixture()]
        requests = paired_requests(cases)
        result = score_deliveries(cases, requests, [judgment(1), judgment(4, status='unclear')])
        self.assertEqual(len(result['rows']), 4)
        self.assertEqual(sum(r['status'] == 'missing' for r in result['rows']), 2)
        for total in result['totals'].values():
            self.assertEqual((total['retained'], total['cases']), (0, 1))

    def test_quality_failure_prevents_vacuous_compliance(self):
        cases = [fixture()]
        requests = paired_requests(cases)
        ratings = [judgment(i) for i in range(1, 5)]
        ratings[0]['quality_pass'] = False
        result = score_deliveries(cases, requests, ratings)
        self.assertEqual(result['totals']['no_history']['retained'], 0)
        self.assertEqual(result['totals']['available_text_history']['retained'], 1)

    def test_fabricated_excerpt_and_duplicate_judgment_rejected(self):
        cases = [fixture()]
        requests = paired_requests(cases)
        rating = judgment(1)
        rating['ratings']['ordered']['excerpts'] = ['not in the output']
        with self.assertRaisesRegex(ValueError, 'exact_output_excerpts'):
            score_deliveries(cases, requests, [rating])
        with self.assertRaisesRegex(ValueError, 'known_unique_judgment_slot'):
            score_deliveries(cases, requests, [judgment(1), judgment(1)])

    def test_judgment_cannot_rewrite_sealed_delivery(self):
        cases = [fixture()]
        requests = paired_requests(cases)
        with self.assertRaisesRegex(ValueError, 'exact_observed_deliverable'):
            score(cases, requests, {1: 'Original different answer.'}, [judgment(1)])
        with self.assertRaisesRegex(ValueError, 'exact_observed_deliverable'):
            score(cases, requests, {}, [judgment(1)])
        result = score(cases, requests, {1: 'Unscored answer.'}, [])
        self.assertEqual(result['rows'][0]['status'], 'unscored')
        self.assertEqual(result['totals']['no_history']['by_role']['primary']['cases'], 1)

    def test_changed_prompt_or_dropped_slot_cannot_shrink_grid(self):
        cases = [fixture()]
        requests = paired_requests(cases)
        edited = copy.deepcopy(requests)
        edited[0]['prompt'] += ' answer hint'
        for bad in (edited, requests[:-1], requests[:2]):
            with self.assertRaisesRegex(ValueError, 'exact_paired_schedule'):
                score_deliveries(cases, bad, [])


if __name__ == '__main__':
    unittest.main()
