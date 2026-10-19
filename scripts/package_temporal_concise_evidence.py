"""Seal an actual D-0028 result once; never export the approval or batch intent."""
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
    aliases = {'world.private.json': 'world.synthetic.json', 'artifacts.private.json': 'artifacts.synthetic.json', 'controls.private.json': 'controls.synthetic.json', 'jobs.json': 'jobs.json', 'deliveries.private.json': 'deliveries.synthetic.json'}
    files = {alias: proposal / n for n, alias in aliases.items()}
    files.update({'raw-report.synthetic.json': run / 'service/report.json', 'answers.synthetic.json': run / 'service/answers.json'})
    for path in (run / 'service/calls').glob('*.json'):
        if path.name.endswith(('.request.json', '.response.json', '.attempt.json', '.failure.json')): files['calls/' + path.name] = path
    for path in (proposal / 'frozen-source').rglob('*'):
        if path.is_file(): files['frozen-source/' + str(path.relative_to(proposal / 'frozen-source'))] = path
    p = json.loads((proposal / 'proposal.json').read_text()); keys = ('id', 'calls_max', 'stage_caps', 'models', 'timeout_seconds', 'cleanup_waits_seconds', 'character_budget', 'token_budget', 'selection', 'data_scope', 'standalone_memory', 'baseline', 'gates', 'reporting', 'cost_boundary', 'limits', 'source_hashes', 'input_hashes', 'sealed_archives', 'forbidden_request_ids')
    contract = {k: p[k] for k in keys}; contract.update(input_aliases=aliases, original_proposal_sha256=hashlib.sha256((proposal / 'proposal.json').read_bytes()).hexdigest(), tokenizer_sha256=p['tokenizer']['model_sha256'])
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        for name, source in files.items():
            if source.is_symlink() or not source.resolve().is_relative_to(ROOT): raise ValueError('Escaping evidence source')
            dest = base / name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, dest)
        (base / 'contract.synthetic.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
        r = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/replay_temporal_concise_evidence.py'), '--base', str(base), '--tokenizer', str(tokenizer)], capture_output=True, text=True, timeout=60)
        if r.returncode: raise ValueError('Frozen replay failed: ' + r.stderr[-3000:])
        encoded = (json.dumps(json.loads(r.stdout), ensure_ascii=False, indent=2) + '\n').encode(); (base / 'report.synthetic.json').write_bytes(encoded)
        manifest = {}
        for path in sorted(base.rglob('*')):
            if not path.is_file(): continue
            name = str(path.relative_to(base)); data = path.read_bytes()
            if not name.startswith('frozen-source/') and any(x in data.decode() for x in ('/Users/', 'human_source', 'access_token', 'refresh_token')): raise ValueError('Private metadata in evidence data')
            manifest[name] = hashlib.sha256(data).hexdigest()
        archive = ROOT / 'examples/temporal-concise-evidence.synthetic.zip'
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
            for name in manifest: output.writestr('d0028/' + name, (base / name).read_bytes())
            output.writestr('d0028/manifest.json', json.dumps(manifest, indent=2) + '\n')
        (ROOT / 'examples/temporal-concise-results.synthetic.json').write_bytes(encoded); (run / 'audit-summary.json').write_bytes(encoded)
    return {'files': len(manifest), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'external_model_calls_by_packager': 0, 'private_approval_or_intent_exported': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--run', required=True); parser.add_argument('--proposal', required=True); parser.add_argument('--tokenizer', required=True); args = parser.parse_args()
    print(json.dumps(package(args.run, args.proposal, args.tokenizer)))
