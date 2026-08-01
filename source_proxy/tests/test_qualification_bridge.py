from __future__ import annotations
import copy
import unittest
from source_proxy.jcode.qualification_bridge import QualificationBridgeError, bridge_chat

def request():
    return {"route":"/api/chat","model":"fake-qwen","messages":[{"role":"system","content":"system"},{"role":"user","content":"read"},{"role":"tool","name":"read_file","tool_call_id":"c1","content":"text"}],"tools":[{"type":"function","function":{"name":"read_file","parameters":{"type":"object"}}}],"tool_choice":"auto","parameters":{"temperature":0}}

def fragments():
    return [{"model":"fake-qwen","choices":[{"delta":{"tool_calls":[{"index":0,"id":"c1","function":{"name":"read_file","arguments":"{}"}}]},"finish_reason":"tool_calls"}],"usage":{"prompt_tokens":9,"completion_tokens":4}}]

class BridgeTests(unittest.TestCase):
    def test_preserves_chat_contract(self):
        receipt=bridge_chat(request(),fragments())
        self.assertEqual(receipt.provider_request["messages"],request()["messages"])
        self.assertEqual(receipt.reconstructed_response["tool_calls"][0]["function"]["name"],"read_file")
    def test_controlled_failures(self):
        cases=[lambda r,f:r.__setitem__("messages",r["messages"][1:]),lambda r,f:r.__setitem__("messages",list(reversed(r["messages"]))),lambda r,f:r.__setitem__("tools",[]),lambda r,f:r["tools"][0]["function"].__setitem__("name","changed"),lambda r,f:r.pop("tool_choice"),lambda r,f:r.__setitem__("fallback",True),lambda r,f:f[0].__setitem__("choices",[]),lambda r,f:f[0]["choices"][0]["delta"]["tool_calls"][0]["function"].__setitem__("arguments","{"),lambda r,f:r["messages"][2].__setitem__("role","assistant"),lambda r,f:r["messages"][2].pop("name"),lambda r,f:f[0]["choices"][0].__setitem__("finish_reason",None),lambda r,f:f[0].pop("usage")]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                r,f=copy.deepcopy(request()),copy.deepcopy(fragments()); mutate(r,f)
                with self.assertRaises(QualificationBridgeError): bridge_chat(r,f)