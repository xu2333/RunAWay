import copy
import unittest

from runaway import fidelity_stress as fs


class SemanticTests(unittest.TestCase):
    def event(self, identity, day, op, **kw):
        return {'id':identity,'day':day,'op':op,'key':'feedback',**kw}

    def test_hand_computed_strength_replacement_revocation_and_nested_restore(self):
        e = [self.event('r1',1,'prefer',value='0',strength=3),
             self.event('r2',2,'prefer',value='1',strength=1),
             self.event('r3',3,'replace',value='1',strength=2),
             self.event('r4',4,'revoke',target='r3'),
             self.event('r5',5,'revoke',target='r4')]
        self.assertEqual([fs.resolve(e,'feedback',d,{})[0] for d in (2,3,4,5)], ['0','1','0','1'])

    def test_conjunction_hard_priority_and_equal_strength_conflict(self):
        e = [self.event('r1',1,'prefer',value='0',strength=3),
             self.event('r2',2,'except',value='1',when={'c0':True}),
             self.event('r3',3,'hard',value='0',when={'c0':True,'c1':True})]
        self.assertEqual(fs.resolve(e,'feedback',3,{'c0':False,'c1':True})[0], '0')
        self.assertEqual(fs.resolve(e,'feedback',3,{'c0':True,'c1':False})[0], '1')
        self.assertEqual(fs.resolve(e,'feedback',3,{'c0':True,'c1':True}), ('0','hard'))
        conflict = [self.event('ra',1,'prefer',value='0',strength=2), self.event('rz',1,'prefer',value='1',strength=2)]
        self.assertEqual(fs.resolve(conflict,'feedback',1,{})[0], 'U')
        self.assertEqual(fs.resolve(list(reversed(conflict)),'feedback',1,{})[0], 'U')
        conflict.append(self.event('rr',2,'revoke',target='rz'))
        self.assertEqual(fs.resolve(conflict,'feedback',2,{})[0], '0')

    def test_clear_and_record_renaming_do_not_manufacture_preference(self):
        w = fs.build_world();person = w['people'][0];renamed = copy.deepcopy(person['events'])
        names = {e['id']:'new-'+str(i) for i,e in enumerate(renamed)}
        for e in renamed:
            e['id'] = names[e['id']]
            if e['op'] == 'revoke':e['target'] = names[e['target']]
        for c in person['cases']:
            self.assertEqual(fs.resolve(person['events'],c['key'],c['at'],c['context']),
                             fs.resolve(renamed,c['key'],c['at'],c['context']))
        self.assertEqual(fs.resolve(renamed,'marker',9,{})[0], '0')
        self.assertEqual(fs.resolve(renamed,'marker',12,{})[0], 'U')


class CalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.world=fs.build_world();cls.result=fs.calibrate(cls.world)

    def test_independent_axes_and_paired_units_not_inflated_by_option_orders(self):
        w=self.world;self.assertEqual(len(w['people']),12)
        lookup={p['id']:p for p in w['people']}
        varied=set()
        for p in w['people']:
            for i,(a,b) in enumerate(zip(p['parameters'],lookup[p['twin']]['parameters'])):
                if a!=b:
                    self.assertEqual(set(k for k in a if a[k]!=b[k]),{'exception'})
                    varied.add(i)
        self.assertEqual(varied,set(range(6)))
        s=self.result['controls']['full_semantic']['current_choice']
        self.assertEqual((s['planned'],s['current_scenarios_option_orders_collapsed']['planned'],s['independent_cluster_count']), (672,336,6))
        self.assertEqual(s['matched_domain_contrasts']['planned'],6)
        self.assertEqual(s['matched_domain_contrasts']['correct'],6)
        wrong=self.result['controls']['wrong_person']['current_choice']
        self.assertGreater(wrong['accuracy'],.9)  # Raw accuracy alone still hides loss of individuality.
        self.assertEqual(wrong['matched_domain_contrasts']['correct'],0)

    def test_each_damage_has_targeted_sensitivity_current_and_history_are_separate(self):
        controls=self.result['controls'];self.assertEqual(self.result['external_model_calls'],0)
        for name,task,layer in [('delete_exceptions','current_choice','exceptions'),
                ('delete_hard','current_choice','hard_constraints'),('ignore_updates','current_choice','updates'),
                ('ignore_revocations','current_choice','revocations'),('wrong_condition','current_choice','exceptions'),
                ('wrong_time','historical_reconstruction','updates'),('delete_strong','current_choice','strength'),
                ('invent_unknowns','current_choice','unknowns'),('weaken_conjunction','current_choice','conjunctions'),
                ('resolve_conflict_arbitrarily','current_choice','conflicts')]:
            q=controls[name][task]['layers'][layer];self.assertLess(q['correct'],q['planned'],name)
        self.assertEqual(controls['wrong_time']['current_choice']['accuracy'],1)
        self.assertLess(controls['wrong_time']['historical_reconstruction']['accuracy'],.5)
        self.assertEqual(controls['delete_hard']['current_choice']['hard_constraints']['observed_violations'],72)
        for name in fs.CONTROLS[1:]:self.assertLess(controls[name]['joint']['accuracy'],1,name)

    def test_missing_unknown_action_consistency_and_hard_violations_are_distinct(self):
        none=self.result['controls']['none']['current_choice'];missing=fs.score(self.world,{},'current_choice')
        self.assertEqual((missing['correct'],missing['missing'],missing['planned']),(0,672,672))
        self.assertEqual((none['correct'],none['missing']),(96,0))
        self.assertEqual(none['current_scenarios_option_orders_collapsed']['consistent'],336)
        self.assertEqual(none['current_scenarios_option_orders_collapsed']['correct'],48)
        self.assertGreater(none['hard_constraints']['abstentions'],0)
        self.assertEqual(none['hard_constraints']['observed_violations'],0)

    def test_future_is_new_wording_and_combinations_without_future_dated_queries(self):
        future=fs.build_world(829491,'future');self.assertEqual(len(future['people']),4)
        old={p['history'] for p in self.world['people']}
        self.assertTrue(old.isdisjoint(p['history'] for p in future['people']))
        signatures={tuple((x['base'],x['exception'],x['revoke_update'],x['restore_hard']) for x in p['parameters']) for p in self.world['people']}
        for p in future['people']:
            self.assertNotIn(tuple((x['base'],x['exception'],x['revoke_update'],x['restore_hard']) for x in p['parameters']),signatures)
            self.assertEqual(len(p['cases']),75)
            self.assertTrue(all(c['at']<=p['source_cutoff'] for c in p['cases']))
            self.assertNotIn('尚未解决',next(c['public']['question'] for c in p['cases'] if c['key']=='conflict'))
        full=fs.score(future,fs.predict(future,'full_semantic'),'current_choice')
        wrong=fs.score(future,fs.predict(future,'wrong_person'),'current_choice')
        self.assertEqual((full['planned'],full['independent_cluster_count'],full['matched_domain_contrasts']['planned']),(224,2,6))
        self.assertLess(wrong['accuracy'],.8)

    def test_scoring_is_invariant_to_query_order_and_invalid_is_not_a_violation(self):
        world=copy.deepcopy(self.world);answers=fs.predict(world,'full_semantic')
        expected=fs.score(world,answers,'current_choice')
        for p in world['people']:p['cases'].reverse()
        actual=fs.score(world,answers,'current_choice')
        for key in ('correct','planned','missing','current_scenarios_option_orders_collapsed','matched_domain_contrasts'):
            self.assertEqual(actual[key],expected[key])
        p=world['people'][0];c=next(c for c in p['cases'] if c['active_hard'])
        answers[p['id']][c['public']['id']]='invalid'
        actual=fs.score(world,answers,'joint')
        self.assertEqual(actual['invalid_answers'],1)
        self.assertEqual(actual['hard_constraints']['observed_violations'],0)


if __name__=='__main__':unittest.main()
