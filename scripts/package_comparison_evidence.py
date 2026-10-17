"""Export the sealed D-0016 synthetic comparison; never invoke a model."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(run, proposal, examples):
    run, proposal, examples = map(Path, (run, proposal, examples))
    report = json.loads((run / 'service/report.json').read_text())
    summary = json.loads((run / 'audit-summary.json').read_text())
    world = json.loads((proposal / 'future-fixtures.private.json').read_text())
    if world['origin'] != 'fully_synthetic' or summary['origin'] != 'fully_synthetic':
        raise ValueError('Only explicitly synthetic evidence is publishable')
    if report['status'] not in ('complete', 'stopped') or report['calls']['executions_missing_usage']:
        raise ValueError('Only a closed batch with resolved accounting is supported')
    if report['calls']['execution_records'] > 24:
        raise ValueError('Comparison cap exceeded')
    # Explicit list: no approval, central messages, workspace receipts or auth.
    files = {
        'report.synthetic.json': run / 'audit-summary.json',
        'raw-report.synthetic.json': run / 'service/report.json',
        'fresh-answers.synthetic.json': run / 'service/fresh-answers.json',
        'fixtures.synthetic.json': proposal / 'future-fixtures.private.json',
        'contract.json': proposal / 'contract.json',
        'reader-jobs.synthetic.jsonl': proposal / 'reader-jobs.jsonl',
    }
    legacy = run / 'service/legacy-answers.json'
    if legacy.exists(): files['legacy-answers.synthetic.json'] = legacy
    for path in (run / 'service/calls').glob('*.json'):
        if path.name.endswith(('.request.json', '.response.json', '.attempt.json', '.failure.json')):
            files['calls/' + path.name] = path
    for path in (proposal / 'executor-frozen-source').rglob('*'):
        if path.is_file():
            files['frozen-source/' + str(path.relative_to(proposal / 'executor-frozen-source'))] = path
    examples.mkdir(parents=True, exist_ok=True)
    archive = examples / 'comparison-evidence.synthetic.zip'
    manifest = {}
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
        for name, path in sorted(files.items()):
            if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                raise ValueError('Refusing escaping source')
            data = path.read_bytes()
            manifest[name] = hashlib.sha256(data).hexdigest()
            output.writestr('d0016/' + name, data)
        output.writestr('d0016/manifest.json', json.dumps(manifest, indent=2) + '\n')
    (examples / 'comparison-results.synthetic.json').write_bytes((run / 'audit-summary.json').read_bytes())
    return {'files': len(manifest), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'external_model_calls_by_packager': 0, 'private_approval_auth_included': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True)
    p.add_argument('--proposal', required=True)
    p.add_argument('--examples', default=str(ROOT / 'examples'))
    a = p.parse_args()
    print(json.dumps(package(a.run, a.proposal, a.examples)))
