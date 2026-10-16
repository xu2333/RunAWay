import copy
import unittest
from runaway.text_integrity import require_intact
from runaway.profile import make_profile
from runaway.demo import demo_bundle
from runaway.portable import make_expression


class TextIntegrityTests(unittest.TestCase):
 def test_damage_rejected_and_valid_non_bmp_preserved(self):
  for text in ['修改建\ufffd\ufffd\ufffd','bad\ud800','bad\udfff']:
   with self.assertRaisesRegex(ValueError,'Text integrity'):require_intact(text)
  value='修改建议 🐸 𠮷';self.assertEqual(require_intact(value),value)
 def test_profile_and_export_fail_without_silent_fix(self):
  profile=demo_bundle()[0]['profile.private.json'];answer={'claims':copy.deepcopy(profile['claims']),'unknowns':profile['unknowns']}
  answer['claims'][0]['statement']+='\ufffd'
  before=copy.deepcopy(answer)
  with self.assertRaisesRegex(ValueError,'Text integrity'):make_profile(answer,profile['sources'],{})
  self.assertEqual(answer,before)
  with self.assertRaisesRegex(ValueError,'Text integrity'):make_expression('损坏\ufffd','profile','test')


if __name__=='__main__':unittest.main()
