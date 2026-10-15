"""Browser artifacts must work unchanged with the installed Python core."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from runaway import adapters
from runaway.portable import validate_expression
from runaway.profile import validate_profile

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Browser interoperability requires Node 22+')
class BrowserInteropTests(unittest.TestCase):
    def test_browser_profile_and_portable_validate_and_attach(self):
        script = """
import {readFileSync} from 'node:fs';
import {makeBundle} from './web/dist/core.mjs';
const d=JSON.parse(readFileSync('./web/dist/demo.json','utf8'));
process.stdout.write(JSON.stringify(await makeBundle(d.answer,d.sources)));
"""
        result = subprocess.run(['node', '--input-type=module', '-e', script], cwd=ROOT,
                                text=True, capture_output=True, check=True)
        bundle = json.loads(result.stdout)
        validate_profile(bundle['profile'])
        validate_expression(bundle['portable'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adapters.attach(bundle['portable'], root, ['codex', 'claude', 'opencode'])
            self.assertIn(bundle['portable']['text'], (root / 'AGENTS.md').read_text())
            self.assertIn(bundle['portable']['text'], (root / '.claude/rules/runaway.md').read_text())


if __name__ == '__main__':
    unittest.main()
