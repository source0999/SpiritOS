System Directive: "Source" Proxy Development – Master Sequential Execution Plan
Role & Context: You are the primary orchestration agent tasked with constructing "Source", the sovereign proxy gateway for the Spirit OS environment. You are operating under strict hardware constraints: an AM5 platform with 16GB (2x8GB) of system RAM and a single NVIDIA RTX 3060 with 12GB of VRAM.

Execution Protocol:
You must operate strictly as a state machine. You are explicitly forbidden from hallucinating future steps or combining tasks. You will execute the following micro-increments sequentially. After completing the "Execution" step of any micro-increment, you must HALT and present the "Verification Block" to the human operator. You may not proceed to the next increment until the human operator confirms the physical presence of the "Success Artifact."

Verified Source Direction Update:
Spirit chat can now answer a concrete Windows folder-listing request for an allowlisted path. The verified user prompt was "whats in my c/projects folder?", and Spirit returned a directory listing from C:\Projects through the Windows desktop agent. The previous blocker was "The Windows agent rejected the bearer token." The fix was starting the Windows Node agent with matching token environment variables and enabling filesystem sharing with SPIRIT_DESKTOP_FS_ENABLED=true and SPIRIT_DESKTOP_FS_ALLOWLIST=C:\Projects.

Planning Boundary:
This does not authorize write/edit/delete, arbitrary full-drive browsing, SSH execution, AppArmor work, or Phase 3 sandboxing. The next Source direction is to turn verified read-only listings and compressed repo context into safe context candidates for human-in-the-loop prompt packets before moving to heavier infrastructure.

Phase 0: Environment Bootstrap & Health Diagnostics
Increment 0.1: Core Dependencies & Architecture Initialization

Objective: Establish the foundational OS dependencies and project structure.

Execution: Scaffold the primary Node.js and Python environments (ensuring compatibility with Next.js 16.2.4 and PyTorch with CUDA support). Establish the core directory structure for the proxy.

Verification Block:

Manual Verification Checks: Run the initial install script and verify the directory tree.

Expected Outcomes: The environment initializes without dependency conflicts across Node and Python.

Success Artifact: A successfully generated package.json and requirements.txt (or equivalent) in the root directory, with a clean terminal exit 0 upon installation.

Recommended Fixes: Check Node version managers or Python virtual environment isolation if conflicts arise.

Next Steps: Proceed to Increment 0.2.

Increment 0.2: Hardware Diagnostics Endpoint

Objective: Build a real-time monitor to track the 12GB VRAM ceiling.

Execution: Construct a /healthcheck API endpoint that queries nvidia-smi (or utilizes a direct Python NVML binding) to pull real-time RTX 3060 VRAM utilization.

Verification Block:

Manual Verification Checks: Ping the /healthcheck endpoint via curl or browser.

Expected Outcomes: The endpoint successfully queries local GPU resources without crashing or hanging.

Success Artifact: A 200 OK JSON response in the terminal displaying exact metrics: {"vram_used": "X GB", "vram_total": "12 GB"}.

Recommended Fixes: If VRAM reads fail, verify the NVIDIA driver installation and ensure the orchestrator user has the correct execution permissions.

Next Steps: Proceed to Increment 0.3.

Increment 0.3: LiteLLM Budget Integration

Objective: Integrate financial metrics into the health diagnostics.

Execution: Connect the /healthcheck endpoint to the LiteLLM BudgetManager class to fetch the current cloud API budget status.

Verification Block:

Manual Verification Checks: Ping the /healthcheck endpoint again.

Expected Outcomes: The API aggregates both hardware limitations and cloud financial constraints.

Success Artifact: An updated 200 OK JSON response: {"vram_used": "X GB", "budget_remaining": "$Y"}.

Recommended Fixes: Verify LiteLLM virtual key configurations if the budget returns null.

Next Steps: Proceed to Phase 1.

Phase 1: Core Gateway & Token Governance Initialization
Increment 1.1: Unified Routing Layer

Objective: Configure LiteLLM to unify multiple provider APIs.

Execution: Establish the base LiteLLM router to translate requests for OpenAI, Anthropic, and local Ollama. Ensure Ollama is configured with the OLLAMA_KEEP_ALIVE=-1 environment variable via API payload to eliminate the 8-15 second load latency when swapping local specialists.

Verification Block:

Manual Verification Checks: Send a test payload to the local proxy endpoint requesting generation from a local model, then immediately send a second request.

Expected Outcomes: The first request loads the model; the second request processes instantly without unloading the model from VRAM.

Success Artifact: A logged API response time for the second request that is under 2 seconds.

Recommended Fixes: If latency remains high, manually verify the OLLAMA_KEEP_ALIVE variable is passing through the LiteLLM header correctly.

