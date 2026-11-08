"""A valid shorter graph can hide condition loss in the existing query set."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('material_condition_counterexample',ROOT/'benchmarks/material-condition-blindspot-v1/check.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class MaterialConditionBlindspotTests(unittest.TestCase):
    def test_fixed_questions_fail_to_identify_a_dropped_material_guard(self):
        r=m.diagnose(m.read_evidence())
        self.assertEqual((r['original_characters'],r['damaged_characters']),(831,755))
        self.assertTrue(r['old_guard_accepts_damaged_graph'])
        self.assertEqual((r['existing_person_cases'],r['original_existing_symbolic_correct'],r['damaged_existing_symbolic_correct']),(44,44,44))
        self.assertEqual((r['orthogonal_unknown_probes'],r['damaged_false_certainty_probes']),(16,16))
        self.assertTrue(all(x['original_symbolic']=='U'and x['damaged_symbolic']!='U'for x in r['probes']))
        self.assertFalse(r['automatic_model_reader_performance_established'])
    def test_damage_changes_only_twelve_material_conditions_not_evidence_or_actions(self):
        data=m.read_evidence();before=copy.deepcopy(data);r=m.diagnose(data)
        self.assertEqual(data,before)
        import json
        graph=json.loads(next(x for x in data['records']if x['slot']==10)['raw']);damaged=r['damaged_graph']
        changed=0
        for old,new in zip(graph['nodes'],damaged['nodes']):
            a=copy.deepcopy(old);b=copy.deepcopy(new)
            if a['kind']=='base':
                for x,y in zip(a['requires'],b['requires']):
                    if x['text']!=y['text']:
                        self.assertIn('材料',x['text']);self.assertNotIn('材料',y['text']);changed+=1
                    x.pop('text');y.pop('text')
            self.assertEqual(a,b)
        self.assertEqual(changed,12)
        for key in('objects','object_aliases','source_accounting','unknowns'):
            self.assertEqual(graph[key],damaged[key])
    def test_diagnostic_has_no_service_and_rejects_foreign_evidence(self):
        with patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
            r=m.diagnose(m.read_evidence())
        backend.assert_not_called();self.assertEqual(r['new_model_calls'],0)
        data=m.read_evidence();data['scientific_source_ref']='foreign'
        with self.assertRaises(AssertionError):m.diagnose(data)

if __name__=='__main__':unittest.main()
