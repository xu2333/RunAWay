"""Regress the observed successful-job/still-pending-step race without network."""
import copy
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('ci_readiness_test',Path(__file__).resolve().parents[1]/'scripts/ci_readiness.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class CIReadinessTests(unittest.TestCase):
    def payload(self):
        return dict(headSha='head',databaseId=123,status='completed',conclusion='success',jobs=[
            dict(name=name,status='completed',conclusion='success',steps=[
                dict(name='Check out',number=2,status='completed',conclusion='success'),
                dict(name='Unit tests',number=5,status='completed',conclusion='success'),
                dict(name='Build wheel',number=74,status='completed',conclusion='success')])for name in('linux','mac')])
    def check(self,p):return c.assess(p,head='head',run_id=123,job_names={'linux','mac'},required_steps={'Unit tests','Build wheel'})
    def test_ready_requires_every_pinned_step_in_every_job(self):
        self.assertEqual(self.check(self.payload())['state'],'ready')
    def test_green_aggregate_with_pending_or_running_steps_waits(self):
        for status in('pending','in_progress'):
            p=self.payload();p['jobs'][1]['steps'][-1].update(status=status,conclusion='')
            self.assertEqual(self.check(p),dict(state='wait',reason='step_metadata_not_settled'))
            p['jobs'][1]['steps'][-1].update(status='completed',conclusion='success')
            self.assertEqual(self.check(p)['state'],'ready')
    def test_missing_step_or_job_cannot_vacuously_pass(self):
        for edit in('empty_steps','missing_step','missing_job'):
            p=self.payload()
            if edit=='empty_steps':p['jobs'][1]['steps']=[]
            elif edit=='missing_step':p['jobs'][1]['steps'].pop()
            else:p['jobs'].pop()
            self.assertEqual(self.check(p)['state'],'wait')
        with self.assertRaises(ValueError):c.assess(self.payload(),head='head',run_id=123,job_names={'linux','mac'},required_steps=set())
    def test_failed_or_skipped_required_step_rejects_despite_green_job(self):
        for conclusion in('failure','skipped','cancelled','timed_out'):
            p=self.payload();p['jobs'][1]['steps'][-1].update(status='completed',conclusion=conclusion)
            self.assertEqual(self.check(p)['state'],'reject')
    def test_foreign_head_run_or_duplicate_job_rejects(self):
        for key,value in(('headSha','other'),('databaseId',999)):
            p=self.payload();p[key]=value;self.assertEqual(self.check(p)['state'],'reject')
        p=self.payload();p['jobs'].append(copy.deepcopy(p['jobs'][0]));self.assertEqual(self.check(p)['state'],'reject')
    def test_incomplete_setup_waits_and_assessment_is_read_only(self):
        p=self.payload();p['jobs'][1]['steps'][0].update(status='in_progress',conclusion='');before=copy.deepcopy(p)
        self.assertEqual(self.check(p)['state'],'wait');self.assertEqual(p,before)

if __name__=='__main__':unittest.main()
