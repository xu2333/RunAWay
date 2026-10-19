import contextlib
import copy
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from runaway import temporal as t, temporal_concise as c
from runaway.cli import main
from runaway.portable import validate_expression
from runaway.adapters import attach
from test_temporal import fixture

ROOT = Path(__file__).resolve().parents[1]


class ConciseProductTests(unittest.TestCase):
    def test_exact_tested_text_and_all_partial_contexts_survive_product_port(self):
        with zipfile.ZipFile(ROOT / 'examples/temporal-concise-evidence.synthetic.zip') as z:
            artifacts = json.loads(z.read('d0028/artifacts.synthetic.json'))
            memories = json.loads(z.read('d0028/deliveries.synthetic.json'))['memories']
        for pid, artifact in artifacts.items():
            result = c.render(artifact, 768)
            self.assertEqual(result['text'], memories[pid]['text'])
            self.assertEqual(result['required_characters'], memories[pid]['characters'])
            self.assertEqual(c.decode(result['text']), c.policy(artifact))
            self.assertEqual(c.prove(artifact)['partial_contexts'], 38)
            self.assertIsNone(result['required_tokens'])
            self.assertFalse(result['model_quality_measured'])

    def test_quoted_delimiters_negative_conditions_conflicts_and_unicode_remain_distinct(self):
        domain = '10;硬["🐈"]'; a = '快试;例外["&!"'; b = '先设计'
        sources = {'schema_version': 1, 'sources': [{'id': 's', 'episode_id': 'e', 'role': 'user', 'text':
            f'{domain}：{a}。\n{domain}：{b}。\n{domain}：若未验证且不可撤销，{b}。'}]}
        spans = t.spans(sources)
        def event(i, action, kind='regular', when=()):
            return dict(id='e'+str(i),kind=kind,domain=domain,action=action,strength=0,when_all=[dict(predicate=k,equals=v) for k,v in when],target='',span_ids=[spans[i]['id']])
        artifact = t.bind(dict(scope='引号"与行分隔\u2028🐈', events=[event(0,a),event(1,b),event(2,b,'constraint',[('未验证',True),('不可撤销',False)])],unmodeled=[]), sources)
        p = c.decode(c.encode(artifact,10000)['text'])
        self.assertEqual(p, c.policy(artifact))
        self.assertEqual(c.resolve(p,domain,{'未验证':False})['status'],'conflict')
        self.assertEqual(c.resolve(p,domain,{'未验证':True})['status'],'context_unknown')
        for x,y in itertools.product((None,True,False),repeat=2):
            ctx={k:v for k,v in [('未验证',x),('不可撤销',y)] if v is not None}
            expected=t.resolve(artifact,domain,ctx)
            self.assertEqual(c.resolve(p,domain,ctx),{k:expected[k] for k in ('status','action')})
        self.assertEqual(c.prove(artifact)['partial_contexts'],9)
        for text in [c.encode(artifact,10000)['text'].removesuffix('\n'),'made-up header\n']:
            with self.assertRaises(ValueError): c.decode(text)

    def test_whole_budget_and_explicit_domains_never_silently_drop_rules(self):
        sources,answer=fixture();artifact=t.bind(answer,sources);full=c.render(artifact,10000)
        self.assertIsNone(c.render(artifact,full['required_characters']-1)['text'])
        self.assertIsNone(c.render(artifact,10000,count=lambda _:289,budget_tokens=288)['text'])
        self.assertEqual(c.render(artifact,10000,[],lambda _:1,288)['included_domains'],[])
        partial=c.render(artifact,10000,['文件标记'])
        self.assertEqual(partial['omitted_domains'],['产品验证'])
        self.assertEqual([d['domain'] for d in c.decode(partial['text'])['domains']],['文件标记'])
        for domains in [['invented'],['文件标记','文件标记'],[{}],'文件标记']:
            with self.assertRaises(ValueError): c.render(artifact,10000,domains)
        with self.assertRaises(ValueError):c.render(artifact,10000,budget_tokens=288)
        corrupted=copy.deepcopy(artifact);corrupted['extraction']['events'][0]['action']='invented'
        with self.assertRaises(ValueError):c.render(corrupted,10000)

    def test_cli_optional_export_preserves_graph_and_existing_harness_transport(self):
        sources,answer=fixture();artifact=t.bind(answer,sources)
        with tempfile.TemporaryDirectory() as temp, patch('runaway.cli.codex_generate',side_effect=AssertionError('No model calls')):
            root=Path(temp);path=root/'artifact.json';path.write_text(json.dumps(artifact))
            with contextlib.redirect_stdout(io.StringIO()):
                main(['timeline','export',str(path),'--format','concise','--out',str(root/'compact')])
                main(['timeline','export',str(path),'--out',str(root/'default')])
                main(['timeline','export',str(path),'--format','concise','--budget-chars','1','--out',str(root/'blocked')])
            expression=validate_expression(json.loads((root/'compact/portable.json').read_text()))
            self.assertEqual(expression['text'],c.render(artifact,768)['text'])
            self.assertEqual((root/'default/prompt.md').read_text(),t.render(artifact,768)['text'])
            self.assertEqual(json.loads((root/'compact/timeline.private.json').read_text()),artifact)
            self.assertTrue((root/'blocked/timeline.private.json').exists())
            self.assertFalse((root/'blocked/portable.json').exists())
            project=root/'project';project.mkdir();attach(expression,project,['codex','claude','opencode'],False)
            for name in ['AGENTS.md','.claude/rules/runaway.md']:
                self.assertIn(expression['text'],(project/name).read_text())


if __name__=='__main__':unittest.main()
