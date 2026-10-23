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
CHART_DIR="${CHART_DIR:-${OPERATOR_ROOT}/helm-charts/charts/simplyblock-operator}"
OUTPUT_FILE="${OUTPUT_FILE:-${DOCS_ROOT}/docs/reference/kubernetes/helm-values.md}"
TEMPLATE_FILE="${TEMPLATE_FILE:-${SCRIPT_DIR}/templates/helm-reference.md.gotmpl}"
HELM_DOCS_VERSION="${HELM_DOCS_VERSION:-v1.14.2}"

if [ ! -f "${CHART_DIR}/Chart.yaml" ]; then
  echo "Could not find the simplyblock-operator chart under ${CHART_DIR}." >&2
  exit 1
fi

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

GOBIN="${WORK_DIR}/bin" go install "github.com/norwoodj/helm-docs/cmd/helm-docs@${HELM_DOCS_VERSION}"

# helm-docs writes next to the chart, so it renders a copy rather than the
# operator checkout.
mkdir -p "${WORK_DIR}/charts"
cp -R "${CHART_DIR}" "${WORK_DIR}/charts/"
CHART_NAME="$(basename "${CHART_DIR}")"
cp "${TEMPLATE_FILE}" "${WORK_DIR}/charts/${CHART_NAME}/reference.md.gotmpl"

"${WORK_DIR}/bin/helm-docs" \
  --chart-search-root "${WORK_DIR}/charts" \
  --template-files reference.md.gotmpl \
  --output-file REFERENCE.md \
  --sort-values-order file \
  --log-level warning

CHART_VERSION="$(sed -n 's/^version: *"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "${CHART_DIR}/Chart.yaml")"

{
  cat <<FRONTMATTER
---
title: "Simplyblock Helm Chart Values"
description: "Generated reference of every value of the simplyblock-operator Helm chart, with its type and default, grouped by top-level key."
weight: 20101
---

<!--
This file is generated. Do not edit it by hand.
Run scripts/helm-reference-gen.sh from the documentation repository.
-->

This page lists every value of the \`simplyblock-operator\` Helm chart, version \`${CHART_VERSION}\`, as it appears in
the chart's \`values.yaml\`. What the chart renders, and example values files for common deployments, are described in
[Simplyblock Helm Chart](index.md).
FRONTMATTER
  cat "${WORK_DIR}/charts/${CHART_NAME}/REFERENCE.md"
} > "${OUTPUT_FILE}"

echo "Generated ${OUTPUT_FILE}"
