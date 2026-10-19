"""Portable data audit plus the five unchanged frozen non-float tests."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import unittest

from structural_report_compare import compare


def verify(source):
    source=Path(source).resolve();sys.path.insert(0,str(source))
    from runaway import structural_dual as bench
    if not Path(bench.__file__).resolve().is_relative_to(source):raise ValueError('Wrong source imported')
    spec=importlib.util.spec_from_file_location('frozen_structural_tests',source/'tests/test_structural_dual.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite=unittest.TestSuite()
    for cls in (module.OracleTests,module.FrozenBenchmarkTests):
        for name in unittest.defaultTestLoader.getTestCaseNames(cls):
            if name!='test_program_audit_replays_without_service_or_old_template_oracle':suite.addTest(cls(name))
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful() or result.testsRun!=5:raise ValueError('Frozen non-float tests failed')
    data=source/'examples/structural-dual';plan=json.loads((data/'plan.synthetic.json').read_text())
    for split in ('development','holdout'):
        world,expected,policies=bench.build_split(plan,split)
        report,records=bench.audit_split(plan,world,expected,policies)
        original=json.loads((data/(split+'-report.synthetic.json')).read_text())
        for job in original['reader_jobs']:
            job['whole_memory_lengths']['actual_local_vocabulary_tokens']=None;job['canonical_request_lengths']['actual_local_vocabulary_tokens']=None
        for rows in original['complete_program_output_lengths'].values():
            for row in rows.values():row['actual_local_vocabulary_tokens']=None
        compare(original,report)
        if not report['passed'] or records!=json.loads((data/(split+'-program-records.synthetic.json')).read_text()):raise ValueError('Raw predictions or original gates changed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args();verify(args.source)
