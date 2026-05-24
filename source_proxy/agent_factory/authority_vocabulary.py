"""Blocked authority vocabulary for deterministic Agent Factory audits."""

from __future__ import annotations

import re
from dataclasses import dataclass

from source_proxy.agent_factory.contracts import FindingSeverity


@dataclass(frozen=True)
class AuthorityVocabularyRule:
    """A phrase rule that reports authority drift without granting authority."""

    rule: str
    pattern: re.Pattern[str]
    severity: FindingSeverity
    detail: str


AUTHORITY_VOCABULARY: tuple[AuthorityVocabularyRule, ...] = (
    AuthorityVocabularyRule(
        rule="authority_grant",
        pattern=re.compile(
            r"\bgrant(?:s|ed|ing)?\s+"
            r"(?:approval|apply|write|command|workflow|queue|commit|push|"
            r"branch|worktree|self-approval|background autonomy)\b",
            re.IGNORECASE,
        ),
        severity="blocked",
        detail="Text appears to grant a blocked authority.",
    ),
    AuthorityVocabularyRule(
        rule="authority_authorized_action",
        pattern=re.compile(
            r"\b(?:authorized|allowed|permitted)\s+to\s+"
            r"(?:approve|apply|write|run commands|execute commands|"
            r"execute workflows|run workflows|consume queues?|commit|push|"
            r"create branches|create worktrees|self-approve)\b",
            re.IGNORECASE,
        ),
        severity="blocked",
        detail="Text appears to authorize a blocked action.",
    ),
    AuthorityVocabularyRule(
        rule="clean_report_permission",
        pattern=re.compile(
            r"\b(?:clean report|passing checks?|audit success)\s+"
            r"(?:authorizes|grants|permits|allows|is permission)\b",
            re.IGNORECASE,
        ),
        severity="blocked",
        detail="Text appears to treat a clean report as permission.",
    ),
    AuthorityVocabularyRule(
        rule="background_autonomy_request",
        pattern=re.compile(
            r"\b(?:run in the background|continue autonomously|background autonomy)\b",
            re.IGNORECASE,
        ),
        severity="blocked",
        detail="Text appears to request blocked background autonomy.",
    ),
)
