#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OPERATOR_ROOT="${OPERATOR_ROOT:-$(cd "${DOCS_ROOT}/../simplyblock-manager" && pwd)}"
OUTPUT_FILE="${OUTPUT_FILE:-${DOCS_ROOT}/docs/reference/operator-api.md}"
CONFIG_FILE="${CONFIG_FILE:-${SCRIPT_DIR}/operator-crd-ref-docs.yaml}"
CRD_REF_DOCS_VERSION="${CRD_REF_DOCS_VERSION:-v0.3.0}"

TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

go run "github.com/elastic/crd-ref-docs@${CRD_REF_DOCS_VERSION}" \
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
