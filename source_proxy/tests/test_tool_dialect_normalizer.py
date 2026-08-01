import unittest
from source_proxy.jcode.tool_dialect_normalizer import ToolNormalizationError,normalize_tool_request
class Tests(unittest.TestCase):
 def test_native_precedes_text(self):
  r=normalize_tool_request(native={"id":"n1","function":{"name":"read_file","arguments":"{\"path\":\"a.py\"}"}},text='bad',allowed_paths=["a.py"]); self.assertEqual(r["parser_selected"],"native")
 def test_text_forms(self):
  for text in ('{"tool":"read_file","arguments":{"path":"a.py"}}','{"name":"read_file","arguments":{"path":"a.py"}}'): self.assertEqual(normalize_tool_request(text=text,allowed_paths=["a.py"])["normalized_tool_request"]["tool"],"read_file")
 def test_rejections(self):
  for text in ('bad',' {"tool":"read_file","arguments":{"path":"a.py"}}','```json\n{}\n```','{"tool":"unknown","arguments":{}}','{"tool":"read_file","arguments":[]}','{"tool":"read_file","arguments":{}}','{"tool":"read_file","arguments":{"path":"x"}}','{"tool":"read_file","arguments":{"path":"a.py","command":"rm"}}','{"tool":"read_file","name":"read_file","arguments":{"path":"a.py"}}'):
   with self.assertRaises(ToolNormalizationError): normalize_tool_request(text=text,allowed_paths=["a.py"])
if __name__=='__main__': unittest.main()
