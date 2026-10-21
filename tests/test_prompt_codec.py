import unittest
from runaway.prompt_codec import pack,unpack

class PromptCodecTests(unittest.TestCase):
    def test_roundtrip_and_complete_dictionary_in_budget(self):
        prefix='名字与固定使用边界\n';a='团队即将据此决策且误判代价明显';b='尚未验证的入口设计、三个方案均可行、无截止压力'
        text=prefix+a+'，先核查。'+b+'，先试。'+a+'，先许可。'+b+'，先理清。'+a+'，再核查。'
        packed,report=pack(text,len(text)-10,prefix=prefix)
        self.assertLessEqual(len(packed),len(text)-10);self.assertEqual(unpack(packed,report),text)
        self.assertTrue(packed.startswith(prefix));self.assertTrue(report['dictionary'])

    def test_existing_symbols_and_unicode_not_corrupted(self):
        text='原文已有①；条件可立即恢复且不外发，先试。条件可立即恢复且不外发，再试。条件可立即恢复且不外发，继续。'
        packed,report=pack(text,len(text)-2);self.assertEqual(unpack(packed,report),text)
        self.assertNotIn('①',[key for key,value in report['dictionary']])

    def test_incompressible_fails_no_cropping(self):
        text=''.join(chr(0x4e00+j) for j in range(600))
        with self.assertRaisesRegex(ValueError,'no truncation'):pack(text,300)
        self.assertEqual(pack('短文本',300)[0],'短文本')

if __name__=='__main__':unittest.main()
