# Cross-platform repository verification

Read `worktree-manifest.md` first. It is the live topology source; paths, branch names, HEADs, and service owners must be verified at the time of use.

## Dell/Linux (SSH)

Run from the selected worktree:

```bash
git worktree list --porcelain
git update-index -q --refresh && git status --short --branch --untracked-files=no
git rev-parse --show-toplevel && git branch --show-current && git rev-parse HEAD
git check-attr --all -- .gitattributes README.md scripts/source-proxy-bootstrap.sh scripts/source-proxy-bootstrap.ps1
for port in 8787 3000 3002; do
  pid=$(lsof -tiTCP:$port -sTCP:LISTEN | head -n1)
  [ -n "$pid" ] && printf '%s ' "$port" && readlink -f "/proc/$pid/cwd" && tr '\0' ' ' < "/proc/$pid/cmdline" && echo
done
curl -kfsS https://127.0.0.1:8787/healthcheck
curl -kfsSI https://127.0.0.1:3000/
curl -fsSI http://127.0.0.1:3002/
sha256sum /home/source/.spiritos-preservation/20260711-full-cleanup/{plan1-3-history.bundle,lane2-proxy-history.bundle,shared-generated-evidence-fixture.tar.gz,plan1-3-crlf-resolution.txt}
```

`git status` is not sufficient for binary drift when filesystem metadata is cached. For any suspect tracked binary, compare the working hash with its `HEAD` blob:

```bash
path='path/to/file.png'; sha256sum "$path"; git show "HEAD:$path" | sha256sum
```

## Windows/SMB (`Z:\`)

```powershell
git -C Z:\ update-index -q --refresh
git -C Z:\ status --short --branch --untracked-files=no
git -C Z:\ branch --show-current
git -C Z:\ rev-parse HEAD
$path = 'path/to/file.png'
$working = (Get-FileHash (Join-Path Z:\ $path) -Algorithm SHA256).Hash
$head = (ssh spirit "git -C /home/source/SpiritOS show HEAD:$path | sha256sum").Split()[0]
"working=$working head=$head"
```

Windows can inspect the SMB-visible SpiritFlix checkout, but it cannot determine whether a Linux-only worktree is registered, prunable, serving a port, or holds preservation archives. SSH to the Dell for those checks. If Windows and cached Linux `git status` disagree, trust the explicit working-file and `HEAD`-blob SHA-256 comparison, refresh the index, and resolve the content before committing.
