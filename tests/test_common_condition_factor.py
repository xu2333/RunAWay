"""Exact public projection restoration; these are not model-reader measurements."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('common_factor_tests',ROOT/'benchmarks/common-condition-factor-v1/codec.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


def fixture():
    return dict(name='四叶签',tagline='前提各归本题项目。',groups=[dict(scope='甲',rules=[
        dict(question='选择',requires=['已经明确允许在本题所问项目内进行可撤销模拟','材料齐备'],choose='先试',priority=0),
        dict(question='选择',requires=['已经明确允许在本题所问项目内进行可撤销模拟','时间紧','材料未齐'],choose='先列',priority=1)]),
        dict(scope='乙',rules=[dict(question='选择',requires=['已经明确允许在本题所问项目内进行可撤销模拟','材料齐备'],choose='先列',priority=0)])],unknowns=['其它组合未知；不代表行动授权。'])


class CommonConditionFactorTests(unittest.TestCase):
    def test_direct_entrypoints_work_outside_checkout_without_pythonpath(self):
        env={k:v for k,v in os.environ.items()if k not in('PYTHONPATH','PYTHONHOME')}
        bench=ROOT/'benchmarks/common-condition-factor-v1'
        with tempfile.TemporaryDirectory()as tmp:
            directory=Path(tmp)
            for script,args in(('check.py',[]),('plan.py',['--out',str(directory/'packet')])):
                proc=subprocess.run([sys.executable,'-I','-B',str(bench/script),*args],
                                    cwd=directory,env=env,capture_output=True,text=True,timeout=90)
                self.assertEqual(proc.returncode,0,proc.stderr)
                result=json.loads(proc.stdout)
                self.assertEqual(result['new_model_calls'],0)
                self.assertFalse(result['model_reader_fidelity_verified'])
            proposal=json.loads((directory/'packet/proposal.json').read_text())
            self.assertFalse(proposal['approved'])
            self.assertEqual(proposal['max_new_local_cli_attempts'],20)
            self.assertEqual(len(json.loads((directory/'packet/static-requests.json').read_text())),20)

    def test_all_eight_inherited_cards_fit768_and_restore_every_original_field(self):
        path=ROOT/'benchmarks/source-id-initial-encoding-v1/measured.synthetic.json'
        data=json.loads(path.read_text());cards=[r for r in data['records']if r['kind']=='extract'];self.assertEqual(len(cards),8)
        before=c.dense.canonical(data)
        with patch('runaway.generation.codex_generate',side_effect=AssertionError('No model'))as backend:
            for parent in cards:
                original=parent['artifact']['prompt'];result=c.factor(original,768)
                self.assertEqual(c.restore(result['prompt']),c.dense.decode(original))
                self.assertLessEqual(result['characters'],768);self.assertGreater(result['saved_characters'],0)
                self.assertEqual(c.dense.parse(c.restore(result['prompt'])),c.dense.parse(original))
                self.assertFalse(result['model_reader_fidelity_verified'])
        backend.assert_not_called();self.assertEqual(c.dense.canonical(data),before)

    def test_condition_prefix_is_shared_across_all_rules_and_every_scope(self):
        value=fixture();text=c.dense._render(value);result=c.factor(text,4096)
        self.assertEqual(result['common_conditions'],['已经明确允许在本题所问项目内进行可撤销模拟'])
        restored=c.dense.parse(c.restore(result['prompt']))
        self.assertEqual(restored,value)
        self.assertEqual(restored['groups'][1]['rules'][0]['choose'],'先列')
        self.assertIn('本题所问项目',result['prompt'])

    def test_unconditional_row_prevents_any_hoisted_prerequisite(self):
        value=fixture();value['groups'][1]['rules'][0]['requires']=[];text=c.dense._render(value)
        result=c.factor(text,4096);self.assertEqual(result['prompt'],text);self.assertEqual(result['common_conditions'],[])
        self.assertEqual(c.dense.parse(c.restore(result['prompt'])),value)

    def test_different_order_is_not_silently_reordered_or_deduplicated(self):
        value=fixture();value['groups'][1]['rules'][0]['requires']=['材料齐备','已经明确允许在本题所问项目内进行可撤销模拟']
        text=c.dense._render(value);result=c.factor(text,4096)
        self.assertEqual(result['prompt'],text);self.assertEqual(c.dense.parse(c.restore(text)),value)
        value=fixture()
        for group in value['groups']:
            for row in group['rules']:row['requires'].insert(0,'已经明确允许在本题所问项目内进行可撤销模拟')
        result=c.factor(c.dense._render(value),4096)
        self.assertEqual(c.dense.parse(c.restore(result['prompt'])),value)

    def test_escape_json_controls_and_unknowns_restore_exactly(self):
        value=fixture();special='材料&齐备|a→b\n"原样"\\'
        for group in value['groups']:
            for row in group['rules']:row['requires'].insert(0,special)
        value['groups'][0]['scope']='甲@?';value['unknowns']=['?原样\n'+special]
        text=c.dense._render(value);result=c.factor(text,4096)
        self.assertEqual(c.dense.parse(c.restore(result['prompt'])),value)
        self.assertEqual(c.restore(result['prompt']),text)

    def test_budget_is_whole_card_and_no_condition_is_truncated(self):
        text=c.dense._render(fixture());before=text
        with self.assertRaises(ValueError):c.factor(text,1)
        for budget in(0,-1,True,768.0):
            with self.assertRaises(ValueError):c.factor(text,budget)
        self.assertEqual(text,before)

    def test_malformed_common_header_is_rejected(self):
        value=fixture();head=c.dense.prefix(value);body=c.dense._render(value)[len(head):]
        for clause in('[]','{}','[true]','[""]','["a", "b"]'):
            with self.assertRaises(ValueError):c.restore(head+c.LABEL+clause+'\n'+body)

    def test_existing_counted_dictionary_can_restore_without_hidden_decoder(self):
        value=fixture()
        phrase='完整保留的长材料条件'*3
        value['groups'][0]['rules'][0]['requires'].append(phrase)
        value['groups'][0]['rules'][1]['requires'].append(phrase)
        value['groups'][1]['rules'][0]['requires'].append(phrase)
        expanded=c.dense._render(value)
        packed,report=c.dense.pack(expanded,len(expanded)-1,prefix=c.dense.prefix(value))
        self.assertTrue(report['dictionary'])
        result=c.factor(packed,4096)
        self.assertEqual(c.restore(result['prompt']),expanded)
        self.assertEqual(c.dense.parse(c.restore(result['prompt'])),value)


if __name__=='__main__':unittest.main()
