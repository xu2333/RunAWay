"""Publish only synthetic inputs, exact JSON checkpoints and frozen code."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from runaway.card import canonical
from runaway import end_to_end_taste as et
from runaway.pipeline import write_once


def package(run, archive):
    run, archive = Path(run).resolve(), Path(archive).resolve()
    et.require(not archive.exists(), 'Do not replace a sealed evidence archive')
    report = et.read(run / 'service' / 'report.json')
    et.require(report['status'] == 'complete' and report['external_model_calls'] == 10, 'Complete real run required')
    # Last live preflight happens BEFORE the new archive joins old-call exclusion.
    p, _, _ = et.preflight(run / 'frozen')
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / 'end-to-end-taste'
        root.mkdir()
        shutil.copytree(run / 'frozen', root / 'frozen', ignore=shutil.ignore_patterns('execution-intent.json'))
        shutil.copytree(run / 'service', root / 'service')
        # Only the native JSON checkpoints, not process logs or approval receipts.
        for path in (root / 'service').rglob('*'):
            et.require(path.is_dir() or path.suffix == '.json', 'Unexpected service artifact')
        shutil.copyfile(et.ROOT / 'scripts/verify_end_to_end_taste_evidence.py', root / 'verify.py')
        manifest = {str(path.relative_to(root)): et.sha(path) for path in sorted(root.rglob('*')) if path.is_file()}
        write_once(root / 'manifest.json', manifest)
        import importlib.util
        spec = importlib.util.spec_from_file_location('end_to_end_replay', et.ROOT / 'scripts/replay_end_to_end_taste.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        verified = module.replay(root)
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
            for path in sorted(root.rglob('*')):
                if path.is_file():
                    z.write(path, str(Path('end-to-end-taste') / path.relative_to(root)))
    summary = {'kind': 'one_authored_synthetic_pair_browser_product', 'proposal_id': p['id'],
               'origin': 'fully_synthetic_histories', 'archive_sha256': et.sha(archive),
               'archive_files': len(manifest), 'request_ids': sorted(path.name.removesuffix('.request.json') for path in (run/'service'/'calls').glob('*.request.json')),
               'calls': 10, 'budget_complete_characters': et.BUDGET, 'conditions': list(et.CONDITIONS),
               'replay': verified, 'report': report,
               'characters': {pid: {'name': value['answer']['name'], 'tagline': value['answer']['tagline'],
                                    'prompt': value['bundle']['portable']['text']}
                              for pid, value in et.read(run/'service'/'products.synthetic.json').items()},
               'real_person_fidelity_verified': False, 'gpu_required': False,
               'interpretation': 'Synthetic sense check only, not RIG, population evidence, or cross-provider validation. No tuning this consumed pair.'}
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True)
    p.add_argument('--archive', required=True)
    p.add_argument('--summary', required=True)
    a = p.parse_args()
    summary = package(a.run, a.archive)
    write_once(Path(a.summary), summary)
    print(json.dumps({'archive': str(Path(a.archive).resolve()), 'files': summary['archive_files'], 'new_model_calls': 0}))


if __name__ == '__main__':
    main()
