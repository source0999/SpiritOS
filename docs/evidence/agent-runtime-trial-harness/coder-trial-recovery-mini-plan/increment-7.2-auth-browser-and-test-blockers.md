# Increment 7.2 - Auth, Browser, and Test Blockers

Date: 2026-06-08

## Auth

Command-line `/coding` remains auth-protected:

```text
curl http://127.0.0.1:3000/coding
HTTP/1.1 401 Unauthorized
{"error":"unauthorized"}
```

No auth bypass was added. Production auth was not weakened.

## Browser

The in-app browser could not open either local route:

```text
http://127.0.0.1:3000/coding -> net::ERR_BLOCKED_BY_CLIENT
https://10.0.0.186:3000/coding -> net::ERR_BLOCKED_BY_CLIENT
```

Because the browser client blocked navigation, I could not complete visual/manual browser selection of the dropdown from this environment.

## Source Proxy

Port 8787 was initially down. I started Source Proxy with the existing repo script:

```text
npm run proxy:https:lan
```

After startup, `https://127.0.0.1:8787/v1/models` returned `200 OK`.

Model status showed:

- `openai` enabled: `gpt-4o-mini`
- `anthropic` enabled
- `deepseek` enabled
- `coder` / local Ollama disabled: `ollama_unreachable`
- `local` / Hermes disabled: `ollama_unreachable`

The first Coder 001 backend attempt was blocked because `SOURCE_PROXY_CODER_MODEL_ALIAS` resolved to `coder`, which was not an enabled alias. I restarted only the Source Proxy process I started with `SOURCE_PROXY_CODER_MODEL_ALIAS=openai` as the narrow runtime workaround for this Gate 7 attempt.

## Focused Vitest

Focused Vitest remains blocked:

```text
npx --no-install vitest run src/lib/coding/__tests__/dummy-coder-10-prompts.test.ts src/lib/coding/__tests__/dummy-coder-10-grader.test.ts src/lib/coding/__tests__/dummy-project-summary.test.ts --reporter=dot

Error: Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js' imported from Z:\node_modules\vitest\dist\module-evaluator.js
```

No root package rewrite or dependency churn was attempted.

## Safe Checks

`npx --no-install tsc --noEmit --pretty false` passed.

`git diff --check` passed, with only line-ending warnings from existing tracked files.
