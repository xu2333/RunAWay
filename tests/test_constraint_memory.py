"""Offline contract safety/representation checks, not model performance tests."""
import copy
import unittest

from runaway import constraint_memory as cm


def fixture():
    texts = ['Only the two greenhouse trays, today. Each tray is dry or wet. '
             'Stable rule is one of these two: water if either tray is dry; '
             'water if exactly one tray is dry. Otherwise wait.',
             'Both trays wet. I choose wait.',
             'Earlier I tried water.',
             'That earlier decision is void; both trays wet: I choose wait.']
    sources = {'schema_version': 1, 'sources': [
        {'id': 's' + str(i + 1), 'episode_id': 'today', 'role': 'user', 'text': text}
        for i, text in enumerate(texts)]}
    def a(i, quote=None):
        return {'source_id': 's' + str(i), 'quote': quote or texts[i - 1]}
    contract = {'version': cm.VERSION, 'name': '小水壶', 'tagline': '不替没说过的话浇水',
                'scope': {'id': 'trays_today', 'text': 'Only the two greenhouse trays, today.',
                          'evidence': [a(1)]},
                'features': [{'id': k, 'values': ['wet', 'dry'], 'evidence': [a(1)]}
                             for k in ('left', 'right')],
                'actions': ['wait', 'water'],
                'family': {'commitment': [a(1)], 'rules': [
                    {'id': 'either', 'definition': 'water if either tray is dry',
                     'any_of': [{'left': 'dry'}, {'right': 'dry'}], 'evidence': [a(1)]},
                    {'id': 'xor', 'definition': 'water if exactly one tray is dry',
                     'any_of': [{'left': 'dry', 'right': 'wet'}, {'left': 'wet', 'right': 'dry'}],
                     'evidence': [a(1)]}]},
                'observations': [{'id': 'last', 'values': {'left': 'wet', 'right': 'wet'},
                                  'choice': 'wait', 'decision': a(4), 'contexts': [a(2)],
                                  'supersedes': ['s3']}]}
    return contract, sources


