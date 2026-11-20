#!/bin/bash
# Compute Engine startup script: install and run the fruit API on port 8080.
set -euxo pipefail
APP_DIR=/opt/fn-gcp

if [ ! -d "$APP_DIR" ]; then
  apt-get update
  apt-get install -y git python3-venv
  git clone https://github.com/noorff70/fn-gcp.git "$APP_DIR"
  python3 -m venv "$APP_DIR/venv"
  "$APP_DIR/venv/bin/pip" install --no-cache-dir -r "$APP_DIR/requirements.txt"
fi

cat > /etc/systemd/system/fruit.service <<'EOF'
[Unit]
Description=Fruit FastAPI
After=network-online.target

[Service]
WorkingDirectory=/opt/fn-gcp
Environment=DATABASE_URL=data/inventory.db
ExecStart=/opt/fn-gcp/venv/bin/uvicorn fruit.main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now fruit
