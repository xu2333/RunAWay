"""Pure CI readiness: a green aggregate never substitutes for completed steps."""
FAILURES={'failure','cancelled','timed_out','action_required','startup_failure','skipped','neutral','stale'}

def assess(value, *, head, run_id, job_names, required_steps):
    if not required_steps or not job_names:
        raise ValueError('Nonempty pinned job/step contract required')
    if value.get('headSha')!=head or value.get('databaseId')!=run_id:
        return dict(state='reject',reason='foreign_head_or_run')
    if value.get('conclusion') in FAILURES:
        return dict(state='reject',reason='run_failed')
    jobs=value.get('jobs',[])
    names=[j.get('name')for j in jobs]
    if len(names)!=len(set(names)) or any(n not in job_names for n in names):
        return dict(state='reject',reason='foreign_or_repeated_job')
    for job in jobs:
        if job.get('conclusion')in FAILURES:
            return dict(state='reject',reason='job_failed')
        steps=job.get('steps',[])
        if any(s.get('conclusion')in FAILURES for s in steps if s.get('name')in required_steps):
            return dict(state='reject',reason='required_step_failed')
    if value.get('status')!='completed' or value.get('conclusion')!='success' or set(names)!=set(job_names):
        return dict(state='wait',reason='aggregate_not_settled')
    for job in jobs:
        if job.get('status')!='completed' or job.get('conclusion')!='success':
            return dict(state='wait',reason='job_not_settled')
        steps=job.get('steps',[])
        step_names=[s.get('name')for s in steps]
        if len(step_names)!=len(set(step_names)):
            return dict(state='reject',reason='repeated_step')
        if not set(required_steps)<=set(step_names):
            return dict(state='wait',reason='required_step_metadata_missing')
        if any(s.get('status')!='completed' or s.get('conclusion')!='success'
               for s in steps if s.get('name')in required_steps):
            return dict(state='wait',reason='step_metadata_not_settled')
        # Also retain the existing guard for unnamed setup/checkout steps.
        if any(s.get('status')!='completed' or s.get('conclusion')!='success'
               for s in steps if type(s.get('number'))is not int or s['number']<100):
            return dict(state='wait',reason='setup_step_metadata_not_settled')
    return dict(state='ready',reason='all_pinned_jobs_and_steps_completed_successfully')
