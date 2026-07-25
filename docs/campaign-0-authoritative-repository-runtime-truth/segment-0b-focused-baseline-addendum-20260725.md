# Campaign 0 Segment 0B - Focused Baseline Addendum

status: `SEGMENT_0B_EVIDENCE_ADDENDUM`

This addendum corrects the Segment 0B focused-baseline receipt before Segment
0C production repair work. It does not reopen Segment 0B and does not make the
Campaign 0 source base regression-green.

## Reported 99 Passed / 2 Skipped Command

The exact command used for the Segment 0B `99 passed, 2 skipped` focused
fallback run was:

```bash
cd /home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725 \
/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python \
  -m pytest \
  -p no:cacheprovider \
  -q \
  source_proxy/tests/test_canonical_context_broker.py \
  source_proxy/tests/test_context_source_readiness.py \
  source_proxy/tests/test_prompt_packet_context_metadata.py
```

Selected test-node list:

- `source_proxy/tests/test_canonical_context_broker.py`
- `source_proxy/tests/test_context_source_readiness.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`

Observed result:

- `99 passed`
- `2 skipped`
- duration `20.27s`

## Runner And Import Identity

Observed at `2026-07-25T22:58:07Z`.

| Field | Observed value |
|---|---|
| Python executable | `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python` |
| Virtual environment path | `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy` |
| Source Proxy import | `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725/source_proxy/__init__.py` |
| Import conclusion | Python/pytest runner came from the existing Source Proxy venv; `source_proxy` resolved from the Campaign 0 worktree via `PYTHONPATH` |

## Pre-Test And Post-Test Identity

| Moment | Branch | HEAD | Dirty count |
|---|---|---|---:|
| Pre-test | `codex/source-proxy-campaign-0-authoritative-base-20260725` | `bf6c73114d22e4947dcee8629a29352e3aeded82` | `0` |
| Post-test | `codex/source-proxy-campaign-0-authoritative-base-20260725` | `bf6c73114d22e4947dcee8629a29352e3aeded82` | `0` |

The isolated worktree did not contain its own `.venv-source-proxy` at Segment
0B time, so this addendum preserves the fallback dependency boundary explicitly.
