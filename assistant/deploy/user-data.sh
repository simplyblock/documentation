#!/bin/bash
# EC2 user data (Amazon Linux 2023) for the Command Assistant host.
# Placeholders __HOST__ and __BRANCH__ are filled in at launch.
set -euxo pipefail
dnf install -y docker git
systemctl enable --now docker
mkdir -p /opt/docs-assistant /var/log/docs-assistant
chown 10001 /var/log/docs-assistant
git clone --depth 1 -b __BRANCH__ https://github.com/simplyblock/documentation.git /opt/docs-assistant/src
echo __BRANCH__ > /opt/docs-assistant/branch
cat > /opt/docs-assistant/config.env <<CFG
ASSISTANT_CORS_ORIGINS=https://docs.simplyblock.io,https://docstest.simplyblock.io
ASSISTANT_LOG_FILE=/var/log/docs-assistant/assistant.jsonl
ASSISTANT_TRUST_FORWARDED_FOR=1
ASSISTANT_DAILY_BUDGET_USD=25
CFG
echo "ASSISTANT_HOST=__HOST__" > /opt/docs-assistant/caddy.env
bash /opt/docs-assistant/src/assistant/deploy/deploy.sh
