import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/structural_report_compare.py'
spec=importlib.util.spec_from_file_location('report_compare',path);comparison=importlib.util.module_from_spec(spec);spec.loader.exec_module(comparison)


class ReportPortabilityTests(unittest.TestCase):
    def test_only_derived_macro_gets_rational_ulp_check(self):
        base=dict(paired_clusters=[dict(correct=2,planned=3)]*3,macro_cluster_accuracy=0.6666666666666668)
        actual=dict(base,macro_cluster_accuracy=0.6666666666666666);comparison.compare(base,actual)
        with self.assertRaises(ValueError):comparison.compare(base,dict(actual,macro_cluster_accuracy=0.67))
        wrong=dict(base,paired_clusters=[dict(correct=1,planned=3)]*3)
        with self.assertRaises(ValueError):comparison.compare(base,wrong)
        with self.assertRaises(ValueError):comparison.compare(dict(correct=10),dict(correct=9))


if __name__=='__main__':unittest.main()
