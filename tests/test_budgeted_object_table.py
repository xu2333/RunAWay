"""Request isolation and compiler parity, not model compression performance."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


c = load('budgeted_table_tests', ROOT / 'benchmarks/budgeted-object-table-v1/candidate.py')
fixture = load('budgeted_table_fixtures', ROOT / 'tests/test_owned_object_table.py').fixture


class BudgetedTableTests(unittest.TestCase):
    def test_request_contains_only_own_source_budget_and_fixed_public_prefix(self):
        sources, _ = fixture()
        req = c.make_request(sources)
        body = json.loads(req['prompt'].split('\nSOURCE_LEDGER_INPUT_JSON:\n')[1])
        self.assertEqual(set(body), {'sources', 'budget_characters', 'fixed_header', 'fixed_guide'})
        self.assertEqual(body['sources'], sources)
        self.assertEqual(body['budget_characters'], 1536)
        self.assertEqual(body['fixed_header'], c.table.base.grouped.HEADER)
        self.assertEqual(body['fixed_guide'], c.table.base.grouped.GUIDE)
        self.assertNotEqual(req['prompt'], c.table.make_request(sources)['prompt'])

    def test_wire_and_bound_prompt_are_exactly_original_for_same_answer(self):
        sources, answer = fixture()
        self.assertEqual(c.SCHEMA, c.table.SCHEMA)
        self.assertEqual(c.VERSION, c.table.VERSION)
        self.assertEqual(c.expand(answer), c.table.expand(answer))
        self.assertEqual(c.bind(answer, sources), c.table.bind(answer, sources))

    def test_request_is_repeatable_and_does_not_mutate_source_or_schema(self):
        sources, _ = fixture()
        before, schema = copy.deepcopy(sources), copy.deepcopy(c.SCHEMA)
        req = c.make_request(sources)
        self.assertEqual(req, c.make_request(sources))
        req['schema']['properties']['name'] = {}
        self.assertEqual(c.SCHEMA, schema)
        self.assertEqual(sources, before)
        for bad in (0, -1, True, '1536'):
            with self.subTest(budget=bad), self.assertRaises(ValueError):
                c.make_request(sources, bad)

    def test_existing_capacity_and_hard_budget_failures_are_not_repaired(self):
        sources, answer = fixture()
        with self.assertRaises(ValueError):
            c.bind(answer, sources, 1)
        answer['objects'] = ['对象%d' % n for n in range(13)]
        before = copy.deepcopy(answer)
        with self.assertRaises(ValueError):
            c.bind(answer, sources)
        self.assertEqual(answer, before)


if __name__ == '__main__':
    unittest.main()
