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
ALL_GATES=(spelling terminology american voice syntax)

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

failed_count=0
failed_gates=""

for gate in "${gates[@]}"; do
  description="gate_${gate}_description"
  echo ""
  echo -e "${BOLD}▶ ${gate}: ${!description}${RESET}"

  if "gate_${gate}"; then
    echo -e "${GREEN}✔ ${gate} passed${RESET}"
  else
    echo -e "${RED}✘ ${gate} failed${RESET}"
    failed_count=$((failed_count + 1))
    failed_gates="${failed_gates} ${gate}"
  fi
done

echo ""
if [ "${failed_count}" -eq 0 ]; then
  echo -e "${GREEN}All ${#gates[@]} quality gate(s) passed.${RESET}"
  exit 0
fi

echo -e "${RED}${failed_count} of ${#gates[@]} quality gate(s) failed:${failed_gates}${RESET}"
exit 1
