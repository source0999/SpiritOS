# Campaign 0 Reproducibility Addendum

Date: 2026-07-26

Scope: Source Proxy Campaign 0 reproducibility only. No production behavior changed.

## Registered Backend Command

Exact command:

```bash
npm run test:coding-regression
```

Registered script from `package.json`:

```bash
.venv-campaign1/bin/python -m pytest -q source_proxy/tests/test_coding_regression_pack.py
```

Selected test node:

```text
source_proxy/tests/test_coding_regression_pack.py
```

## Worktree-Local Python Binding

The registered command requires `.venv-campaign1` in the Campaign 0 checkout.
That binding is worktree-local and intentionally ignored.

Required existing environment:

```text
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy
```

Established binding:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
ln -s /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy .venv-campaign1
```

Ignore authority:

```text
/home/source/.campaign-3-5-execution-repository-20260719.git/info/exclude:8:.venv-campaign1
```

Interpreter used:

```text
/usr/bin/python3.12
```

Command runner path:

```text
/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725/.venv-campaign1/bin/python
```

Resolved Source Proxy import path:

```text
/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725/source_proxy/__init__.py
```

Python version: `Python 3.12.3`

## Reproduction Steps

For a fresh operator or agent:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
test -x /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python
ln -s /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy .venv-campaign1
npm run test:coding-regression
```

If `.venv-campaign1` already exists and points to the same environment, do not
recreate it.

## Proof Result

Campaign 0 checkout:

- Branch: `codex/source-proxy-campaign-0-authoritative-base-20260725`
- Head during proof: `f0994d1e865bd934189ef7ca113f9c2eed0a2395`
- Production source delta from verified source/runtime proof commit `ab68745c`
  through this proof: none; only documentation and evidence files changed.

Registered backend result:

- Command: `npm run test:coding-regression`
- Exit status: 0
- Counts: `139 passed, 46 subtests passed in 36.99s`
- Log: `commands/backend_registered.log`
- Metadata: `commands/backend_registered.json`

Frontend/build lane:

- `npm run test:coding-frontend-regression`: exit 0, `193 passed`
- `npm run typecheck`: exit 0
- `CI=1 NEXT_TELEMETRY_DISABLED=1 npm run build`: exit 0

The pre-test command logs record one dirty status entry because the generated
reproducibility evidence directory was already untracked. The `.venv-campaign1`
binding itself did not dirty Git status and is intentionally not committed.

## Evidence Files

- `reproducibility-environment.json`
- `reproducibility-summary.json`
- `commands/backend_registered.log`
- `commands/backend_registered.json`
- `commands/frontend_registered.log`
- `commands/frontend_registered.json`
- `commands/typecheck_registered.log`
- `commands/typecheck_registered.json`
- `commands/build_registered.log`
- `commands/build_registered.json`
