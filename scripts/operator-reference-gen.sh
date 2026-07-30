
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Prefer the operator checkout managed by `./doc-builder update-repositories`
# (pinned via scripts/operator.lock). Fall back to a sibling checkout for local
# development. Override explicitly by setting OPERATOR_ROOT.
if [ -z "${OPERATOR_ROOT:-}" ]; then
  if [ -d "${DOCS_ROOT}/scripts/operator-repo" ]; then
    OPERATOR_ROOT="${DOCS_ROOT}/scripts/operator-repo"
  else
    OPERATOR_ROOT="$(cd "${DOCS_ROOT}/../simplyblock-manager" && pwd)"
  fi
fi
OUTPUT_FILE="${OUTPUT_FILE:-${DOCS_ROOT}/docs/reference/operator-api.md}"
CONFIG_FILE="${CONFIG_FILE:-${SCRIPT_DIR}/operator-crd-ref-docs.yaml}"
CRD_REF_DOCS_REPO="${CRD_REF_DOCS_REPO:-https://github.com/simplyblock/crd-ref-docs.git}"
CRD_REF_DOCS_REF="${CRD_REF_DOCS_REF:-master}"

TMP_FILE="$(mktemp)"
CRD_REF_DOCS_DIR="$(mktemp -d)"
CRD_REF_DOCS_BIN="$(mktemp -u)"
trap 'rm -f "${TMP_FILE}" "${CRD_REF_DOCS_BIN}"; rm -rf "${CRD_REF_DOCS_DIR}"' EXIT

git clone --quiet --depth 1 --branch "${CRD_REF_DOCS_REF}" \
  "${CRD_REF_DOCS_REPO}" "${CRD_REF_DOCS_DIR}"

go build -C "${CRD_REF_DOCS_DIR}" -o "${CRD_REF_DOCS_BIN}" .

"${CRD_REF_DOCS_BIN}" \
  --source-path "${OPERATOR_ROOT}/api" \
  --config "${CONFIG_FILE}" \
  --renderer markdown \
  --output-path "${TMP_FILE}"

{
  cat <<'FRONTMATTER'
---
title: "Simplyblock Operator API Reference"
description: "Generated API reference for Simplyblock operator Custom Resource Definitions (CRDs)."
weight: 20091
---

<!--
This file is generated. Do not edit it by hand.
Run scripts/operator-reference-gen.sh from the documentation repository.
-->

FRONTMATTER
  cat "${TMP_FILE}"
} > "${OUTPUT_FILE}"

echo "Generated ${OUTPUT_FILE}"
