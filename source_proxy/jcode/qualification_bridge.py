"""Qualification-only chat bridge; it never selects production transport."""
from __future__ import annotations
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
class QualificationBridgeError(ValueError): pass
@dataclass(frozen=True)
class BridgeReceipt:
    provider_request: dict[str, Any]
    reconstructed_response: dict[str, Any]
    preserved: tuple[str, ...]
def build_provider_request(request: Mapping[str, Any]) -> dict[str, Any]:
    for name in ("model","messages","tools","tool_choice"):
        if name not in request: raise QualificationBridgeError("missing_required_field")
    if request.get("route") not in (None,"/api/chat"): raise QualificationBridgeError("qualification_route_denied")
    if request.get("fallback"): raise QualificationBridgeError("fallback_denied")
    messages=request["messages"]
    if not isinstance(messages,list) or not messages or messages[0].get("role")!="system": raise QualificationBridgeError("system_role_or_order_invalid")
    for message in messages:
        if not isinstance(message,Mapping) or message.get("role") not in {"system","user","assistant","tool"}: raise QualificationBridgeError("message_role_invalid")
        if message.get("role")!="tool" and "tool_call_id" in message: raise QualificationBridgeError("tool_result_role_invalid")
        if message.get("role")=="tool" and (not message.get("name") or "tool_call_id" not in message): raise QualificationBridgeError("tool_result_identity_invalid")
    tools=request["tools"]
    if not isinstance(tools,list) or not all(isinstance(t,Mapping) and t.get("function",{}).get("name") for t in tools): raise QualificationBridgeError("tool_schema_invalid")
    names={t["function"]["name"] for t in tools}
    if any(m.get("role")=="tool" and m.get("name") not in names for m in messages): raise QualificationBridgeError("tool_result_name_invalid")
    return {"route":"/api/chat","model":request["model"],"messages":[dict(m) for m in messages],"tools":[dict(t) for t in tools],"tool_choice":request["tool_choice"],"options":dict(request.get("parameters") or {}),"stream":True}
def reconstruct_stream(fragments: Sequence[Mapping[str,Any]], *, expected_model:str)->dict[str,Any]:
    calls={}; finish=None; usage=None; content=""
    for f in fragments:
        if not isinstance(f,Mapping) or f.get("model")!=expected_model: raise QualificationBridgeError("stream_model_invalid")
        choices=f.get("choices")
        if not isinstance(choices,list) or len(choices)!=1: raise QualificationBridgeError("stream_fragment_invalid")
        c=choices[0]; d=c.get("delta")
        if not isinstance(d,Mapping): raise QualificationBridgeError("stream_delta_invalid")
        content+=str(d.get("content") or "")
        for item in d.get("tool_calls") or []:
            if not isinstance(item,Mapping) or not isinstance(item.get("index"),int): raise QualificationBridgeError("tool_fragment_invalid")
            x=calls.setdefault(item["index"],{"id":"","type":"function","function":{"name":"","arguments":""}}); fn=item.get("function") or {}
            x["id"]=item.get("id") or x["id"]; x["function"]["name"]+=str(fn.get("name") or ""); x["function"]["arguments"]+=str(fn.get("arguments") or "")
        if c.get("finish_reason") is not None: finish=c["finish_reason"]
        if f.get("usage") is not None: usage=f["usage"]
    if finish is None: raise QualificationBridgeError("finish_reason_missing")
    ordered=[calls[i] for i in sorted(calls)]
    try:
        for x in ordered:
            if not x["id"] or not x["function"]["name"]: raise ValueError
            json.loads(x["function"]["arguments"])
    except (ValueError,TypeError): raise QualificationBridgeError("tool_call_incomplete")
    if usage is None: raise QualificationBridgeError("usage_missing")
    return {"role":"assistant","content":content or None,"tool_calls":ordered,"finish_reason":finish,"usage":usage}
def bridge_chat(request: Mapping[str,Any], fragments: Sequence[Mapping[str,Any]])->BridgeReceipt:
    provider=build_provider_request(request); response=reconstruct_stream(fragments,expected_model=str(request["model"]))
    return BridgeReceipt(provider,response,("roles","message_order","tools","tool_choice","model","parameters","tool_result_role_and_name","streamed_tool_fragments","finish_reason","usage"))
