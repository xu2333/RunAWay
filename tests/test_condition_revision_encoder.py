"""Author fixtures for explicit condition retirement;not model fidelity results."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


m = load('condition_revision_test_candidate', ROOT / 'benchmarks/condition-revision-graph-v1/candidate.py')


def example():
    source = dict(schema_version=1, sources=[
        dict(id='intro', role='user', text='对象风筝的方案是手绘分镜与文字提纲；以下说当前方式。'),
        dict(id='pair', role='user', text='风筝在仅本地演练、材料齐备、余量≥8分钟时我选手绘分镜；仅本地演练、材料齐备、余量<8分钟时我选文字提纲。'),
        dict(id='higher', role='user', text='风筝只把第一条条件余量≥8分钟替换为余量≥13分钟，继续手绘分镜，其余前提不改。'),
        dict(id='lower', role='user', text='风筝只把第二条条件余量<8分钟替换为余量<13分钟，继续文字提纲，其余前提不改。'),
        dict(id='past', role='user', text='风筝确实已经实施过手绘分镜，这是既往实施事实。'),
        dict(id='rename', role='user', text='风筝现改名纸鸢，仍然同一项，不是副本。')])
    for item in source['sources']: item['episode_id']='kite'
    ref = lambda sid:dict(source_id=sid)
    def base(key, action, condition, kind='choice'):
        return dict(id=key,kind='base',target_kind=kind,object_index=0,question='方式' if kind=='choice' else '既往实施',
            requires=[dict(text=t,evidence=[ref('pair')])for t in ('仅本地演练','材料齐备',condition)] if condition else [],
            action=action,priority=0,decisions=[ref('pair' if kind=='choice' else 'past')],contexts=[ref('intro')],order_split=None)
    nodes=[base('high','手绘分镜','余量≥8分钟'),base('low','文字提纲','余量<8分钟'),base('history','手绘分镜',None,'status')]
    for key,parent,old,new,sid in (('high_new','high','余量≥8分钟','余量≥13分钟','higher'),('low_new','low','余量<8分钟','余量<13分钟','lower')):
        nodes.append(dict(id=key,kind='condition_revision',parent_id=parent,
            edits=[dict(parent_condition=old,replacement=dict(text=new,evidence=[ref(sid)]))],
            decisions=[ref(sid)],contexts=[ref('intro')],relation_evidence=[ref(sid)]))
    ownership={'intro':[],'pair':['high','low'],'higher':['high_new'],'lower':['low_new'],'past':['history'],'rename':[]}
    answer=dict(version=m.VERSION,name='小纸鸢',tagline='只换门槛，不换抽屉。',objects=['纸鸢'],nodes=nodes,
        unknowns=['缺关键前提及未覆盖组合未知。'],derived_node_ids=[],
        object_aliases=[dict(id='alias',object_index=0,canonical='纸鸢',alias='风筝',evidence=[ref('rename')])],
        source_accounting={sid:dict(kind='direct_choice' if ids else 'no_choice',node_ids=ids,
            alias_ids=['alias']if sid=='rename'else[],reason='作者构造的协议夹具，不是自动提炼。')for sid,ids in ownership.items()})
    return source,answer


class ConditionRevisionEncoderTests(unittest.TestCase):
    def test_condition_only_update_retires_two_parents_and_preserves_other_fields(self):
        source,answer=example();files=m.bind(answer,source,1536);trace=files['condition-revision.private.json']
        self.assertEqual(trace['retired_node_ids'],['high','low'])
        self.assertEqual(set(trace['active_node_ids']),{'high_new','low_new','history'})
        rows={r['question']+r['action']:r for r in trace['ledger']['rows']}
        high=rows['方式手绘分镜'];self.assertEqual([c['text']for c in high['requires']],['仅本地演练','材料齐备','余量≥13分钟'])
        self.assertEqual(high['priority'],0);self.assertEqual(high['object'],'纸鸢（又名风筝）')
        self.assertFalse(trace['edge_semantics_verified']);self.assertFalse(files['summary.private.json']['behavioral_fidelity_verified'])

    def test_partial_update_does_not_globally_erase_other_choice_in_same_message(self):
        source,answer=example();answer['nodes']=[n for n in answer['nodes']if n['id']!='low_new']
        source['sources'][3]['text']='这条只补充背景，没有新的选择。'
        answer['source_accounting']['lower'].update(kind='no_choice',node_ids=[])
        trace=m.bind(answer,source,1536)['condition-revision.private.json']
        self.assertIn('low',trace['active_node_ids']);self.assertNotIn('high',trace['active_node_ids'])
        self.assertEqual(len(trace['ledger']['rows']),3)

    def test_guard_deletion_is_local_and_preserves_gate_time_and_past_status(self):
        source,answer=example();source['sources'][2]['text']='风筝第一条现在不再需要材料齐备；仍选手绘分镜，其余前提不改。'
        node=answer['nodes'][3];node['edits']=[dict(parent_condition='材料齐备',replacement=None)]
        trace=m.bind(answer,source,1536)['condition-revision.private.json']
        high=next(r for r in trace['ledger']['rows']if r['question']=='方式'and r['action']=='手绘分镜')
        low=next(r for r in trace['ledger']['rows']if r['question']=='方式'and r['action']=='文字提纲')
        self.assertEqual([c['text']for c in high['requires']],['仅本地演练','余量≥8分钟'])
        self.assertIn('材料齐备',[c['text']for c in low['requires']])
        self.assertEqual(next(r for r in trace['ledger']['rows']if r['question']=='既往实施')['action'],'手绘分镜')

    def test_undefined_or_duplicate_predicate_edits_fail_without_repair(self):
        for fault in ('unknown','duplicate','no_change','same_text_new_evidence'):
            source,answer=example();node=answer['nodes'][3]
            if fault=='unknown':node['edits'][0]['parent_condition']='来源没有的门槛'
            elif fault=='duplicate':node['edits']*=2
            else:node['edits'][0]['replacement']['text']='余量≥8分钟'
            # Same text with different evidence is not a logical condition change.
            with self.subTest(fault=fault):
                if fault=='no_change':
                    node['edits'][0]['replacement']=copy.deepcopy(answer['nodes'][0]['requires'][-1])
                with self.assertRaises(ValueError):m.bind(answer,source,1536)

    def test_action_object_question_and_priority_cannot_be_overridden_by_condition_edge(self):
        for field,value in (('action','文字提纲'),('object_index',1),('question','实施'),('priority',9),('order_split',None)):
            source,answer=example();answer['nodes'][3][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):m.bind(answer,source,1536)

    def test_future_reused_or_past_status_parent_rejects(self):
        for fault in ('future','retired','status'):
            source,answer=example()
            if fault=='future':answer['nodes'][3]['parent_id']='low_new'
            elif fault=='status':answer['nodes'][3]['parent_id']='history'
            else:answer['nodes'][4]['parent_id']='high'
            with self.subTest(fault=fault),self.assertRaises(ValueError):m.bind(answer,source,1536)

    def test_role_source_and_relation_timing_are_still_checked(self):
        for fault in ('source','assistant','early','late'):
            source,answer=example();node=answer['nodes'][3]
            if fault=='source':node['decisions'][0]['source_id']='outside'
            elif fault=='assistant':source['sources'][2]['role']='assistant';answer['source_accounting'].pop('higher')
            elif fault=='early':node['relation_evidence']=[dict(source_id='pair')]
            else:node['relation_evidence']=[dict(source_id='rename')]
            with self.subTest(fault=fault),self.assertRaises(ValueError):m.bind(answer,source,1536)

    def test_accounting_alias_and_whole_budget_checks_are_not_weakened(self):
        for fault in ('accounting','alias','budget'):
            source,answer=example()
            if fault=='accounting':answer['source_accounting']['higher']['node_ids']=[]
            elif fault=='alias':answer['object_aliases'][0]['alias']='不在原文的名字'
            else: answer['unknowns']=[''.join(chr(0x4e00+j*160+i)for i in range(160))for j in range(4)]
            with self.subTest(fault=fault),self.assertRaises(ValueError):m.bind(answer,source,300 if fault=='budget' else 1536)

    def test_source_only_request_has_new_schema_without_questions_or_fixture(self):
        source,answer=example();request=m.make_request(source,1536)
        self.assertIn('condition_revision',str(request['schema']))
        self.assertEqual(request['schema']['properties']['version']['enum'],[m.VERSION])
        self.assertNotIn('high_new',request['prompt']);self.assertNotIn('query_ids',request['prompt'])
        self.assertNotIn('source_accounting',request['prompt'].split('GRAPH_INPUT_JSON:\n')[1])

    def test_formal_relation_evidence_does_not_certify_the_semantic_edit(self):
        source,answer=example()
        # The user only changed the threshold,not the rehearsal premise. An
        # incorrect model edge can nevertheless cite the right user message.
        answer['nodes'][3]['edits']=[dict(parent_condition='仅本地演练',replacement=None)]
        files=m.bind(answer,source,1536)
        self.assertFalse(files['condition-revision.private.json']['edge_semantics_verified'])
        self.assertFalse(files['summary.private.json']['behavioral_fidelity_verified'])

    def test_no_condition_edges_preserve_the_existing_source_id_public_card(self):
        fixture=load('condition_revision_legacy_fixture',ROOT/'tests/test_source_id_initial_encoder.py')
        source,_,old=fixture.example();expected=m.renderer.bind(old,source,1536)['prompt.md']
        answer=copy.deepcopy(old);answer['version']=m.VERSION
        self.assertEqual(m.bind(answer,source,1536)['prompt.md'],expected)

    def test_action_after_condition_revision_keeps_the_new_and_untouched_conditions(self):
        source,answer=example()
        source['sources'].append(dict(id='action',episode_id='kite',role='user',text='刚才高分支的新条件继续；只改动作，现在选文字提纲。'))
        answer['nodes'].append(dict(id='action_new',kind='action_revision',parent_id='high_new',action='文字提纲',
            decisions=[dict(source_id='action')],contexts=[dict(source_id='intro')],
            relation_evidence=[dict(source_id='action')],order_split=None))
        answer['source_accounting']['action']=dict(kind='direct_choice',node_ids=['action_new'],alias_ids=[],reason='作者构造的动作更新。')
        trace=m.bind(answer,source,1536)['condition-revision.private.json']
        self.assertEqual(set(trace['retired_node_ids']),{'high','low','high_new'})
        row=next(r for r in trace['ledger']['rows']if any(a['source_id']=='action'for a in r['decisions']))
        self.assertEqual(row['action'],'文字提纲')
        self.assertEqual([c['text']for c in row['requires']],['仅本地演练','材料齐备','余量≥13分钟'])

    def test_condition_revision_inherits_execution_annotation_without_rewriting_status(self):
        source,answer=example()
        source['sources'][0]['text']+='手绘分镜是独立完整的方法名。'
        source['sources'][1]['text']=source['sources'][1]['text'].replace('选手绘分镜','选先手绘分镜')
        answer['nodes'][0]['action']='先手绘分镜'
        answer['nodes'][0]['order_split']=dict(core_action='手绘分镜',core_evidence=[dict(source_id='intro')],execution_question='执行先后')
        answer['source_accounting']['higher']['kind']='contextual_choice'
        files=m.bind(answer,source,1536);trace=files['condition-revision.private.json']
        self.assertEqual(len(trace['bindings']),1)
        value=m.dense.parse(m.renderer.restore(files['prompt.md']))
        rules=[r for g in value['groups']for r in g['rules']]
        self.assertTrue(any(r['question']=='执行先后'and r['choose']=='先手绘分镜'for r in rules))
        self.assertTrue(any(r['question']=='既往实施'and r['choose']=='手绘分镜'for r in rules))


if __name__=='__main__':unittest.main()