Next Steps: Proceed to Increment 1.2.

Increment 1.2: Asynchronous Expenditure Logging

Objective: Establish the database backend for cost tracking.

Execution: Spin up the PostgreSQL backend and connect it to LiteLLM to log all routing and expenditure data asynchronously.

Verification Block:

Manual Verification Checks: Send a test cloud inference request through the proxy, then query the PostgreSQL database.

Expected Outcomes: The database successfully records the transaction without blocking the inference stream.

Success Artifact: A valid row in the PostgreSQL expenditure table containing user_id, project_id, and the calculated token cost.

Recommended Fixes: Verify the database connection string and async worker threads if the row does not appear.

Next Steps: Proceed to Increment 1.3.

Increment 1.3: The Approval Gate

Objective: Enforce explicit pre-flight cost governance.

Execution: Implement the async_pre_call_hook in LiteLLM to intercept requests, calculate exact token costs via provider-specific counting endpoints, and pause execution if the projected cost is greater than $0.00.

Verification Block:

Manual Verification Checks: Send a large context payload targeting a paid cloud route (e.g., Claude 3.5 Sonnet).

Expected Outcomes: Execution strictly pauses before the network request is initiated.

Success Artifact: A terminal or UI prompt specifically demanding a physical y/n confirmation alongside a "spend-before-you-send" breakdown.

Recommended Fixes: Check the model_prices_and_context_window.json catalog mapping if the cost calculation fails.

Next Steps: Proceed to Phase 2.

Phase 2: Context Bundling & MCP Bridge
Increment 2.1: Repomix Aggregation Configuration

Objective: Optimize local code bundling.

Execution: Configure Repomix to recursively scan the directory structure, strictly enforcing .gitignore and .repomixignore rules.

Verification Block:

Manual Verification Checks: Run the Repomix build command on the current repository.

Expected Outcomes: The tool outputs a single aggregated file excluding all node_modules and ignored directories.

Success Artifact: A generated repomix-output.xml (or .txt) file containing the source code.

Recommended Fixes: Adjust the .repomixignore file if restricted paths are captured.

Next Steps: Proceed to Increment 2.2.

Increment 2.2: Tree-sitter AST Pruning & XML Structuring

Objective: Compress the repository context to fit within the 12GB VRAM constraints.

Execution: Integrate Tree-sitter to analyze the Abstract Syntax Tree (AST), extract structural signatures, and prune boilerplate/comments. Wrap the highly compressed output in strict <system_directive> and <repository_context> XML tags.

Verification Block:

Manual Verification Checks: Run the AST compression script on a complex component.

Expected Outcomes: The output retains interfaces and function definitions but drops internal implementation details and comments.

Success Artifact: A valid XML payload where the target file's size is reduced by at least 40% compared to raw text.

Recommended Fixes: Check the Tree-sitter language grammar definitions if parsing fails.

Next Steps: Proceed to Increment 2.3.

Increment 2.3: Next.js MCP Integration via WebSockets

Objective: Establish bidirectional diagnostic communication.

Execution: Initialize the next-devtools-mcp package using the Vercel @modelcontextprotocol/sdk to establish a persistent WebSocket connection (bypassing SSE limitations). Expose tools like get_errors and get_page_metadata.

Verification Block:

Manual Verification Checks: Intentionally create a TypeScript error in the Next.js app, then invoke the local agent to pull the get_errors tool.

Expected Outcomes: The agent retrieves the exact compilation error natively without manual terminal copying.

Success Artifact: A complete JSON-RPC response payload in the WebSocket stream containing the exact text of the forced type error.

Recommended Fixes: Audit the Next.js API route configuration if the WebSocket connection drops or defaults to polling.

Next Steps: Proceed to Increment 2.4.

Increment 2.4: Human-in-the-Loop Decision Router

Objective: Decide whether a task should use paid API execution or a manual browser/subscription workflow before any cloud spend occurs.

Execution: Build a Source decision router that classifies incoming tasks by context size, cost sensitivity, urgency, privacy risk, implementation risk, and whether a human subscription/browser model is likely better than API execution. The router must return an explicit recommendation: api_route, manual_route, local_route, or ask_user. It must preserve the existing paid-route approval gate and never auto-spend.

Verification Block:

Manual Verification Checks: Submit representative tasks for code review, large-context planning, quick local generation, and sensitive/private content.

Expected Outcomes: Source produces a structured routing decision with reason codes, estimated context size, risk tier, and a recommended route.

Success Artifact: A JSON response showing task_classification, recommended_route, reason_codes, risk_tier, context_estimate, and next_prompt_action.