class ConstraintMemoryTests(unittest.TestCase):
    def setUp(self):
        self.c, self.s = fixture()

    def decide(self, values, **kw):
        return cm.decide(self.c, self.s, scope=kw.get('scope', 'trays_today'),
                         values=values, offered=kw.get('offered', ['wait', 'water']))

    def test_unobserved_entailment_requires_explicit_family_and_keeps_alternatives(self):
        compiled = cm.compile_contract(self.c, self.s)
        self.assertEqual(compiled['compatible_rule_ids'], ['either', 'xor'])
        self.assertEqual(self.decide({'left': 'dry', 'right': 'wet'})['choice'], 'water')
        self.assertEqual(self.decide({'left': 'dry', 'right': 'dry'})['choice'], cm.U)
        self.c['family'] = None
        self.assertEqual(self.decide({'left': 'dry', 'right': 'wet'})['reason'], 'unobserved_without_family_commitment')
        self.assertEqual(self.decide({'left': 'wet', 'right': 'wet'})['choice'], 'wait')

    def test_partial_is_universal_over_completions_and_rules(self):
        self.assertEqual(self.decide({'left': 'dry'})['choice'], cm.U)
        # Eliminate XOR with a second actual user choice. Now either is identified.
        self.s['sources'].append({'id': 's5', 'episode_id': 'today', 'role': 'user',
                                  'text': 'Both trays dry. I choose water.'})
        o = copy.deepcopy(self.c['observations'][0]);o.update(id='both_dry', values={'left': 'dry', 'right': 'dry'},
            choice='water', decision={'source_id': 's5', 'quote': 'Both trays dry. I choose water.'}, supersedes=[])
        self.c['observations'].append(o)
        self.assertEqual(self.decide({'left': 'dry'})['choice'], 'water')
        self.assertEqual(self.decide({'right': 'wet'})['choice'], cm.U)

    def test_no_family_partial_requires_complete_observed_coverage(self):
        self.c['family'] = None
        self.assertEqual(self.decide({'left': 'wet'})['choice'], cm.U)

    def test_undefined_features_scopes_and_absent_action_are_unknown(self):
        self.assertEqual(self.decide({'left': 'damp'})['reason'], 'undefined_feature_value')
        self.assertEqual(self.decide({'weather': 'sunny'})['reason'], 'undefined_feature_value')
        self.assertEqual(self.decide({}, scope='outdoor_garden')['reason'], 'outside_scope')
        self.assertEqual(self.decide({'left': 'wet', 'right': 'wet'}, offered=['water'])['reason'], 'known_action_not_offered')

    def test_contradictory_current_observations_do_not_choose_a_hidden_rule(self):
        self.s['sources'].append({'id': 's5', 'episode_id': 'today', 'role': 'user', 'text': 'I choose water.'})
        o = copy.deepcopy(self.c['observations'][0]);o.update(id='conflict', choice='water',
            decision={'source_id': 's5', 'quote': 'I choose water.'}, supersedes=[])
        self.c['observations'].append(o)
        self.assertEqual(self.decide({})['reason'], 'inconsistent_evidence')
        with self.assertRaisesRegex(ValueError, 'Inconsistent'):
            cm.render(self.c, self.s, 16000)

    def test_no_compatible_rule_does_not_fabricate_one(self):
        self.c['observations'][0]['choice'] = 'water'
        self.s['sources'][-1]['text'] = 'Both trays wet. I choose water.'
        self.c['observations'][0]['decision']['quote'] = self.s['sources'][-1]['text']
        self.assertEqual(self.decide({})['reason'], 'inconsistent_evidence')

    def test_commitments_and_choices_cannot_use_assistant_evidence(self):
        for position in (0, 3):
            with self.subTest(position=position):
                s = copy.deepcopy(self.s);s['sources'][position]['role'] = 'assistant'
                with self.assertRaisesRegex(ValueError, 'user evidence'):
                    cm.validate(self.c, s)

    def test_invalid_quote_definition_value_and_chronology_are_rejected(self):
        variants = []
        c = copy.deepcopy(self.c);c['family']['rules'][0]['definition'] = 'invented';variants.append(c)
        c = copy.deepcopy(self.c);c['features'][0]['values'].append('snow');variants.append(c)
        c = copy.deepcopy(self.c);c['observations'][0]['supersedes'] = ['s4'];variants.append(c)
        c = copy.deepcopy(self.c);c['scope']['evidence'][0]['quote'] = 'not in sources';variants.append(c)
        for c in variants:
            with self.subTest(contract=c), self.assertRaises(ValueError):
                cm.validate(c, self.s)

    def test_no_opaque_labels_or_truncation_and_all_overhead_counted(self):
        self.c['tagline'] = '保持来源条件，不把推导当观察。' * 3
        text = cm.render(self.c, self.s, 16000)
        self.assertIn('water if exactly one tray is dry', text)
        self.assertIn('water if either tray is dry', text)
        self.assertIn('dry', text)
        self.assertIn(cm.GUIDE, text)
        with self.assertRaisesRegex(ValueError, 'exceeds budget'):
            cm.render(self.c, self.s, 300)

    def test_quote_matching_explicitly_does_not_certify_semantic_translation(self):
        # A wrong prose-to-logic translation can still have exact source quotes.
        # The API must not advertise structural validation as semantic proof.
        self.c['family']['rules'][0]['any_of'] = [{'left': 'wet'}]
        checked = cm.compile_contract(self.c, self.s)
        self.assertFalse(checked['semantic_translation_verified'])
        self.assertFalse(checked['behavioral_fidelity_verified'])
        self.assertEqual(checked['status'], 'candidate_unvalidated')

    def test_undefined_action_is_rejected_and_boolean_constants_are_supported(self):
        c = copy.deepcopy(self.c);c['actions'][1] = 'invented action'
        with self.assertRaisesRegex(ValueError, 'Action vocabulary'):
            cm.validate(c, self.s)
        # Constant policies still require a source definition and user commitment.
        # These structural variants do not claim semantic translation correctness.
        self.c['family']['rules'][0]['any_of'] = []
        self.c['family']['rules'][1]['any_of'] = [{}]
        checked = cm.compile_contract(self.c, self.s)
        self.assertEqual(checked['compatible_rule_ids'], ['either'])
        self.assertEqual(self.decide({})['choice'], 'wait')

    def test_finite_state_explosion_is_rejected_before_enumeration(self):
        self.s['sources'][0]['text'] += ' Defined third value: damp.'
        self.c['features'] = [{'id': 'dimension' + str(i), 'values': ['wet', 'dry', 'damp'],
                               'evidence': [{'source_id': 's1', 'quote': self.s['sources'][0]['text']}]}
                              for i in range(6)]
        with self.assertRaisesRegex(ValueError, 'exceeds256'):
            cm.validate(self.c, self.s)


if __name__ == '__main__':
    unittest.main()
