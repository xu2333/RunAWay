"""Export the sealed D-0021 batch from an explicit synthetic-only allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def package(run, proposal, tokenizer):
    run, proposal = Path(run), Path(proposal)
    files = {'raw-report.synthetic.json': run / 'service/report.json',
             'answers.synthetic.json': run / 'service/answers.json',
             'development.synthetic.json': proposal / 'development.private.json',
             'jobs.synthetic.json': proposal / 'jobs.json',
             'runtime-package-check.json': run / 'runtime-package-check.json'}
    for p in (run / 'service/calls').glob('*.json'):
        if p.name.endswith(('.request.json', '.response.json', '.attempt.json', '.failure.json')):
            files['calls/' + p.name] = p
    for folder, source in (('runtime-source', run / 'runtime-source'), ('frozen-source', proposal / 'frozen-source')):
        for path in source.rglob('*'):
            if path.is_file():
                files[folder + '/' + str(path.relative_to(source))] = path
    config = json.loads((proposal / 'proposal.json').read_text())
    contract = {k: config[k] for k in ('id', 'calls_max', 'stage_caps', 'character_budget', 'token_budget', 'scope', 'stopping', 'source_hashes', 'input_hashes', 'sealed_prior_archives')}
    contract['original_proposal_sha256'] = hashlib.sha256((proposal / 'proposal.json').read_bytes()).hexdigest()
    contract['runtime_source_note'] = 'Complete47-module runtime package matched public commit4312176 at execution. Companion modules beyond the34 proposal-listed sources are supplemental identity evidence, not retroactively frozen approval evidence.'
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        for name, source in files.items():
            if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
                raise ValueError('Escaping evidence source')
            target = base / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        (base / 'contract.synthetic.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
        command = [sys.executable, '-B', str(ROOT / 'scripts/replay_temporal_evidence.py'), '--base', str(base), '--tokenizer', str(tokenizer)]
        replay = subprocess.run(command, text=True, capture_output=True, timeout=60)
        if replay.returncode:
            raise ValueError('Frozen replay failed: ' + replay.stderr[-2000:])
        summary = json.loads(replay.stdout)
        encoded = (json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode()
        (base / 'report.synthetic.json').write_bytes(encoded)
        archive = ROOT / 'examples/temporal-evidence.synthetic.zip'
        manifest = {}
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
            for path in sorted(base.rglob('*')):
                if path.is_file():
                    name = str(path.relative_to(base)); data = path.read_bytes()
                    if '/Users/' in data.decode('utf-8') and not name.startswith(('runtime-source/', 'frozen-source/')):
                        raise ValueError('Private filesystem path in data export')
                    manifest[name] = hashlib.sha256(data).hexdigest(); output.writestr('d0021/' + name, data)
            output.writestr('d0021/manifest.json', json.dumps(manifest, indent=2) + '\n')
        (ROOT / 'examples/temporal-results.synthetic.json').write_bytes(encoded)
        (run / 'audit-summary.json').write_bytes(encoded)
    return {'files': len(manifest), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'external_model_calls_by_packager': 0, 'private_approval_or_intent_exported': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True); parser.add_argument('--proposal', required=True); parser.add_argument('--tokenizer', required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.run, args.proposal, args.tokenizer)))
