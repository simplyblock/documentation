#!/bin/bash
# (Re)deploys the Command Assistant API on its EC2 host: pulls the branch,
# builds the image, reads the Anthropic key from SSM Parameter Store, and
# (re)starts the API and Caddy. Run as root on the host:
#   sudo bash /opt/docs-assistant/src/assistant/deploy/deploy.sh
set -euo pipefail

BRANCH="${BRANCH:-$(cat /opt/docs-assistant/branch 2>/dev/null || echo main)}"
REGION="${REGION:-eu-central-1}"
KEY_PARAM="${KEY_PARAM:-/docs-assistant/anthropic-api-key}"
DIR=/opt/docs-assistant

cd "$DIR/src"
git fetch --depth 1 origin "$BRANCH"
git reset --hard FETCH_HEAD
echo "$BRANCH" > "$DIR/branch"

docker build -t docs-assistant assistant/

KEY=$(aws ssm get-parameter --region "$REGION" --with-decryption --name "$KEY_PARAM" --query Parameter.Value --output text)
umask 077
{ echo "ANTHROPIC_API_KEY=$KEY"; cat "$DIR/config.env"; } > "$DIR/env"
umask 022

docker network inspect docs-assistant >/dev/null 2>&1 || docker network create docs-assistant
docker rm -f docs-assistant >/dev/null 2>&1 || true
docker run -d --name docs-assistant --restart unless-stopped --network docs-assistant \
  --env-file "$DIR/env" -v /var/log/docs-assistant:/var/log/docs-assistant docs-assistant

cp assistant/deploy/Caddyfile "$DIR/Caddyfile"
if docker inspect caddy >/dev/null 2>&1; then
  docker exec caddy caddy reload --config /etc/caddy/Caddyfile
else
  docker run -d --name caddy --restart unless-stopped --network docs-assistant -p 80:80 -p 443:443 \
    --env-file "$DIR/caddy.env" -v "$DIR/Caddyfile:/etc/caddy/Caddyfile:ro" -v caddy_data:/data caddy:2
fi
docker image prune -f >/dev/null
echo "deployed $(git rev-parse --short HEAD) from $BRANCH"
