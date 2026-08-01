import unittest
from source_proxy.jcode.bounded_agent_loop import run_bounded_agent_loop
class Tests(unittest.TestCase):
 def test_read_reinjected_then_final(self):
  replies=iter([{"tool_call":{"tool":"read_file","call_id":"c1","arguments":{"path":"a.py"}}},{"final":"done"}])
  r=run_bounded_agent_loop(lambda h:next(replies),lambda c:"text",[{"role":"user","content":"task"}],available_files=["a.py"],available_tools=["read_file"])
  self.assertEqual(r.status,"COMPLETED"); self.assertEqual(r.messages[-2]["role"],"tool")
 def test_recovery_and_boundaries(self):
  r=run_bounded_agent_loop(lambda h:{"request_available_files":True},lambda c:"",[{"role":"user","content":"task"}],available_files=["a.py"],available_tools=["read_file"]); self.assertEqual(r.status,"STOPPED_REFUSAL")
  self.assertEqual(run_bounded_agent_loop(lambda h:{},lambda c:"",[],available_files=[],available_tools=[]).status,"STOPPED_EVIDENCE_INCOMPLETE")
  self.assertEqual(run_bounded_agent_loop(lambda h:{"final":"x"},lambda c:"",[],available_files=[],available_tools=[],cancelled=True).status,"CANCELLED")
if __name__=='__main__':unittest.main()
