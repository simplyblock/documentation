#!/usr/bin/env bash
set -euo pipefail

# Resolves the latest matching simplyblock-operator release tag for a given
# sbcli version and writes it to scripts/operator.lock (next to sbcli.lock).
#
# "Latest matching" means the operator tag whose MAJOR.MINOR equals the sbcli
# version's MAJOR.MINOR, with the highest patch level. For example, an sbcli
# version of 26.2.4 resolves to the newest operator tag v26.2.y (e.g. v26.2.8).
#
# Usage:
#   ./scripts/operator-lock.sh [<sbcli-version>]
#
# If no version is passed, it is read from scripts/sbcli.lock. If operator.lock
# already exists, it is left untouched. If no matching operator tag exists (for
# example for older releases that predate the operator), the lock is skipped
# without failing.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPERATOR_REPO_URL="${OPERATOR_REPO_URL:-https://github.com/simplyblock/simplyblock-operator.git}"
OPERATOR_LOCK="${OPERATOR_LOCK:-${SCRIPT_DIR}/operator.lock}"
SBCLI_LOCK="${SBCLI_LOCK:-${SCRIPT_DIR}/sbcli.lock}"

VERSION="${1:-}"
if [ -z "${VERSION}" ] && [ -f "${SBCLI_LOCK}" ]; then
  VERSION="$(cat "${SBCLI_LOCK}")"
fi

if [ -z "${VERSION}" ]; then
  echo "No sbcli version supplied and no ${SBCLI_LOCK} present." >&2
  exit 1
fi

if [ -f "${OPERATOR_LOCK}" ]; then
  echo "operator.lock already present ($(cat "${OPERATOR_LOCK}")), leaving untouched."
  exit 0
fi

MAJOR_MINOR="$(printf '%s' "${VERSION}" | grep -oE '^[0-9]+\.[0-9]+' || true)"
if [ -z "${MAJOR_MINOR}" ]; then
  echo "Could not derive MAJOR.MINOR from sbcli version '${VERSION}'." >&2
  exit 1
fi

# Escape dots so they are matched literally in the tag regex.
MM_REGEX="$(printf '%s' "${MAJOR_MINOR}" | sed 's/\./\\./g')"

echo "Resolving latest simplyblock-operator tag matching v${MAJOR_MINOR}.* ..."
OPERATOR_TAG="$(git ls-remote --tags --refs "${OPERATOR_REPO_URL}" \
  | sed -E 's#.*refs/tags/##' \
  | grep -E "^v${MM_REGEX}\.[0-9]+$" \
  | sort -V \
  | tail -n1 || true)"

if [ -z "${OPERATOR_TAG}" ]; then
  echo "No simplyblock-operator release tag found matching v${MAJOR_MINOR}.* — skipping operator lock." >&2
  exit 0
fi

echo "Locking simplyblock-operator to ${OPERATOR_TAG}"
printf '%s\n' "${OPERATOR_TAG}" > "${OPERATOR_LOCK}"
