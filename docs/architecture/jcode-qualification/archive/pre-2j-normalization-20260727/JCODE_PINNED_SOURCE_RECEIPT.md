# JCode Pinned Source Receipt

| Field | Value |
| --- | --- |
| Upstream | `https://github.com/1jehuang/jcode.git` |
| Audit checkout | `/home/source/.codex-audits/jcode-20260727T0145Z` |
| Default/checked-out branch | `master` |
| Pinned commit | `2444e7b6bc80d421ae3ee404081bdb41150a1830` |
| Commit time | `2026-07-26T18:38:36-07:00` |
| Commit subject | `Update README.md` |
| Nearest ancestor tag | `v0.58.0` |
| Describe | `v0.58.0-51-g2444e7b6` |
| Workspace version | `0.58.0` (`Cargo.toml:3`) |
| License | MIT (`LICENSE`) |
| Audit checkout status | clean |
| Audit timestamp | `2026-07-27T02:28:53Z` |

`VERIFIED FACT`: tags `v0.59.0` and `v0.60.0` exist in the fetched repository,
but neither is an ancestor of the pinned `master` commit. GitHub's release page
identified `v0.58.0` as the latest published release at audit time. Conclusions
are therefore pinned to the exact SHA, not to a floating release label.

Commands:

```text
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git describe --tags --always --long
git merge-base --is-ancestor v0.59.0 HEAD
git merge-base --is-ancestor v0.60.0 HEAD
git status --short
```

No installation script was piped to a shell. Rust was installed only beneath
`/home/source/.codex-audits/rust-cargo` and
`/home/source/.codex-audits/rust-toolchains`; no global JCode binary or upstream
binary was added to SpiritOS.
