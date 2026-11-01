"""Lossless public-field codec calibration; no model fidelity claim."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from runaway.portable import render_expression
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


c = load('dense_codec_tests', ROOT / 'benchmarks/owned-dense-v1/codec.py')
fixture = load('dense_owner_fixtures', ROOT / 'tests/test_owned_conditions.py').fixture


class DenseCodecTests(unittest.TestCase):
    def test_semantic_projection_is_exactly_the_original_grouped_fields(self):
        source, ledger = fixture()
        grouped, _ = c.base.project(ledger, source)
        files = c.bind(ledger, source)
        parsed = c.parse(files['prompt.md'])
        self.assertEqual(c.grouped_projection(parsed), c.base.grouped.projection(grouped))
        self.assertEqual(render_expression(files['portable.json']), files['prompt.md'])
        self.assertFalse(files['summary.private.json']['behavioral_fidelity_verified'])

    def test_reserved_delimiters_control_chars_and_priority_prefixes_roundtrip(self):
        values = ['a|b', 'a&b', 'a→b', '1:问题', '@范围', '?未知', '\\n', '多行\n\r\t文本', '①②', '引号"与\\']
        for s in values:
            value = {'name': '符号团', 'tagline': s, 'groups': [{'scope': s,
                'rules': [{'question': s, 'requires': [s], 'choose': s, 'priority': 0},
                          {'question': '另一个问题', 'requires': [], 'choose': s, 'priority': 9}]}],
                'unknowns': [s]}
            with self.subTest(value=repr(s)):
                self.assertEqual(c.parse(c._render(value)), value)

    def test_default_priority_exception_and_same_priority_conflict_are_retained(self):
        source, ledger = fixture()
        ledger['rows'].append(dict(copy.deepcopy(ledger['rows'][1]), action='另一做法'))
        files = c.bind(ledger, source)
        rows = c.parse(files['prompt.md'])['groups'][0]['rules']
        self.assertEqual([r['priority'] for r in rows], [0, 1, 1])
        self.assertEqual([r['choose'] for r in rows], ['走草地', '走回廊', '另一做法'])
        self.assertEqual(files['semantic-projection.private.json']['unknowns'], ledger['unknowns'])

    def test_public_json_dictionary_needs_no_private_encoding_report(self):
        value = {'name': '重复团', 'tagline': '公开字典也计数。', 'groups': [{'scope': '程序符号夹具', 'rules': [
            {'question': '目标%d' % i, 'requires': ['条件，必须保存原始来源并保留全部上下文界限'],
             'choose': '完成核对以后执行指定操作', 'priority': 0} for i in range(20)]}], 'unknowns': ['其他情况未知。']}
        expanded = c._render(value)
        text, report = c.pack(expanded, len(expanded)-100, prefix=c.prefix(value))
        self.assertTrue(report['dictionary'])
        self.assertEqual(c.decode(text), expanded)
        self.assertEqual(c.parse(text), value)
        self.assertLessEqual(len(text), len(expanded)-100)
        # Every dictionary value, including delimiters/newlines if selected,
        # is a counted JSON string in the public artifact itself.
        header = text[len(c.prefix(value)):].split('\n', 1)[0]
        self.assertIsInstance(json.loads(header[len(c.LABEL):]), dict)

    def test_literal_symbols_do_not_collide_with_dictionary_keys(self):
        text = c.prefix({'name': '碰撞团', 'tagline': '①是原文。'}) + '@对象\n' + ''.join(
            '问题%d|前提，保留这段足够长的相同来源限定→原文①\n' % i for i in range(15)) + '?未知\n'
        packed, report = c.pack(text, len(text)-80, prefix=c.prefix({'name': '碰撞团', 'tagline': '①是原文。'}))
        self.assertNotIn('①', dict(report['dictionary']))
        self.assertEqual(c.decode(packed), text)

    def test_bad_escapes_separators_dictionary_and_sections_are_rejected(self):
        source, ledger = fixture()
        good = c.bind(ledger, source)['expanded.private.md']
        bad = [good.replace('路线选择|', '路线选择\\z|', 1),
               good.replace('路线选择|', '路线选择||', 1), good.rstrip('\n'),
               good+'@迟到的范围\n', good.replace('@花园路径', '?先到未知\n@花园路径', 1)]
        pre = c.prefix(c.parse(good))
        for mapping in ('{}', '{"①":"②"}', '{"x":"替换"}', '{"①":1}'):
            bad.append(pre+c.LABEL+mapping+'\n'+good[len(pre):])
        for text in bad:
            with self.subTest(text=text[-80:]), self.assertRaises((ValueError, json.JSONDecodeError)):
                c.parse(text)

    def test_invalid_quotes_roles_and_hard_budget_are_not_bypassed(self):
        source, ledger = fixture()
        for fault in ('quote', 'role', 'budget'):
            answer = copy.deepcopy(ledger)
            if fault == 'quote':
                answer['rows'][0]['decisions'][0]['quote'] = 'invented'
            elif fault == 'role':
                a = source['sources'][2]
                answer['rows'][0]['decisions'] = [{'source_id': a['id'], 'quote': a['text']}]
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                c.bind(answer, source, 1 if fault == 'budget' else 1536)

    def test_no_decisions_still_retains_unknown_boundary_and_complete_guide(self):
        source, ledger = fixture()
        ledger['rows'] = []
        files = c.bind(ledger, source)
        self.assertEqual(c.parse(files['prompt.md'])['groups'], [])
        self.assertIn(c.GUIDE, files['prompt.md'])
        self.assertEqual(c.parse(files['prompt.md'])['unknowns'], ledger['unknowns'])


if __name__ == '__main__':
    unittest.main()