Recommended Fixes: Adjust classification thresholds if the router overuses API routes or fails to escalate sensitive/manual workflows.

Next Steps: Proceed to Increment 2.5.

Increment 2.5: Prompt Packet Generator

Objective: Generate polished manual prompt packets for ChatGPT, Gemini, Google AI Studio, Grok, Claude, and other browser-based model workflows.

Execution: Implement a prompt packet generator that packages the user's task, compressed repository context, constraints, acceptance criteria, and return format into a copy-ready prompt. The packet must be usable without leaking secrets and should include explicit instructions for the external model to avoid unsupported claims.

Verification Block:

Manual Verification Checks: Ask Source for a manual-route packet for a complex coding task and inspect the generated packet.

Expected Outcomes: The packet is coherent, paste-ready, scoped to the task, and includes enough context for a browser model to help without needing repository access.

Success Artifact: A generated prompt packet containing target_model_hint, task_summary, relevant_context, constraints, requested_output, and paste_back_instructions.

Recommended Fixes: Tighten context trimming if the packet is too long; add missing acceptance criteria if the packet is too vague.

Next Steps: Proceed to Increment 2.6.

Increment 2.6: Manual Model Recommendation Layer

Objective: Recommend the best manual browser/subscription model for the task before asking the user to paste anything externally.

Execution: Implement a recommendation layer that maps task type and context shape to model suggestions such as ChatGPT, Claude, Gemini / Google AI Studio, Grok, or local Ollama. The layer should explain the tradeoff in one short rationale and should prefer manual browser routes when they avoid API spend.

Verification Block:

Manual Verification Checks: Submit tasks requiring coding, long-context review, web/current research, design critique, and quick local drafting.

Expected Outcomes: Source recommends a suitable manual model route with a concise reason and fallback option.

Success Artifact: A structured recommendation containing primary_model, fallback_model, route_type, rationale, and expected_user_action.

Recommended Fixes: Rebalance recommendations if they are too generic or ignore context size / modality.

Next Steps: Proceed to Increment 2.7A.

Increment 2.7A: Workspace Self-Inspection & Capability Manifest

Objective: Make Source truthfully aware of its current project/workspace files, enabled tools, disabled tools, safe filesystem roots, Windows bridge status, and approval boundaries before it recommends API, manual browser, local, or implementation routes.

Execution: Build a read-only self-inspection layer that combines:

configured local project roots
Windows bridge filesystem state
Source proxy decision endpoints
tool/capability registry state
safe allowlist boundaries
generated context bundles
current repo metadata
approval requirements

The layer must never imply full-machine access. It must report only configured roots like C:\Projects or SPIRIT_PROJECT_PATH, and it must explicitly distinguish:

available read-only tools
unavailable tools
gated edit tools
gated terminal tools
paid API routes
manual browser routes
local routes

Recommended endpoint names for later implementation:

GET /v1/self/status
GET /v1/tools/manifest
GET /v1/context/index
POST /v1/actions/preview

Do not implement these endpoints in this documentation pass. Only add the plan.

Verification Block:

Manual Verification Checks: Ask Source for its current workspace/capability status before choosing an API, manual browser, local, or implementation route.

Expected Outcomes: Source reports only configured roots and known capabilities, clearly labels unavailable or gated capabilities, and refuses to imply full-machine access.

Success Artifact: A capability manifest/status response design containing configured_roots, windows_bridge_status, enabled_tools, disabled_tools, approval_boundaries, available_routes, and context_bundle_status.

Recommended Fixes: If the manifest implies broad filesystem access, hides unavailable tools, or blurs paid/manual/local routes, tighten the status schema and wording before implementation.

Next Steps: Proceed to Increment 2.7B.

Increment 2.7B: API-vs-Manual Cost/Context Preview

Objective: Show the user a clear cost/context preview before choosing paid API execution or manual browser execution.

Execution: Combine the approval gate, compressed context estimator, prompt packet generator, and manual model recommendation into one preview response. The preview must show projected API cost when available, context size, privacy/risk flags, manual route recommendation, and a direct question asking whether to use API or manual browser workflow.

Verification Block:

Manual Verification Checks: Submit a large task that could be handled either by a paid API route or by a manual subscription model.

Expected Outcomes: Source pauses and presents an API-vs-manual decision screen instead of immediately executing.

Success Artifact: A response containing projected_api_cost, context_tokens, manual_model_recommendation, api_model_option, privacy_flags, and a required human decision.

Recommended Fixes: If the preview skips the manual path, audit the decision router; if cost is missing for a paid route, fail closed and recommend manual route.

Next Steps: Proceed to Increment 2.8.

Increment 2.8: Safe Context Source Inventory

