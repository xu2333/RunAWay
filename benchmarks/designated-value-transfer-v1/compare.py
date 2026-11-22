"""Fixed two-branch transfer comparison. No model calls without an explicit invocation."""
import argparse
import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Reuse the exact prior transport, browser schema, ZIP installer and fresh-project reader.
prior = runpy.run_path(str(HERE.parent / 'designated-value-v1/compare.py'))
ORDER = ('original-1', 'current-1', 'current-2', 'original-2')


def reads():
    first = [(card, ('signed', 'unsigned')[(i + block) % 2])
             for block in range(2) for i, card in enumerate(ORDER)]
    for rep, sequence in enumerate((first, reversed(first)), 1):
        for card, branch in sequence:
            yield card, branch, rep


def run(out):
    inputs = json.loads(prior['local']('node', HERE / 'materials.mjs', 'requests'))
    out.mkdir(parents=True, mode=0o700, exist_ok=False)
    record = prior['record']
    stage = 'start'
    try:
        for card in ORDER:
            stage = card
            record(out / (stage + '.intent.json'), {'kind': 'extract', 'model': prior['MODEL']})
            answer, meta = prior['codex_generate'](
                inputs[card.split('-')[0]], prior['MODEL'], timeout=180,
                schema=prior['BROWSER_SCHEMA'], system='Return the requested JSON only. No tools.')
            record(out / (card + '.usage.json'), meta)
            answer_path = out / (card + '.answer.txt')
            answer_path.write_text(answer, encoding='utf-8')
            if not meta.get('usage') or not all(isinstance(u, dict) and
                    'input_tokens' in u and 'output_tokens' in u for u in meta['usage']):
                raise ValueError('Missing extraction usage')
            view = json.loads(prior['local']('node', HERE / 'materials.mjs', 'portable', answer_path))
            record(out / (card + '.portable.json'), view)
        for card, branch, rep in reads():
            stage = f'{card}-{branch}-{rep}'
            record(out / (stage + '.intent.json'), {'kind': 'read', 'card': card, 'task': branch})
            response = prior['read_card'](out / (card + '.portable.json'), inputs['tasks'][branch])
            record(out / (stage + '.json'), response)
    except Exception as error:
        record(out / 'closed.json', {'failed_stage': stage, 'error_type': type(error).__name__,
                                     'progress': getattr(error, 'provenance', None)})
        raise
    record(out / 'closed.json', {'slots_completed': 20})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approved-new-run', type=Path, required=True)
    run(parser.parse_args().approved_new_run.resolve())
