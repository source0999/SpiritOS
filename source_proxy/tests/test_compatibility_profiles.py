import unittest
from source_proxy.jcode.compatibility_profiles import QWEN_7B,QWEN_14B,verify_profile
class Tests(unittest.TestCase):
 def test_exact_identities(self):
  self.assertTrue(verify_profile(QWEN_7B,{QWEN_7B.model:{"digest":QWEN_7B.digest,"details":{"quantization_level":"Q4_K_M"}}}))
  self.assertTrue(verify_profile(QWEN_14B,{QWEN_14B.model:{"digest":QWEN_14B.digest,"details":{"quantization_level":"Q4_K_M"}}}))
 def test_no_aliases_or_unbounded_turns(self):
  for p in (QWEN_7B,QWEN_14B): self.assertEqual(p.max_turns,3); self.assertEqual(p.parser_precedence,('native','strict_textual_json'))
if __name__=='__main__':unittest.main()
