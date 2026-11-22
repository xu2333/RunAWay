"""Run the frozen 12-slot comparison once, after separate approval and exact-commit CI."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from runaway.generation import codex_generate, run_bounded
from runaway.selfplay import BROWSER_SCHEMA

MODEL = 'gpt-6.1-sol'
ORDER = ('original-1', 'candidate-1', 'candidate-2', 'original-2')


def local(*args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, timeout=40)


def record(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def install(project, work, portable):
    bundle = work / 'card.zip'
    local('node', 'scripts/export_harness.mjs', '--target', 'codex', '--portable', portable, '--out', bundle)
    with ZipFile(bundle) as archive:
        archive.extractall(work / 'bundle')
    local('git', 'init', '-q', project)
    local('node', work / 'bundle/install.mjs', '--project', project)
    if json.loads(portable.read_text())['text'] not in (project / 'AGENTS.md').read_text():
        raise ValueError('Installed project lost portable card bytes')


def read_card(portable, task):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        project = work / 'project'
        install(project, work, portable)
        args = ['codex', 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
                '--sandbox', 'read-only', '--json', '-m', MODEL, '-C', str(project),
                '--enable', 'skip_host_skill_discovery', '-c', 'memories.use_memories=false',
                '-c', 'memories.generate_memories=false', '-c', 'web_search="disabled"',
                '-c', 'mcp_servers={}', '-c', 'approval_policy="never"']
        for feature in ('shell_tool', 'multi_agent', 'multi_agent_v2', 'apps', 'plugins', 'hooks',
                        'browser_use', 'computer_use', 'image_generation', 'view_image', 'skill_search'):
            args.extend(['--disable', feature])
        result = run_bounded(args + ['-'], task, 180)
        result.check_returncode()
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        answers, usage = [], []
        for event in events:
            kind = event['type']
            if kind in ('error', 'turn.failed'):
                raise ValueError('Codex reported failure')
            if kind == 'turn.completed':
                usage.append(event.get('usage'))
            item = event.get('item', {})
            if item.get('type') == 'error' and item.get('message', '').startswith('Under-development features enabled:'):
                continue
            if item and item.get('type') not in ('reasoning', 'agent_message'):
                raise ValueError('Unexpected Codex item')
            if kind == 'item.completed' and item.get('type') == 'agent_message':
                answers.append(item['text'])
        if not answers or not usage or not all(isinstance(u, dict) and 'input_tokens' in u and 'output_tokens' in u for u in usage):
            raise ValueError('Incomplete read')
        return {'answer': answers[-1], 'usage': usage}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approved-new-run', type=Path, required=True,
                        help='new, unused evidence directory for an authorized run')
    out = parser.parse_args().approved_new_run.resolve()
    inputs = json.loads(local('node', HERE / 'materials.mjs', 'requests'))
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    stage = 'start'
    try:
        for card in ORDER:
            stage = card
            record(out / (card + '.intent.json'), {'model': MODEL, 'kind': 'extract'})
            answer, meta = codex_generate(inputs[card.split('-')[0]], MODEL, timeout=180,
                                          schema=BROWSER_SCHEMA, system='Return the requested JSON only. No tools.')
            record(out / (card + '.usage.json'), meta)
            answer_path = out / (card + '.answer.txt')
            answer_path.write_text(answer, encoding='utf-8')
            if not meta.get('usage') or not all(isinstance(u, dict) and 'input_tokens' in u and 'output_tokens' in u for u in meta['usage']):
                raise ValueError('Missing extraction usage')
            portable = json.loads(local('node', HERE / 'materials.mjs', 'portable', answer_path))
            record(out / (card + '.portable.json'), portable)
        for repeat, order in enumerate((ORDER, reversed(ORDER)), 1):
            for card in order:
                stage = f'{card}-read-{repeat}'
                record(out / (stage + '.intent.json'), {'model': MODEL, 'card': card})
                record(out / (stage + '.json'), read_card(out / (card + '.portable.json'), inputs['task']))
    except Exception as exc:
        record(out / 'closed.json', {'failed_stage': stage, 'error_type': type(exc).__name__,
                                     'progress': getattr(exc, 'provenance', None)})
        raise
    record(out / 'closed.json', {'slots_completed': 12})


if __name__ == '__main__':
    main()
