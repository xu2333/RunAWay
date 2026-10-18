"""Seal D-0023 synthetic evidence once, excluding approval, intents and local paths."""
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


def package(run, proposal, tokenizer, profile='scale'):
    profiles = {'scale': ('d0023', 'temporal-scale'), 'conflict_repair': ('d0026', 'temporal-conflict-repair'),
                'conflict_transfer': ('d0027', 'temporal-conflict-transfer')}
    if profile not in profiles: raise ValueError('Unknown frozen packaging profile')
    prefix, bundle = profiles[profile]
    run, proposal = Path(run), Path(proposal)
    files = {'raw-report.synthetic.json': run / 'service/report.json',
        'answers.synthetic.json': run / 'service/answers.json',
        'world.synthetic.json': proposal / 'world.private.json', 'jobs.json': proposal / 'jobs.json',
        'prior-controls.synthetic.json': proposal / 'prior-controls.private.json'}
    for path in (run / 'service/calls').glob('*.json'):
        if path.name.endswith(('.request.json', '.response.json', '.attempt.json', '.failure.json')):
            files['calls/' + path.name] = path
    for path in (proposal / 'frozen-source').rglob('*'):
        if path.is_file(): files['frozen-source/' + str(path.relative_to(proposal / 'frozen-source'))] = path
    config = json.loads((proposal / 'proposal.json').read_text())
    keys = ('id', 'calls_max', 'stage_caps', 'models', 'character_budget', 'token_budget', 'timeout_seconds', 'cleanup_waits_seconds', 'history_characters', 'selection', 'data_scope', 'prior_controls', 'gates', 'reporting', 'cost_boundary', 'source_hashes', 'input_hashes', 'sealed_archives', 'forbidden_request_ids')
    contract = {k: config[k] for k in keys}
    contract['original_proposal_sha256'] = hashlib.sha256((proposal / 'proposal.json').read_bytes()).hexdigest()
    contract['input_aliases'] = {'world.private.json': 'world.synthetic.json', 'jobs.json': 'jobs.json', 'prior-controls.private.json': 'prior-controls.synthetic.json'}
    contract['tokenizer_sha256'] = config['tokenizer']['model_sha256']
    if profile != 'scale': contract['replay_profile'] = profile
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        for name, source in files.items():
            if source.is_symlink() or not source.resolve().is_relative_to(ROOT): raise ValueError('Escaping evidence source')
            target = base / name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        (base / 'contract.synthetic.json').write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/replay_temporal_scale_evidence.py'), '--base', str(base), '--tokenizer', str(tokenizer)], capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError('Frozen replay failed: ' + result.stderr[-3000:])
        summary = json.loads(result.stdout); encoded = (json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode()
        (base / 'report.synthetic.json').write_bytes(encoded)
        manifest = {}
        # Complete privacy validation precedes exclusive archive creation.
        for path in sorted(base.rglob('*')):
            if not path.is_file(): continue
            name = str(path.relative_to(base)); data = path.read_bytes()
            if not name.startswith('frozen-source/') and any(x in data.decode() for x in ('/Users/', 'human_source', 'access_token', 'refresh_token')):
                raise ValueError('Private metadata in evidence data')
            manifest[name] = hashlib.sha256(data).hexdigest()
        archive = ROOT / ('examples/' + bundle + '-evidence.synthetic.zip')
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as output:
            for name in manifest: output.writestr(prefix + '/' + name, (base / name).read_bytes())
            output.writestr(prefix + '/manifest.json', json.dumps(manifest, indent=2) + '\n')
        (ROOT / ('examples/' + bundle + '-results.synthetic.json')).write_bytes(encoded)
        (run / 'audit-summary.json').write_bytes(encoded)
    return {'files': len(manifest), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'external_model_calls_by_packager': 0, 'private_approval_or_intent_exported': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True); parser.add_argument('--proposal', required=True); parser.add_argument('--tokenizer', required=True)
    args = parser.parse_args(); print(json.dumps(package(args.run, args.proposal, args.tokenizer)))
