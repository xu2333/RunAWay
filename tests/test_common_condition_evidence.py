"""Archive consistency and loss-localization checks; never fresh model evaluation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


r=load('common_condition_evidence_tests',ROOT/'scripts/replay_common_condition.py')
t=load('common_condition_trace_tests',ROOT/'scripts/inspect_common_condition.py')


class CommonConditionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=r.p.read(r.DEFAULT)
        with patch('runaway.generation.codex_generate',side_effect=AssertionError('No service'))as backend:
            cls.report=r.check()
        backend.assert_not_called()

    def reject(self,data):
        with self.assertRaises((ValueError,KeyError,TypeError,AssertionError)):r.replay(data)

    def test_actual_archive_reconstructs_counters_usage_and_full_120_case_denominators(self):
        report=self.report
        self.assertEqual(report['actual_attempts'],self.data['status']['attempt_reservations'])
        self.assertEqual(report['actual_children'],self.data['status']['local_cli_child_intents'])
        self.assertEqual(report['known_usage'],self.data['status']['known_usage'])
        self.assertEqual(report['summary'],self.data['status']['scores'])
        self.assertEqual(len(report['all_case_transitions']),120)
        self.assertEqual(sum(report['paired_transitions'].values()),120)
        for method in r.p.METHODS:
            cell=report['summary']['methods'][method]
            self.assertEqual([cell['strict_eight_answers'][k]['planned']for k in('joint','known','unknown')],[120,56,64])
            self.assertEqual(cell['old_anchors']['joint']['planned'],88)
            self.assertEqual(cell['crossed_unknown']['joint']['planned'],32)

    def test_sources_questions_views_references_and_implementation_are_exact(self):
        for name in r.p.FILES:
            data=copy.deepcopy(self.data);data['prepared_files'][name]={};self.reject(data)
        for key in('scientific_source_ref','input_manifest_sha256'):
            data=copy.deepcopy(self.data);data[key]='foreign';self.reject(data)

    def test_raw_value_and_changed_valid_answers_cannot_silently_replace_archive(self):
        record=next((x for x in self.data['records']if x['raw_present']),None)
        if record is None:
            self.assertTrue(self.data['status']['stop']);return
        data=copy.deepcopy(self.data);data['records'][0]['raw']+='changed';self.reject(data)
        pair=next(((rec,row)for rec in self.data['records']if rec['kind']in('full','read')and rec['state']=='completed'
                   for row in r.p.inputs()['rows']if row['person']==rec['profile']and row['gold']!='U'
                   and all(r.e.parse_answer(rec['raw']).get(q)==row['gold']for q in row['query_ids'])),None)
        if pair is None:self.assertTrue(self.data['status']['stop']);return
        rec,row=pair;data=copy.deepcopy(self.data);rec=data['records'][rec['slot']-1]
        a=r.e.parse_answer(rec['raw']);a[row['query_ids'][0]]='U';rec['raw']=json.dumps(a,ensure_ascii=False)
        rec['raw_value_sha256']=r.p.digest(rec['raw']);self.reject(data)

    def test_request_parent_method_and_budget_routing_cannot_change(self):
        for fault in('request','method','generation','budget'):
            data=copy.deepcopy(self.data);rec=next((x for x in data['records']if x['kind']=='read'),data['records'][0])
            if fault=='request':
                rec['request']['prompt']+='foreign';rec['request_sha256']=r.p.digest(rec['request']);rec['execution_record']['request_sha256']=rec['request_sha256']
            else:
                rec[fault]='foreign';rec['execution_record'][fault]='foreign'
            self.reject(data)

    def test_both_layout_denominators_cannot_shrink(self):
        for group,method,endpoint in(('methods',r.p.METHODS[0],'strict_eight_answers'),('methods',r.p.METHODS[1],'strict_eight_answers')):
            data=copy.deepcopy(self.data);data['status']['scores'][group][method][endpoint]['joint']['planned']-=1;self.reject(data)
        for fault in('usage','attempt','child','counter_boolean','open'):
            data=copy.deepcopy(self.data)
            if fault=='usage':data['status']['known_usage']['total_tokens']=data['status']['known_usage'].get('total_tokens',0)+1
            elif fault=='attempt':data['status']['attempt_reservations']-=1
            elif fault=='child':data['records'][0]['local_cli_child_intent']=1
            elif fault=='counter_boolean':data['status']['local_cli_child_intents']=True
            else:data['status']['scope_closed']=False
            self.reject(data)

    def test_private_fields_and_unsupported_claims_are_rejected(self):
        for key in r.FALSE_CLAIMS:
            data=copy.deepcopy(self.data);data[key]=True;self.reject(data)
        data=copy.deepcopy(self.data);data['human_authorization']='PRIVATE';self.reject(data)
        data=copy.deepcopy(self.data);data['records'][0]['runtime_path']='PRIVATE';self.reject(data)
        data=copy.deepcopy(self.data);data['records'][0]['artifact']={'prompt':'invented'};self.reject(data)

    def test_missing_products_are_separate_from_new_observed_losses(self):
        good=dict(correct=True,missing=False);wrong=dict(correct=False,missing=False);absent=dict(correct=False,missing=True)
        for a,b,result in((good,good,'kept'),(wrong,good,'recovered'),(good,wrong,'new_observed_loss'),(wrong,wrong,'both_observed_fail'),
                          (absent,good,'baseline_missing'),(good,absent,'candidate_missing'),(absent,absent,'both_missing')):
            self.assertEqual(r.transition(a,b),result)

    def test_loss_categories_distinguish_unknown_wrong_choice_and_false_certainty(self):
        for gold,values,kind in(('A',[None,'U'],'missing'),('A',['U']*8,'all_unknown_from_known'),('A',['A','U'],'intermittent_unknown_from_known'),
                                 ('A',['B','U'],'mixed_unknown_and_different_choice'),('A',['B','A'],'different_choice_from_known'),('U',['A','U'],'choice_when_reference_unknown')):
            self.assertEqual(r.loss_kind(gold,values),kind)
        with self.assertRaises(ValueError):r.loss_kind('A',[])

    def test_crossed_case_trace_retains_full_episode_roles_and_original_parent_card(self):
        cell=next(c for c in self.report['all_case_transitions']if c['person']=='otter'and c['cohort']=='crossed_time_material')
        before=r.p.digest(self.data);value=t.trace(self.data,self.report,'otter',cell['case'],r.p.METHODS[0],0)
        self.assertEqual(len(value['complete_related_source_episodes']),12)
        self.assertEqual({s['role']for s in value['complete_related_source_episodes']},{'user','assistant','tool','context'})
        view=next(v for v in self.data['prepared_files']['views.public.json']if(v['profile'],v['method'],v['generation'])==('otter',r.p.METHODS[0],0))
        self.assertEqual(value['public_view'],view['prompt']);self.assertEqual(len(value['public_queries']),2)
        self.assertEqual(value['answers_by_read_and_order'],[cell[r.p.METHODS[0]]['answers_by_generation'][0][:2],cell[r.p.METHODS[0]]['answers_by_generation'][0][2:]])
        self.assertEqual(r.p.digest(self.data),before);self.assertEqual(value['new_service_calls'],0)

    def test_source_id_trace_expands_refs_without_changing_inherited_card(self):
        cell=next(c for c in self.report['all_case_transitions']if c['person']=='tansy'and c['cohort']=='crossed_time_material')
        value=t.trace(self.data,self.report,'tansy',cell['case'],r.p.METHODS[1],1)
        self.assertIsNotNone(value['deterministically_resolved_graph'])
        self.assertNotEqual(value['inherited_original_raw_graph'],value['deterministically_resolved_graph'])
        self.assertEqual(value['restored_public_projection'],r.p.factor_codec.dense.decode(value['inherited_flat_public_card']))

    def test_factored_view_restores_the_same_parent_and_carries_its_own_guide(self):
        for person in r.p.PROFILES:
            for generation in(0,1):
                case=next(c['case']for c in self.report['all_case_transitions']if c['person']==person and c['cohort']=='scope_not_established')
                flat=t.trace(self.data,self.report,person,case,'flat',generation)
                factored=t.trace(self.data,self.report,person,case,'factored',generation)
                self.assertEqual(flat['inherited_original_raw_graph'],factored['inherited_original_raw_graph'])
                self.assertEqual(flat['inherited_flat_public_card'],flat['public_view'])
                self.assertEqual(factored['restored_public_projection'],flat['restored_public_projection'])
                self.assertIn(r.p.factor_codec.LABEL,factored['public_view'])
                self.assertLessEqual(factored['public_characters'],768)
                self.assertEqual((flat['whole_character_ceiling'],factored['whole_character_ceiling']),(1536,768))
        for rec in self.data['records']:
            if rec['kind']!='read':continue
            payload=json.loads(rec['request']['prompt'].split('READER_INPUT_JSON:\n',1)[1])
            view=next(v for v in self.data['prepared_files']['views.public.json']if(v['profile'],v['method'],v['generation'])==(rec['profile'],rec['method'],rec['generation']))
            self.assertEqual(payload['material'],view['prompt'])
            self.assertNotIn('restored_public_projection',rec['request']['prompt'])

    def test_opposite_generation_changes_and_invalid_trace_coordinates_are_visible(self):
        cell={'gold':'A',r.p.METHODS[0]:{'answers_by_generation':[['A']*4,['U']*4]},r.p.METHODS[1]:{'answers_by_generation':[['U']*4,['A']*4]}}
        self.assertEqual(r.generation_transition(cell,0),'new_observed_loss');self.assertEqual(r.generation_transition(cell,1),'recovered')
        for g in('0','1'):self.assertEqual(sum(self.report['paired_transitions_by_generation'][g].values()),120)
        for args in(('foreign','0_cross_0_0',r.p.METHODS[0],0),('otter','foreign',r.p.METHODS[0],0),
                     ('tansy','0_cross_0_0','foreign',0),('otter','0_cross_0_0',r.p.METHODS[0],2)):
            with self.assertRaises(ValueError):t.trace(self.data,self.report,*args)


if __name__=='__main__':unittest.main()
