from __future__ import annotations

import asyncio

from fastapi import BackgroundTasks, Response

import source_proxy.api.chat as chat


class _Spend:
    def as_payload(self) -> dict[str, object]:
        return {"approval_required": False}


class _Router:
    async def acompletion(self, *, model: str, **_kwargs: object) -> dict[str, object]:
        if model == "primary":
            raise TimeoutError()
        return {"id": "fallback-completion", "model": model}


def test_chat_fallback_returns_secondary_receipt_not_primary_success(monkeypatch) -> None:
    monkeypatch.setattr(chat, "central_gate_check", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(chat, "available_model_aliases", lambda: {"primary", "secondary"})
    monkeypatch.setattr(chat, "route_model_for_alias", lambda alias: f"model/{alias}")
    monkeypatch.setattr(chat, "route_provider_for_alias", lambda alias: f"provider-{alias}")
    async def spend(**_kwargs): return _Spend()
    monkeypatch.setattr(chat, "async_pre_call_hook", spend)
    monkeypatch.setattr(chat, "get_router", lambda: _Router())
    monkeypatch.setattr(chat, "build_expenditure_record", lambda **kwargs: kwargs)

    payload = asyncio.run(chat.chat_completions(
        chat.ChatCompletionRequest(model="primary", fallback_model="secondary", messages=[{"role": "user", "content": "hi"}]),
        Response(), BackgroundTasks(),
    ))

    receipt = payload["source_proxy"]["route_fallback"]
    assert receipt["fallback_used"] is True
    assert receipt["primary_success"] is False
    assert receipt["selected_provider"] == "secondary"
