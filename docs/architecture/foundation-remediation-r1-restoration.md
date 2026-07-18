# SpiritOS Foundation Remediation R1 Restoration

This runbook restores the immutable Foundation Remediation R1 closeout. The recovery
anchor is local and path-bound; keep the bundle and its sidecar at the recorded paths
while validating the restored checkout.

## Frozen identities

- Source commit `S`: `ce854e613d748581938137b20b79163ec85eca5d`
- Annotated terminal tag: `foundation-remediation-r1-terminal-20260718T102845Z`
- Remediation branch: `codex/spiritos-foundation-remediation-r1-20260717`
- Bundle: `/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T102845Z/foundation-remediation-r1-terminal.bundle`
- SHA-256 sidecar: `/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T102845Z/foundation-remediation-r1-terminal.bundle.sha256`

The annotated tag names the terminal closeout commit `E`. Never guess or copy an
unverified `E` value: dereference it from the tag with `^{commit}`. The first parent
of `E` must be the frozen source commit `S`.

## Verify the recovery anchor

Run these commands on the host that contains the recorded absolute anchor path:

```bash
set -euo pipefail

ANCHOR=/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T102845Z
BUNDLE="$ANCHOR/foundation-remediation-r1-terminal.bundle"
SIDECAR="$BUNDLE.sha256"
TAG=foundation-remediation-r1-terminal-20260718T102845Z

test -f "$BUNDLE"
test -f "$SIDECAR"
cd "$ANCHOR"
sha256sum --check "$(basename "$SIDECAR")"
VERIFY_REPO="$(mktemp -d)"
git init --bare --quiet "$VERIFY_REPO"
git -C "$VERIFY_REPO" bundle verify "$BUNDLE"
rm -rf "$VERIFY_REPO"
git bundle list-heads "$BUNDLE" | grep -F "refs/tags/$TAG"
```

Stop if the sidecar, bundle verification, or terminal-tag lookup fails. Do not
restore from an unverified copy.

## Create a fresh restored checkout

```bash
set -euo pipefail

ANCHOR=/home/source/SpiritOS-foundation-remediation-r1-final-anchor-20260718T102845Z
BUNDLE="$ANCHOR/foundation-remediation-r1-terminal.bundle"
RESTORE=/home/source/SpiritOS-foundation-remediation-r1-20260717
BRANCH=codex/spiritos-foundation-remediation-r1-20260717
TAG=foundation-remediation-r1-terminal-20260718T102845Z
SOURCE=ce854e613d748581938137b20b79163ec85eca5d

test ! -e "$RESTORE"
git clone --no-checkout --branch "$BRANCH" "$BUNDLE" "$RESTORE"
cd "$RESTORE"
git fetch "$BUNDLE" \
  "refs/heads/$BRANCH:refs/remotes/foundation-r1/$BRANCH" \
  "refs/tags/$TAG:refs/tags/$TAG"

test "$(git cat-file -t "refs/tags/$TAG")" = tag
E="$(git rev-parse "$TAG^{commit}")"
test "$(git rev-parse "$E^")" = "$SOURCE"
test "$(git rev-parse "refs/remotes/foundation-r1/$BRANCH")" = "$E"
git merge-base --is-ancestor "$SOURCE" "$E"
git switch --detach "$E"
test "$(git rev-parse HEAD)" = "$E"
```

The configured worktree identity is path-bound. If the original repository still
exists at `RESTORE`, use that exact checkout, omit `git clone`, run the two-ref
`git fetch` against the verified bundle, and then repeat every identity and checkout
assertion. A differently named restore directory is useful for inspection but cannot
satisfy the terminal continuity validator. Remain detached at `E` for validation;
create any future campaign branch only after the restored closeout passes.

## Revalidate the restored terminal tree

Use a Python environment containing the repository's declared validator
dependencies. From the detached `E` checkout run:

```bash
set -euo pipefail

ROOT="$(pwd -P)"
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/validate-foundation-remediation-r1-continuity.py --root "$ROOT"
python3 scripts/validate-foundation-remediation-r1-authority.py --root "$ROOT"
python3 scripts/validate-foundation-remediation-r1-test-profiles.py --root "$ROOT"
python3 scripts/scan-foundation-remediation-r1-secrets.py --root "$ROOT"
python3 scripts/validate-foundation-remediation-r1-evidence.py --root "$ROOT"
python3 scripts/foundation-remediation-r1-completion.py --root "$ROOT"
git fsck --full --strict --no-progress --no-dangling
test -z "$(git status --porcelain --untracked-files=all)"
```

The completion command must emit exactly
`SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE`. A missing external anchor, a different
tag target, a non-annotated tag, an `E` whose first parent is not `S`, dirty output,
or any validator failure invalidates the restoration.

## Start subsequent work

After restoration succeeds, create a new, separately named campaign branch from the
verified terminal commit, not from the historical design Campaign 3 branch:

```bash
E="$(git rev-parse foundation-remediation-r1-terminal-20260718T102845Z^{commit})"
git switch -c <new-campaign-branch> "$E"
```

Do not move, recreate, or overwrite the annotated R1 tag. This runbook does not
authorize a push.
