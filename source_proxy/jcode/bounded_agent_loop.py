from __future__ import annotations
from dataclasses import dataclass
from typing import Any,Callable
@dataclass(frozen=True)
class LoopResult: status:str; messages:list[dict[str,Any]]; evidence:list[dict[str,Any]]
def run_bounded_agent_loop(model:Callable[[list[dict[str,Any]]],dict[str,Any]], tool:Callable[[dict[str,Any]],Any], messages:list[dict[str,Any]], *,available_files:list[str],available_tools:list[str],max_turns:int=3,max_tools:int=3,cancelled:bool=False)->LoopResult:
 history=[dict(x) for x in messages]; evidence=[]; recovery=False; tools=0
 if cancelled:return LoopResult("CANCELLED",history,evidence)
 for turn in range(max_turns):
  reply=model(history); evidence.append({"turn":turn+1,"model_reply":reply})
  if reply.get("final"):
   return LoopResult("COMPLETED",history+[dict(reply)],evidence)
  if reply.get("request_available_files"):
   if recovery:return LoopResult("STOPPED_REFUSAL",history,evidence)
   recovery=True; history.append({"role":"system","content":"Use available tools: "+", ".join(available_tools)+". Available files: "+", ".join(available_files)}); continue
  call=reply.get("tool_call")
  if not call:return LoopResult("STOPPED_EVIDENCE_INCOMPLETE",history,evidence)
  if tools>=max_tools:return LoopResult("STOPPED_BUDGET",history,evidence)
  tools+=1; history.append({"role":"assistant","tool_calls":[call]})
  try: observation=tool(call); content=str(observation)
  except Exception as exc: content="ERROR: "+str(exc)
  message={"role":"tool","name":call["tool"],"tool_call_id":call.get("call_id",""),"content":content}; history.append(message); evidence.append({"tool":call,"observation":message})
 return LoopResult("STOPPED_BUDGET",history,evidence)