Objective: Turn verified read-only folder listings into a Source context inventory without reading or sending file contents yet.

Execution: Plan a read-only inventory layer that can record candidate context roots from SPIRIT_PROJECT_PATH, Repomix outputs, and allowlisted Windows folders such as C:\Projects. The inventory must preserve boundaries: no arbitrary drive browsing, no hidden files, no secrets, no recursive expansion by default, and no writes.

Verification Block:

Manual Verification Checks: Ask Source to list candidate context roots after the Windows bridge has returned C:\Projects.

Expected Outcomes: Source distinguishes verified roots, unavailable roots, and blocked paths; it describes what can be safely listed but does not read file contents yet.

Success Artifact: A structured inventory containing verified_context_roots, blocked_paths_policy, available_read_only_sources, and next_context_selection_action.

Recommended Fixes: If the inventory implies arbitrary filesystem access, tighten wording and allowlist checks before implementing.

Next Steps: Proceed to Increment 2.9.

Increment 2.9: Prompt Packet Context Selection Plan

Objective: Make prompt packets actually useful by selecting safe excerpts or compressed context references from verified sources.

Execution: Design the context-selection layer that feeds Increment 2.5. It should choose between compressed Repomix XML, selected source files, and allowlisted Windows project listings. It must redact secret-shaped names, avoid .env/certs/keys, cap size, and clearly label whether actual file contents were included or only path listings were included.

Verification Block:

Manual Verification Checks: Request a prompt packet for a repo review and for a Windows project-folder review.

Expected Outcomes: Source states whether it included real excerpts, compressed XML references, or only folder listings, and it refuses to include blocked files.

Success Artifact: A prompt packet metadata block containing context_inclusion_mode, included_paths, omitted_paths, redaction_notes, and estimated_context_tokens.

Recommended Fixes: If prompt packets imply they reviewed code when only paths were included, fix the packet language before continuing.

Next Steps: Proceed to Phase 3.

Phase 3: Multimodal Infrastructure & Advanced Security Sandboxing
Increment 3.1: VRAM-Safe Local Visual Vectorization

Objective: Deploy local semantic visual search via LanceDB.

Execution: Write the ingestion script to process the ~/Design/Refs directory using CLIP. Crucially, strictly enforce torch.no_grad() and limit image tensor batching to <= 16 images to prevent OOM exceptions on the 12GB VRAM. Store embeddings in LanceDB for zero-shot classification.

Verification Block:

Manual Verification Checks: Place 20 design images in the target directory and run the indexing script. Query LanceDB with a natural language string.

Expected Outcomes: The script processes the images in batches without crashing the GPU, and the text query returns the correct mathematical closest match.

Success Artifact: The /healthcheck endpoint shows VRAM remained below 11.5GB during ingestion, and LanceDB returns a matched image file path.

Recommended Fixes: If CUDA OOM occurs, immediately drop the batch size to 8.

Next Steps: Proceed to Increment 3.2.

Increment 3.2: Bubblewrap Unprivileged Sandboxing

Objective: Construct the ephemeral, isolated execution environment.

Execution: Implement the Bubblewrap script to spawn unprivileged sandboxes. The script must manipulate user namespaces, make the host /home directory invisible, drop all Linux capabilities (except those required for compilation), and enforce SECCOMP profiles.

Verification Block:

Manual Verification Checks: Command the agent (or manually trigger the script) to execute ls /home inside the sandbox.

Expected Outcomes: The sandbox process returns an empty or permission-denied response.

Success Artifact: A terminal output of ls: cannot open directory '/home': No such file or directory originating from the isolated Bubblewrap process.

Recommended Fixes: Ensure Bubblewrap is correctly installed on the host Ubuntu machine and the user namespace mappings are valid.

Next Steps: Proceed to Increment 3.3.

Increment 3.3: AppArmor Layering & Network Egress Denials

Objective: Enforce final defense-in-depth protocol.

Execution: Layer a strict AppArmor profile over the Bubblewrap processes to enforce read/write bounds. Implement network egress restrictions within the sandbox that deny default access, allowing only trusted domains such as registry.npmjs.org.

Verification Block:

Manual Verification Checks: From inside the sandbox, attempt to run curl https://google.com and then run npm ping.

Expected Outcomes: The unauthorized curl request is physically dropped, while the npm registry connection succeeds.

Success Artifact: A connection timeout or curl: (6) Could not resolve host error for the unauthorized domain, alongside a successful npm notice PING response.

Recommended Fixes: If legitimate compilation steps are blocked, audit the dmesg output to identify and explicitly allow the required system calls in the AppArmor profile.

Next Steps: Execute comprehensive end-to-end testing of the fully established Source Proxy.
