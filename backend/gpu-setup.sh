#!/usr/bin/env bash
# ─── Spirit OS · AMD RX 580 ROCm Host Setup ───────────────────────────────────
#
# Run this script ONCE on the host before `docker compose up -d`.
# Installs the minimum ROCm host-side libraries needed for the Docker container
# to export /dev/kfd and /dev/dri correctly to the Ollama ROCm image.
#
# Hardware target: Dell Precision · Ryzen 7600 · XFX RX 580 (Ellesmere/gfx803)
# OS:              Ubuntu 24.04 (Noble)
# ROCm target:     6.x (matches ollama/ollama:rocm image)
#
# Usage:
#   sudo bash backend/gpu-setup.sh
#
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

[[ $EUID -ne 0 ]] && die "This script must be run as root: sudo bash $0"

# ── Step 1: Add AMD ROCm APT repository ──────────────────────────────────────
info "Step 1/6 · Adding AMD ROCm APT repository..."

CODENAME=$(lsb_release -cs 2>/dev/null || echo "noble")
ROCM_VERSION="6.3.1"
ROCM_REPO="https://repo.radeon.com/rocm/apt/${ROCM_VERSION}"

# Remove any stale entries from previous failed attempts (6.0, 6.1, etc.)
rm -f /etc/apt/sources.list.d/rocm.list /etc/apt/sources.list.d/amdgpu.list

if [[ ! -f /etc/apt/sources.list.d/amdgpu.list ]]; then
  # Download and install AMD's official GPG key
  curl -fsSL https://repo.radeon.com/rocm/rocm.gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/rocm.gpg

  # amdgpu DKMS repo (kernel driver)
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] \
    https://repo.radeon.com/amdgpu/latest/ubuntu ${CODENAME} main" \
    > /etc/apt/sources.list.d/amdgpu.list

  # ROCm user-space libraries repo
  echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/rocm.gpg] \
    ${ROCM_REPO} ${CODENAME} main" \
    > /etc/apt/sources.list.d/rocm.list

  ok "ROCm APT repository added."
else
  ok "ROCm APT repository already configured — skipping."
fi

# ── Step 2: Update package index ─────────────────────────────────────────────
info "Step 2/6 · Updating package index..."
apt-get update -qq
ok "Package index updated."

# ── Step 3: Install amdgpu-dkms (kernel driver) ──────────────────────────────
info "Step 3/6 · Installing amdgpu-dkms (kernel-level GPU driver)..."
info "  This may take several minutes — DKMS compiles the kernel module."
apt-get install -y amdgpu-dkms
ok "amdgpu-dkms installed."

# ── Step 4: Install ROCm user-space tools (rocminfo, rocm-smi) ───────────────
info "Step 4/6 · Installing ROCm user-space tools..."

# Ubuntu 24.04 ships its own 'rocminfo' (5.7.x) from the main repo.
# AMD's rocm repo ships 'rocminfo' (1.0.0.6xxxx) with different versioning.
# apt resolves the wrong one unless we pin AMD's repo at higher priority.
cat > /etc/apt/preferences.d/rocm-pin << 'EOF'
Package: *
Pin: origin repo.radeon.com
Pin-Priority: 1001
EOF

apt-get update -qq

# Install only the diagnostic tools — rocm-hip-runtime is not needed on the
# host because the Docker container ships its own complete ROCm runtime.
apt-get install -y rocminfo rocm-smi-lib
ok "ROCm tools installed."

# ── Step 5: Add current user to render + video groups ────────────────────────
info "Step 5/6 · Configuring /dev/kfd and /dev/dri group memberships..."

# Determine the non-root user who will run docker compose
REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo '')}"

if [[ -n "$REAL_USER" && "$REAL_USER" != "root" ]]; then
  usermod -aG render,video "$REAL_USER"
  ok "Added $REAL_USER to render and video groups."
else
  warn "Could not determine non-root user — add yourself manually:"
  warn "  sudo usermod -aG render,video \$USER && newgrp render"
fi

# Print the actual GIDs so you can verify docker-compose.yml group_add values
RENDER_GID=$(getent group render | cut -d: -f3 || echo "NOT FOUND")
VIDEO_GID=$(getent group video  | cut -d: -f3 || echo "NOT FOUND")
info "  render GID = ${RENDER_GID}   (docker-compose.yml has \"993\" — $([ "$RENDER_GID" = "993" ] && echo 'MATCH ✓' || echo "MISMATCH — update group_add to \"${RENDER_GID}\""))"
info "  video  GID = ${VIDEO_GID}"

# ── Step 6: Validate /dev nodes exist ────────────────────────────────────────
info "Step 6/6 · Validating /dev nodes..."

MISSING=0
for node in /dev/kfd /dev/dri; do
  if [[ -e "$node" ]]; then
    ok "  $node present"
  else
    warn "  $node NOT FOUND — amdgpu module may not be loaded yet"
    MISSING=1
  fi
done

echo ""
echo "─────────────────────────────────────────────────────────────────────────"
if [[ $MISSING -eq 1 ]]; then
  warn "One or more /dev nodes are missing."
  warn "A REBOOT is required to load the new amdgpu-dkms kernel module."
  warn "After rebooting, re-run this script to verify, then:"
  warn "  cd /home/source/SpiritOS/backend && sudo docker compose up -d"
else
  ok "All /dev nodes present."
  echo ""
  info "Next steps:"
  info "  1. Kill host Ollama if it is running:"
  info "       sudo fuser -k 11434/tcp"
  info "       sudo systemctl stop ollama && sudo systemctl disable ollama"
  info ""
  info "  2. Start the Spirit OS backend:"
  info "       cd /home/source/SpiritOS/backend"
  info "       sudo docker compose down && sudo docker compose up -d"
  info ""
  info "  3. Verify GPU inside container (wait ~40s for start_period):"
  info "       sudo docker exec spirit-ollama rocm-smi"
  info "       sudo docker exec spirit-ollama rocminfo | grep -A3 'Ellesmere\|gfx803'"
  info "       sudo docker logs spirit-ollama 2>&1 | grep -i 'library\|rocm\|cpu'"
  info ""
  info "  4. Pull dolphin3:"
  info "       sudo docker exec spirit-ollama ollama pull dolphin3"
  info ""
  info "  SUCCESS indicator in logs:"
  info "       msg=\"inference compute\" library=rocm    ← GPU active"
  info "       msg=\"inference compute\" library=cpu     ← still on CPU (bad)"
fi
echo "─────────────────────────────────────────────────────────────────────────"
