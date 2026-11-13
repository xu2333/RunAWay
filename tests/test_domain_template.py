"""Counted domain-template syntax tests,not model-reading or extraction evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('domain_template_test_codec',ROOT/'benchmarks/domain-template-v2/codec.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


def fixture():
    groups=[]
    for i,u in enumerate(('分钟','元')):
        groups.append(dict(scope='项目'+str(i)+'；（余量按非负整数'+u+'计）'+('且（必要门槛）'if i else''),rules=[
            dict(question='做法',requires=['另须成立','余量≥13'+u],choose='甲|方案',priority=0),
            dict(question='做法',requires=['另须成立','余量<13'+u],choose='乙\\方案',priority=0),
            dict(question='做法',requires=['余量<13'+u,'例外成立'],choose='甲|方案',priority=1)]))
    return dict(name='测试卡',tagline='数值不偷跑',groups=groups,unknowns=['副本未知','未覆盖未知'])


class DomainTemplateTests(unittest.TestCase):
    def test_roundtrip_preserves_every_ordered_field_with_domain_only_scope(self):
        value=fixture();result=c.render(value)
        self.assertEqual(c.restore(result['prompt']),value)
        self.assertIn('余量取非负整数，单位同界。',result['prompt'])
        self.assertNotIn('余量按非负整数',result['prompt'])
        self.assertFalse(result['model_reader_fidelity_verified']);self.assertFalse(result['used_by_authorized14'])
        self.assertEqual(result['new_model_calls'],0)

    def test_domain_and_unit_must_be_explicit_in_every_group(self):
        for replacement in('项目；（必要门槛）','项目；（余量按非负整数站计）','项目；（余量按正整数分钟计）','项目；（必要门槛）且（余量按非负整数分钟计）'):
            value=fixture();value['groups'][0]['scope']=replacement
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):c.render(value)

    def test_noncanonical_input_cannot_be_silently_normalized(self):
        value=fixture();value['unknown_extra']='hidden'
        with self.assertRaises(ValueError):c.render(value)
        value=fixture();value['groups'][0]['scope']='项目；（余量按非负整数分钟计）且'
        with self.assertRaises(ValueError):c.render(value)

    def test_full_counted_budget_and_guide_cannot_be_excluded(self):
        value=fixture();value['unknowns'].append('未观察就不替用户决定。'*8);result=c.render(value)
        n=len(result['prompt']);self.assertEqual(n,result['characters'])
        self.assertEqual(c.render(value,n)['characters'],n)
        with self.assertRaises(ValueError):c.render(value,n-1)
        for text in(result['prompt'].replace('余量取非负整数，单位同界。',''),result['prompt'].replace('另须空即真。','另须空不明。'),result['prompt']+'junk\n'):
            with self.assertRaises(ValueError):c.restore(text)

    def test_unescaped_metadata_and_literal_action_characters_roundtrip(self):
        value=fixture();value['name']='卡"名';value['tagline']='多行\n元|分钟';value['unknowns'].append('字面\\n不自动解释')
        result=c.render(value)
        self.assertEqual(c.restore(result['prompt']),value)
        self.assertEqual(c.restore(result['prompt'])['groups'][0]['rules'][0]['choose'],'甲|方案')

    def test_unsupported_rule_shapes_fail_without_dropping_conditions(self):
        for fault in('extra_condition','priority','action','float_threshold'):
            value=fixture();g=value['groups'][0]
            if fault=='extra_condition':g['rules'][0]['requires'].insert(0,'还有门槛')
            elif fault=='priority':g['rules'][2]['priority']=2
            elif fault=='action':g['rules'][2]['choose']='另一方案'
            else:g['rules'][0]['requires'][-1]='余量≥13.5分钟'
            with self.subTest(fault=fault),self.assertRaises(ValueError):c.render(value)

    def test_guide_does_not_certify_semantics_or_bind_to_a_source(self):
        # A valid encoding of a changed graph is not a proof of its source truth.
        original=fixture();changed=copy.deepcopy(original)
        for row in changed['groups'][0]['rules']:
            row['requires']=[x.replace('13分钟','14分钟')for x in row['requires']]
        text=c.render(changed)['prompt']
        self.assertEqual(c.restore(text),changed);self.assertNotEqual(c.restore(text),original)

    def test_actual_slot3_capacity_is_posthoc_and_old_record_is_unchanged(self):
        s=importlib.util.spec_from_file_location('domain_template_test_archive',ROOT/'scripts/replay_domain_revision.py')
        r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
        data=r.p.read(r.DEFAULT);before=r.p.digest(data)
        rec=next(x for x in data['records']if x['slot']==3);self.assertIsNotNone(rec['artifact'])
        value=c.d.parse(r.p.old.candidate.restore(rec['artifact']['prompt']))
        view=c.render(value);self.assertEqual((rec['artifact']['characters'],view['characters']),(1061,767))
        self.assertEqual(c.restore(view['prompt']),value);self.assertEqual(r.p.digest(data),before)
        self.assertFalse(view['source_only_generation_tested'])


if __name__=='__main__':unittest.main()
