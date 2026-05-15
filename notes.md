Your future feature list (post-Coder-Agent-fix):

Undo button for approvals — especially important while testing (so you can safely revert a bad apply).
Persistent memory instead of localStorage — move all the important state (approval history, legacy prompts, agent memory, etc.) to a real backend/DB so it’s consistent no matter what domain, device, or browser you use.
“Legacy Prompts” / SS+ buttons — after a good approval, one-click way to save exemplary prompts + actions so the AI always has strong signal examples to reference and keep the same high-quality flow.
Better visibility into Coder Agent internals — easy way to see what the Architect, Coder, and Debugger actually did in each run (full action history).
Multi-agent support on your Dell — yes, you can add more specialized agents (Designer Agent, etc.) that sit on standby and don’t all run at once.

Designer AgentSpecializes in UI/UX, glass aesthetics, theme system, component polish, responsive tweaksYou already want this. Perfect for the design-demo page and future dashboard/oracle work.MediumReviewer AgentDoes deep code review, catches style violations, security issues, performance problems, suggests improvementsHuge safety net. Especially useful when you start approving bigger changes.EasyArchitect AgentHigh-level planning, system design, decides file structure, tech choices, long-term architecturePrevents messy code. Great before big new features.MediumTester AgentAuto-generates + runs tests, suggests verification commands, checks edge casesMakes the verification step much stronger.Medium

Strong runners-up (add later)

Documenter Agent – writes/updates READMEs, comments, _blueprints/ files, keeps things maintainable
Refactor Agent – cleans up technical debt, renames things, improves consistency across the codebase
Researcher Agent – deep repo + web research before starting implementation (already partially exists in the decision layer)
Oracle Agent – specialized for voice/oracle surface, TTS/STT flows, real-time conversation patterns

How this fits your vision