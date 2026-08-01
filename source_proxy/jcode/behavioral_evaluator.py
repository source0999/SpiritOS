from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Evaluation:
 verdict:str; behavioral:bool; structural:bool|None; safety:bool; evidence_complete:bool; uncertainty:bool
 def as_dict(self): return self.__dict__
def evaluate(*,focused_exit:int,changed_paths:set[str],allowed_paths:set[str],interface_ok:bool,evidence_complete:bool,structural_required:bool=False,structural_ok:bool=True)->Evaluation:
 safety=changed_paths <= allowed_paths
 behavioral=focused_exit==0 and interface_ok
 structural=structural_ok if structural_required else None
 uncertainty=not evidence_complete
 verdict='PASS' if behavioral and safety and evidence_complete and (structural is not False) else ('UNCERTAIN' if uncertainty else 'FAIL')
 return Evaluation(verdict,behavioral,structural,safety,evidence_complete,uncertainty)
