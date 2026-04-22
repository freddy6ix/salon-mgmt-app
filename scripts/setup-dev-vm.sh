#!/usr/bin/env bash
# Run once on the dev VM after first boot to set up the full dev environment.
set -euo pipefail

echo "=== Installing system packages ==="
sudo apt-get update -q
sudo apt-get install -y -q \
  git curl wget unzip build-essential \
  ca-certificates gnupg lsb-release

echo "=== Installing Docker ==="
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -q
sudo apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER"

echo "=== Installing uv (Python) ==="
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

echo "=== Installing Node.js 20 ==="
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y -q nodejs

echo "=== Installing gcloud CLI (already present via VM, skipping) ==="

echo "=== Cloning repo ==="
git clone https://github.com/freddy6ix/salon-mgmt-app.git ~/salon-mgmt-app

echo ""
echo "=== Done! Next steps ==="
echo "1. Log out and back in (or run 'newgrp docker') for Docker group to take effect"
echo "2. cd ~/salon-mgmt-app"
echo "3. cp backend/.env.example backend/.env  (then fill in values)"
echo "4. docker compose up -d  (starts local Postgres)"
echo "5. cd backend && uv sync && uv run alembic upgrade head"
echo "6. cd ../frontend && npm install"
