import importlib.util
import unittest
from collections import Counter
from pathlib import Path

from tests.test_real_model_selection_transfer import p, fixture

path = Path(__file__).resolve().parents[1] / 'benchmarks/real-selection-name-extraction-v1/encoder.py'
spec = importlib.util.spec_from_file_location('selection_encoder', path)
encoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(encoder)


class SelectionNameTests(unittest.TestCase):
    def test_annotation_only_changes_system_on_source_only_request(self):
        _, original, _ = p.prepare(fixture())
        request = encoder.candidate_request(original)
        self.assertEqual(request, dict(original, system=original['system'] + '\n' + encoder.GUIDANCE))
        for term in ('aa index', 'qwen', '榜单', '排名', '校准', '冻结', '同家族'):
            self.assertNotIn(term, encoder.GUIDANCE.casefold())
        self.assertEqual(Counter(encoder.DELIVERIES), {arm: 2 for arm in encoder.EXTRACTIONS})

    def test_ranking_and_independence_cannot_offset_each_other(self):
        criteria = dict.fromkeys(('quality','population','calibration','timing','independence','ranking'), 'met')
        self.assertTrue(encoder.endpoints(criteria)['core_and_ranking'])
        criteria['ranking'] = 'partial'
        self.assertEqual(encoder.endpoints(criteria), {'core': True, 'core_and_ranking': False})
        criteria.update(ranking='met', independence='absent')
        self.assertFalse(encoder.endpoints(criteria)['core'])
