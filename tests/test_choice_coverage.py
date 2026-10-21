import unittest
from runaway.choice_reader import COVERAGE_CHECK, make_request, decode_response

class CoverageReaderTests(unittest.TestCase):
    def test_coverage_changes_only_instructions(self):
        queries=[{'id':'q1','scenario':'换了题材，同一个限制','options':{'A':'先试','B':'先问'}}]
        for fmt in ['label','text']:
            basic=make_request('给定材料',queries,answer_format=fmt)
            explicit=make_request('给定材料',queries,answer_format=fmt,reader_mode='standard')
            coverage=make_request('给定材料',queries,answer_format=fmt,reader_mode='coverage')
            self.assertEqual(basic,explicit)
            self.assertEqual(coverage['schema'],basic['schema'])
            self.assertEqual(coverage['prompt'],COVERAGE_CHECK+'\n'+basic['prompt'])
        self.assertEqual(decode_response(queries,{'q1':'U'}),{'q1':'U'})
        with self.assertRaises(ValueError):make_request('',queries,reader_mode='guess')

if __name__=='__main__':unittest.main()
