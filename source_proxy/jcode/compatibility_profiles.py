from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class QwenProfile:
 model:str; digest:str; quantization:str; temperature:int=0; output_budget:int=1024; context_budget:int=8192; max_turns:int=3; max_tool_calls:int=3; timeout_seconds:int=180; preferred_dialect:str='strict_textual_json'; parser_precedence:tuple[str,...]=('native','strict_textual_json'); recovery_roles:tuple[str,...]=('system','user'); tool_result_role:str='tool'; qualified_task_classes:tuple[str,...]=('read','write'); disqualified_task_classes:tuple[str,...]=()
QWEN_7B=QwenProfile('qwen2.5-coder:7b','dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364','Q4_K_M')
QWEN_14B=QwenProfile('qwen2.5-coder:14b','9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849','Q4_K_M',timeout_seconds=180)
def verify_profile(profile:QwenProfile, registry:dict)->bool:
 item=registry.get(profile.model,{})
 return item.get('digest')==profile.digest and item.get('details',{}).get('quantization_level')==profile.quantization
