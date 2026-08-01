from __future__ import annotations
import hashlib,json
from collections.abc import Mapping
from typing import Any
ALLOWED={"read_file","write_file","apply_patch","focused_test","list","find"}
class ToolNormalizationError(ValueError): pass
def normalize_tool_request(*,native:Mapping[str,Any]|None=None,text:str|None=None,allowed_paths=())->dict[str,Any]:
    raw=""; parser=""
    if native is not None:
        parser="native"; raw=json.dumps(native,sort_keys=True); name=native.get("function",{}).get("name"); args=native.get("function",{}).get("arguments"); call_id=native.get("id")
        if not call_id or not isinstance(args,(str,dict)): raise ToolNormalizationError("malformed_native_fragment")
        try: args=json.loads(args) if isinstance(args,str) else dict(args)
        except ValueError: raise ToolNormalizationError("malformed_native_arguments")
    elif isinstance(text,str):
        parser="strict_textual_json"; raw=text
        if text.strip()!=text or "```" in text: raise ToolNormalizationError("ambiguous_textual_tool_call")
        try: value=json.loads(text)
        except ValueError: raise ToolNormalizationError("malformed_textual_json")
        if not isinstance(value,dict) or set(value)-{"tool","name","arguments"} or ("tool" in value and "name" in value): raise ToolNormalizationError("ambiguous_textual_tool_call")
        name=value.get("tool",value.get("name")); args=value.get("arguments"); call_id="text-"+hashlib.sha256(text.encode()).hexdigest()[:12]
    else: raise ToolNormalizationError("no_tool_request")
    if name not in ALLOWED: raise ToolNormalizationError("unknown_tool")
    if not isinstance(args,dict): raise ToolNormalizationError("invalid_arguments")
    path=args.get("path")
    if name in {"read_file","write_file","apply_patch"} and (not isinstance(path,str) or not path): raise ToolNormalizationError("missing_or_invalid_path")
    if path is not None and path not in set(allowed_paths): raise ToolNormalizationError("unauthorized_path")
    if any(key in args for key in ("command","shell","code")): raise ToolNormalizationError("executable_argument_denied")
    normalized={"tool":name,"arguments":args,"call_id":call_id}
    return {"raw_model_output_sha256":hashlib.sha256(raw.encode()).hexdigest(),"parser_selected":parser,"normalized_tool_request":normalized,"schema_validation":"PASS","authorization":"PASS","rejection_reason":None}
