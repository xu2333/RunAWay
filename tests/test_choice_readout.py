import copy
import json
import unittest
from runaway.choice_reader import make_request,decode_response

Q=[{'id':'q01','scenario':'同一个需求','options':{'A':'先做小样','B':'先理结构','C':'先访谈'}},
   {'id':'q02','scenario':'同一个需求','options':{'A':'先访谈','B':'先做小样','C':'先理结构'}}]

class ChoiceReadoutTests(unittest.TestCase):
    def test_text_tracks_action_across_position_change(self):
        result=decode_response(Q,{'q01':'先做小样','q02':'先做小样'},answer_format='text')
        self.assertEqual(result,{'q01':'A','q02':'B'})
        self.assertEqual(decode_response(Q,{'q01':'U','q02':'U'},answer_format='text'),{'q01':'U','q02':'U'})

    def test_literal_choice_matching_never_repairs_answers(self):
        for bad in ['先做小样。','A','我觉得先做小样',' 先做小样']:
            with self.assertRaises(ValueError):decode_response(Q,{'q01':bad,'q02':'U'},answer_format='text')
        with self.assertRaises(ValueError):decode_response(Q,{'q01':'U'},answer_format='text')
        self.assertEqual(decode_response(Q,{'q01':'U'},answer_format='text',allow_missing=True),{'q01':'U'})

    def test_ambiguous_or_reserved_option_text_rejected(self):
        for duplicate in ['先做小样','U']:
            q=copy.deepcopy(Q);q[0]['options']['B']=duplicate
            with self.assertRaises(ValueError):make_request('',q,answer_format='text')
        with self.assertRaises(ValueError):make_request('',Q,answer_format='semantic_guess')

    def test_label_default_is_unchanged_and_material_queries_identical(self):
        label=make_request('记忆',Q);explicit=make_request('记忆',Q,answer_format='label');text=make_request('记忆',Q,answer_format='text')
        self.assertEqual(label,explicit)
        self.assertEqual(label['schema']['properties']['q01']['enum'],['A','B','C','U'])
        self.assertEqual(text['schema']['properties']['q01']['enum'],['先做小样','先理结构','先访谈','U'])
        self.assertEqual(label['prompt'].split('\nREADER_INPUT_JSON:\n')[1],text['prompt'].split('\nREADER_INPUT_JSON:\n')[1])
        self.assertNotIn('到本题选项字母',text['prompt'])
        self.assertEqual(decode_response(Q,{'q01':'A','q02':'B'}),{'q01':'A','q02':'B'})

if __name__=='__main__':unittest.main()
