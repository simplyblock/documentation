#!/usr/bin/env bash
#
# Runs the documentation quality gates.
#
# Every gate runs, even when an earlier one failed, so a single run reports all
# problems at once. The script exits non-zero if any gate failed.
#
# Usage:
#   ./scripts/quality-gate.sh                  # run all gates
#   ./scripts/quality-gate.sh spelling         # run the named gates only
#
# To add a gate, append its name to ALL_GATES and implement the matching
# gate_<name> function together with its gate_<name>_description.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PYTHON="${PYTHON:-python3}"

if [ -t 1 ]; then
  BOLD="\033[1m"
  RED="\033[31m"
  GREEN="\033[32m"
  RESET="\033[0m"
else
  BOLD=""
  RED=""
  GREEN=""
  RESET=""
fi

# The available gates, in execution order.
ALL_GATES=(spelling terminology american voice oxford syntax)

gate_spelling_description="Brand name spelling and casing"
gate_spelling() {
  "${PYTHON}" "${SCRIPT_DIR}/check-simplyblock-spelling.py"
}

gate_terminology_description="Spelling of product names, projects and acronyms"
gate_terminology() {
  "${PYTHON}" "${SCRIPT_DIR}/check-terminology.py"
}

gate_american_description="American English spelling"
gate_american() {
  "${PYTHON}" "${SCRIPT_DIR}/check-american-english.py"
}

gate_voice_description="Impersonal voice, without addressing the reader or the author"
gate_voice() {
  "${PYTHON}" "${SCRIPT_DIR}/check-voice.py"
}

gate_oxford_description="Oxford comma candidates (warnings only)"
gate_oxford() {
  "${PYTHON}" "${SCRIPT_DIR}/check-oxford-comma.py"
}

gate_syntax_description="Markdown structure, links, frontmatter and placeholders"
gate_syntax() {
  "${PYTHON}" "${SCRIPT_DIR}/check-mkdocs-syntax.py"
}

ensure_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Command $1 not found. Please install it." >&2
    exit 1
  fi
}

ensure_command "${PYTHON}"

gates=("$@")
if [ ${#gates[@]} -eq 0 ]; then
  gates=("${ALL_GATES[@]}")
fi

for gate in "${gates[@]}"; do
  if ! declare -F "gate_${gate}" >/dev/null; then
    echo "Unknown quality gate: ${gate}" >&2
    echo "Available gates: ${ALL_GATES[*]}" >&2
    exit 2
  fi
done

cd "${DOCS_ROOT}"

# Every gate writes into its own log, so that its errors can be listed again once
# all gates have run. Without that, the first failure of a long run has scrolled
# away by the time the last gate is done.
LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/quality-gate.XXXXXX")"
cleanup() {
  rm -rf "${LOG_DIR}"
}
trap cleanup EXIT

failed_count=0
failed_gates=()
error_count=0

for gate in "${gates[@]}"; do
  description="gate_${gate}_description"
  echo ""
  echo -e "${BOLD}▶ ${gate}: ${!description}${RESET}"

  # "pipefail" is set, so the status of the gate survives the pipe into tee.
  if "gate_${gate}" 2>&1 | tee "${LOG_DIR}/${gate}.log"; then
    echo -e "${GREEN}✔ ${gate} passed${RESET}"
  else
    gate_errors="$(grep -c "^ERROR" "${LOG_DIR}/${gate}.log" || true)"
    if [ "${gate_errors}" -gt 0 ]; then
      echo -e "${RED}✘ ${gate} failed with ${gate_errors} error(s)${RESET}"
    else
      echo -e "${RED}✘ ${gate} failed without reporting a finding${RESET}"
    fi
    failed_count=$((failed_count + 1))
    failed_gates+=("${gate}")
    error_count=$((error_count + gate_errors))
  fi
done

echo ""
if [ "${failed_count}" -eq 0 ]; then
  echo -e "${GREEN}All ${#gates[@]} quality gate(s) passed.${RESET}"
  exit 0
fi

# The collected errors of the whole run, so that the list to work through is in
# one place instead of spread over the output of every gate.
if [ "${error_count}" -gt 0 ]; then
  echo -e "${BOLD}${RED}━━ ${error_count} error(s) in ${failed_count} of ${#gates[@]} quality gate(s) ━━${RESET}"
else
  echo -e "${BOLD}${RED}━━ ${failed_count} of ${#gates[@]} quality gate(s) failed ━━${RESET}"
fi
for gate in "${failed_gates[@]}"; do
  echo ""
  echo -e "${BOLD}${gate}:${RESET}"
  if grep -q "^ERROR" "${LOG_DIR}/${gate}.log"; then
    # Only the finding itself, its excerpt stays in the output of the gate above.
    grep "^ERROR" "${LOG_DIR}/${gate}.log"
  else
    # A gate that fails without reporting a finding did not run to its end.
    echo "  The gate itself failed, it reported no finding. Its last output was:"
    tail -n 5 "${LOG_DIR}/${gate}.log" | sed 's/^/  /'
  fi
done

echo ""
echo -e "${RED}${failed_count} of ${#gates[@]} quality gate(s) failed: ${failed_gates[*]}${RESET}"
exit 1
