# SpiritOS Foundation Remediation R1 Restoration

This runbook restores and revalidates the immutable Foundation Remediation R1
closeout. Continuity and canonical authority are path-bound: the restored checkout
must be exactly `/home/source/SpiritOS-foundation-remediation-r1-20260717`.

## Frozen identities

- Accepted source commit `S`: `ec204d63e431d10501c67db0264082db6e4d31e4`
- Annotated terminal tag: `foundation-remediation-r1-terminal-20260718T120047Z`
- Remediation branch: `codex/spiritos-foundation-remediation-r1-20260717`
- Required checkout path: `/home/source/SpiritOS-foundation-remediation-r1-20260717`
- Bundle: `/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T120047Z/foundation-remediation-r1-terminal.bundle`
- SHA-256 sidecar: `/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T120047Z/foundation-remediation-r1-terminal.bundle.sha256`

Candidate `d6dd49438ef186c6e28cf33276434b0c609aa471` was rejected and is not a
restoration target. Commit `S` contains the terminal-independent completion
regression repair. The production lifecycle was then cleanly reproved at `S`, and
all 22 registered closeout profiles passed at that same source.

The annotated tag names the terminal closeout commit `E`. Do not copy an assumed
value for `E`; always dereference it from the tag with `^{commit}`. The first parent
of `E` must be accepted source `S`.

## Verify the recovery anchor

Run on the host containing the recorded absolute anchor path:

```bash
set -euo pipefail

ANCHOR=/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T120047Z
BUNDLE="$ANCHOR/foundation-remediation-r1-terminal.bundle"
SIDECAR="$BUNDLE.sha256"
TAG=foundation-remediation-r1-terminal-20260718T120047Z

test -f "$BUNDLE"
test -f "$SIDECAR"
cd "$ANCHOR"
sha256sum --check "$(basename "$SIDECAR")"

VERIFY_REPO="$(mktemp -d)"
trap 'rm -rf "$VERIFY_REPO"' EXIT
git init --bare --quiet "$VERIFY_REPO"
git -C "$VERIFY_REPO" bundle verify "$BUNDLE"
git bundle list-heads "$BUNDLE" | grep -F "refs/tags/$TAG"
rm -rf "$VERIFY_REPO"
trap - EXIT
```

Stop if the sidecar, bundle verification, or terminal-tag lookup fails. The rejected
candidate must not be substituted for `S`, tagged, or treated as accepted evidence.

## Restore at the configured path

The following fresh-clone workflow intentionally refuses to continue if the
configured path already exists. An operator must preserve or move an existing tree
aside after reviewing it; this runbook never deletes it.

```bash
set -euo pipefail

ANCHOR=/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T120047Z
BUNDLE="$ANCHOR/foundation-remediation-r1-terminal.bundle"
ROOT=/home/source/SpiritOS-foundation-remediation-r1-20260717
BRANCH=codex/spiritos-foundation-remediation-r1-20260717
TAG=foundation-remediation-r1-terminal-20260718T120047Z
SOURCE=ec204d63e431d10501c67db0264082db6e4d31e4

test ! -e "$ROOT"
git clone --no-checkout --branch "$BRANCH" "$BUNDLE" "$ROOT"
cd "$ROOT"
git fetch "$BUNDLE" \
  "refs/heads/$BRANCH:refs/remotes/foundation-r1/$BRANCH" \
  "refs/tags/$TAG:refs/tags/$TAG"

test "$(pwd -P)" = "$ROOT"
test "$(git cat-file -t "refs/tags/$TAG")" = tag
E="$(git rev-parse "$TAG^{commit}")"
test "$(git rev-parse "$E^")" = "$SOURCE"
test "$(git rev-parse "refs/remotes/foundation-r1/$BRANCH")" = "$E"
git merge-base --is-ancestor "$SOURCE" "$E"
git switch --detach "$E"
test "$(git rev-parse HEAD)" = "$E"
```

For an intact repository already at the exact configured path, verify that it has no
unpreserved work, fetch the same branch and tag refspecs from the verified bundle,
and repeat every path, tag-type, parent, branch-tip, ancestry, and detached-checkout
assertion above. A checkout at another path is not continuity-equivalent.

## Revalidate terminal `E`

Use the declared Python environment from the detached `E` checkout:

```bash
set -euo pipefail

ROOT=/home/source/SpiritOS-foundation-remediation-r1-20260717
PY=/home/source/SpiritOS/.venv/bin/python
export PATH=/home/source/SpiritOS/.venv/bin:/usr/local/bin:/usr/bin:/bin
export PYTHONDONTWRITEBYTECODE=1

cd "$ROOT"
test "$(pwd -P)" = "$ROOT"
test -x "$PY"
E="$(git rev-parse foundation-remediation-r1-terminal-20260718T120047Z^{commit})"
test "$(git rev-parse HEAD)" = "$E"

"$PY" scripts/validate-foundation-remediation-r1-continuity.py --root "$ROOT"
"$PY" scripts/validate-foundation-remediation-r1-authority.py --root "$ROOT"
"$PY" scripts/validate-foundation-remediation-r1-test-profiles.py --root "$ROOT"
"$PY" scripts/scan-foundation-remediation-r1-secrets.py --root "$ROOT"
"$PY" scripts/validate-foundation-remediation-r1-evidence.py --root "$ROOT"
"$PY" scripts/foundation-remediation-r1-completion.py --root "$ROOT"
git fsck --full --strict --no-progress --no-dangling
test -z "$(git status --porcelain --untracked-files=all)"
```

The completion command must emit exactly
`SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE`. Validation must confirm the clean
source-bound reproof and 22/22 accepted profile receipts. A missing external anchor,
a non-annotated or differently targeted tag, an `E` whose first parent is not `S`,
the wrong checkout path, dirty output, or any validator failure invalidates the
restoration.

## Start subsequent work

Only after restoration passes may a separately named future campaign branch from
the verified terminal commit:

```bash
cd /home/source/SpiritOS-foundation-remediation-r1-20260717
E="$(git rev-parse foundation-remediation-r1-terminal-20260718T120047Z^{commit})"
git switch -c <new-campaign-branch> "$E"
```

Do not branch from the rejected candidate or historical design Campaign 3 branch.
Do not move, recreate, or overwrite the annotated R1 tag. This runbook does not
authorize a push.
