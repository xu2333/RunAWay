"""Wire capacity and expansion calibration, not model fidelity."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owned_object_table_tests', ROOT / 'benchmarks/owned-object-table-v1/candidate.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def fixture():
    source = {'id': 's1', 'episode_id': 'toy', 'role': 'user', 'text': '这里是程序夹具；我在这些主题的选择均为甲，执行许可尚未决定。'}
    anchor = {'source_id': 's1', 'quote': source['text']}
    row = {'object_index': 0, 'question': '方案选择', 'requires': [], 'action': '甲', 'priority': 0,
           'decisions': [anchor], 'contexts': [anchor], 'supersedes': []}
    return {'schema_version': 1, 'sources': [source]}, {'version': c.VERSION, 'name': '索引小团',
        'tagline': '名字写全，条件归位。', 'objects': ['程序夹具主题'], 'rows': [row],
        'unknowns': ['未决定执行许可。']}


class ObjectTableTests(unittest.TestCase):
    def test_source_only_request_keeps_budget_and_questions_out_of_encoder(self):
        source, _ = fixture()
        request = c.make_request(source)
        body = json.loads(request['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n')[1])
        self.assertEqual(body, {'sources': source})
        with self.assertRaises(TypeError):
            c.make_request(source, 1536)

    def test_private_index_expands_before_identical_original_binding(self):
        source, wire = fixture()
        before = copy.deepcopy(wire)
        expanded = c.expand(wire)
        files = c.bind(wire, source)
        original = c.base.bind(expanded, source)
        self.assertEqual(files['prompt.md'], original['prompt.md'])
        self.assertEqual(files['portable.json'], original['portable.json'])
        self.assertNotIn('object_index', files['prompt.md'])
        self.assertIn('程序夹具主题', files['prompt.md'])
        self.assertEqual(wire, before)
        self.assertFalse(files['object-table.private.json']['annotation_semantics_verified'])

    def test_thirteenth_object_and_thirtyfirst_row_are_rejected_on_wire(self):
        for fault in ('objects', 'rows'):
            source, wire = fixture()
            if fault == 'objects':
                wire['objects'] = ['主题%d' % n for n in range(13)]
            else:
                wire['rows'] *= 31
            before = copy.deepcopy(wire)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                c.bind(wire, source)
            self.assertEqual(wire, before)

    def test_twelve_used_objects_fit_existing_group_count_without_implicit_aliases(self):
        source, wire = fixture()
        row = wire['rows'][0]
        wire['objects'] = ['主题%d' % n for n in range(12)]
        wire['rows'] = [dict(copy.deepcopy(row), object_index=n) for n in range(12)]
        expanded = c.expand(wire)
        public, _ = c.base.project(expanded, source)
        self.assertEqual(len(public['groups']), 12)
        self.assertEqual({g['scope'] for g in public['groups']}, set(wire['objects']))
        c.bind(wire, source)

    def test_undefined_boolean_or_duplicate_reference_does_not_trigger_repair(self):
        for fault in ('undefined', 'boolean', 'duplicate'):
            source, wire = fixture()
            if fault == 'undefined':
                wire['rows'][0]['object_index'] = 1
            elif fault == 'boolean':
                wire['rows'][0]['object_index'] = True
            else:
                wire['objects'] *= 2
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                c.bind(wire, source)

    def test_unknown_and_hard_budget_failure_survive_object_expansion(self):
        source, wire = fixture()
        expanded = c.expand(wire)
        self.assertEqual(expanded['unknowns'], wire['unknowns'])
        with self.assertRaises(ValueError):
            c.bind(wire, source, 1)
        wire.update(objects=[], rows=[])
        self.assertEqual(c.expand(wire)['rows'], [])
        c.bind(wire, source)


if __name__ == '__main__':
    unittest.main()
