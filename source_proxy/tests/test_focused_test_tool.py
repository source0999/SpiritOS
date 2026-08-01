import sys,tempfile,unittest
from pathlib import Path
from source_proxy.jcode.focused_test_tool import FocusedTestError,FocusedTestTool,SealedTest
from source_proxy.jcode.behavioral_evaluator import evaluate
class Tests(unittest.TestCase):
 def test_sealed_tool_and_observation(self):
  with tempfile.TemporaryDirectory() as d:
   tool=FocusedTestTool({'ok':SealedTest((sys.executable,'-c','print("ok")'),Path(d))}); r=tool.run('ok'); self.assertEqual((r.role,r.name,r.exit_code),('tool','focused_test',0)); self.assertIn('command_id',r.evidence)
 def test_tool_failures(self):
  with tempfile.TemporaryDirectory() as d:
   tool=FocusedTestTool({'fail':SealedTest((sys.executable,'-c','raise SystemExit(1)'),Path(d),max_output_bytes=2)})
   with self.assertRaises(FocusedTestError): tool.run('x')
   self.assertEqual(tool.run('fail').exit_code,1); self.assertEqual(tool.run('fail',cancelled=True).content,'CANCELLED')
 def test_behavior_not_ast_shape(self):
  good=evaluate(focused_exit=0,changed_paths={'fixture.py'},allowed_paths={'fixture.py'},interface_ok=True,evidence_complete=True); self.assertEqual(good.verdict,'PASS')
  self.assertEqual(evaluate(focused_exit=1,changed_paths={'fixture.py'},allowed_paths={'fixture.py'},interface_ok=True,evidence_complete=True).verdict,'FAIL')
  self.assertEqual(evaluate(focused_exit=0,changed_paths={'x.py'},allowed_paths={'fixture.py'},interface_ok=True,evidence_complete=True).verdict,'FAIL')
  self.assertEqual(evaluate(focused_exit=0,changed_paths={'fixture.py'},allowed_paths={'fixture.py'},interface_ok=True,evidence_complete=False).verdict,'UNCERTAIN')
if __name__=='__main__':unittest.main()
