from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
class FocusedTestError(ValueError): pass
@dataclass(frozen=True)
class SealedTest:
 command: tuple[str,...]; cwd: Path; timeout_seconds: float=20; max_output_bytes: int=65536
@dataclass(frozen=True)
class TestObservation:
 role:str; name:str; content:str; exit_code:int; evidence:dict
class FocusedTestTool:
 def __init__(self, registry:Mapping[str,SealedTest]): self.registry=dict(registry)
 def run(self, command_id:str, *, cancelled:bool=False)->TestObservation:
  if cancelled: return TestObservation('tool','focused_test','CANCELLED',-1,{'cancelled':True})
  spec=self.registry.get(command_id)
  if spec is None: raise FocusedTestError('unsealed_command_id')
  if not spec.cwd.is_dir() or any(not isinstance(v,str) for v in spec.command): raise FocusedTestError('sealed_command_invalid')
  try: result=subprocess.run(spec.command,cwd=spec.cwd,capture_output=True,text=True,timeout=spec.timeout_seconds,shell=False,check=False)
  except subprocess.TimeoutExpired as exc: return TestObservation('tool','focused_test','TIMEOUT',-1,{'timeout':True,'stdout':str(exc.stdout or '')[:spec.max_output_bytes]})
  out=(result.stdout or '')[:spec.max_output_bytes]; err=(result.stderr or '')[:spec.max_output_bytes]
  overflow=len(result.stdout or '')+len(result.stderr or '')>spec.max_output_bytes
  return TestObservation('tool','focused_test',out+'\n'+err,result.returncode,{'command_id':command_id,'stderr':err,'overflow':overflow,'cwd':str(spec.cwd)})
