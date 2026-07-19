"""Authenticated issuance and revocation surface for Campaign 3.5 model calls."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from source_proxy.approval.model_call_authority import (
    ModelCallAuthorityError,
    issue_campaign_3_5_model_call_authorization,
    revoke_campaign_3_5_model_call_authorization,
)
from source_proxy.approval.operator_session import (
    OperatorSessionError,
    verify_operator_approval_assertion,
)


router = APIRouter(prefix="/v1/campaigns/campaign-3.5")
_TASK_ID = "campaign-3.5:model-call-authority"
_ISSUE_PREVIEW_ID = "campaign-3.5:model-call-authority:issue"
_REVOKE_PREVIEW_ID = "campaign-3.5:model-call-authority:revoke"


def _require_assertion(assertion_value: str, *, action: str, preview_id: str) -> str:
    assertion = verify_operator_approval_assertion(assertion_value)
    if (
        assertion.get("operator") != "spiritos-local-operator"
        or assertion.get("role") != "approval-issuer"
        or assertion.get("action") != action
        or assertion.get("task_id") != _TASK_ID
        or assertion.get("preview_id") != preview_id
        or assertion.get("generation") != 1
    ):
        raise OperatorSessionError("operator_assertion_mismatch")
    return str(assertion["operator"])


@router.post("/model-call-authority")
async def issue_model_call_authority(
    x_spiritos_operator_assertion: str = Header(default=""),
) -> dict[str, object]:
    try:
        operator = _require_assertion(
            x_spiritos_operator_assertion,
            action="approve",
            preview_id=_ISSUE_PREVIEW_ID,
        )
        return issue_campaign_3_5_model_call_authorization(operator=operator)
    except OperatorSessionError as error:
        raise HTTPException(status_code=403, detail={"reason_code": str(error)}) from error
    except ModelCallAuthorityError as error:
        raise HTTPException(status_code=422, detail={"reason_code": error.reason_code}) from error


@router.delete("/model-call-authority")
async def revoke_model_call_authority(
    x_spiritos_operator_assertion: str = Header(default=""),
) -> dict[str, object]:
    try:
        operator = _require_assertion(
            x_spiritos_operator_assertion,
            action="reject",
            preview_id=_REVOKE_PREVIEW_ID,
        )
        return revoke_campaign_3_5_model_call_authorization(operator=operator)
    except OperatorSessionError as error:
        raise HTTPException(status_code=403, detail={"reason_code": str(error)}) from error
    except ModelCallAuthorityError as error:
        raise HTTPException(status_code=422, detail={"reason_code": error.reason_code}) from error
