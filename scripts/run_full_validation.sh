#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_ROOT_DEFAULT="$REPO_ROOT/reports/test_runs"

usage() {
  cat <<'USAGE'
Usage: run_full_validation.sh [options]

Options:
  --list                  List available command groups and exit
  --only a,b,c            Comma-separated list of group names to run
  --skip a,b,c            Comma-separated list of group names to skip
  --log-root PATH         Override the root directory where logs are stored
  --stop-on-fail          Abort after the first failing command
  --sleep SECONDS         Seconds to sleep between command groups (default: 1)
  --summary-format FMT    Summary format: tsv (default), json, or both
  -h, --help              Show this message and exit
USAGE
}

normalize_name() {
  local raw="$1"
  # Trim leading/trailing whitespace while preserving inner spacing
  echo "$raw" | sed 's/^ *//;s/ *$//'
}

normalize_array() {
  local -n ref=$1
  local normalized=()
  local item
  for item in "${ref[@]}"; do
    local trimmed="$(normalize_name "$item")"
    if [[ -n "$trimmed" ]]; then
      normalized+=("$trimmed")
    fi
  done
  ref=("${normalized[@]}")
}

in_array() {
  local needle="$1"; shift
  local element
  for element in "$@"; do
    if [[ "$needle" == "$element" ]]; then
      return 0
    fi
  done
  return 1
}

COMMAND_GROUPS=(
  "Static analysis|ruff check ."
  "Type checking|mypy --config-file mypy.ini"
  "Test collection|pytest --collect-only"
  "Core simulation|pytest tests/test_reservoir.py tests/test_simulation_builder.py tests/test_simulation_workflow.py"
  "Agents|pytest tests/test_valve_control_agent.py tests/test_reservoir_perception_agent.py tests/test_csv_inflow_agent.py"
  "Configuration|pytest tests/test_config_to_language.py tests/test_universal_config.py tests/test_output_config.py"
  "Precision framework|python test_precision_enhanced_conversion.py"
  "Precision report|python precision_testing_framework.py"
  "Examples full sweep|python examples/test_all_examples.py"
  "Examples multi-mode|python examples/test_all_modes.py"
  "API core|pytest tests/test_api_endpoints.py tests/test_api_auth.py tests/test_api_monitoring.py"
  "WebSocket|pytest tests/test_websocket_monitor.py tests/test_websocket_stress.py"
  "Agents integration|pytest tests/test_agents_integration.py tests/test_integration_workflow.py"
  "Batch and cloud|pytest tests/test_batch_simulation.py tests/test_cloud_deployment.py tests/test_simulation_workflow.py"
  "Performance|pytest tests/test_performance.py tests/test_performance_stress.py"
  "Security|pytest tests/security/test_security.py tests/test_simple_security.py"
  "Static security|bandit -r ."
  "Dependency audit|safety check"
  "Frontend lint|npm run lint --prefix frontend"
  "Frontend tests|npm run test --prefix frontend"
  "Frontend build|npm run build --prefix frontend"
  "End-to-end|pytest tests/e2e/test_e2e.py"
)

LOG_ROOT="${LOG_ROOT:-$LOG_ROOT_DEFAULT}"
STOP_ON_FAIL_FLAG="${STOP_ON_FAIL:-}"
SLEEP_SECONDS="${SLEEP_SECONDS:-1}"
SUMMARY_FORMAT="tsv"
LIST_ONLY=0
declare -a ONLY_GROUPS=()
declare -a SKIP_GROUPS=()
declare -A KNOWN_GROUPS=()

for entry in "${COMMAND_GROUPS[@]}"; do
  IFS='|' read -r known_name _ <<<"$entry"
  known_name="$(normalize_name "$known_name")"
  KNOWN_GROUPS["$known_name"]=1
done

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list)
      LIST_ONLY=1
      shift
      ;;
    --only)
      if [[ $# -lt 2 ]]; then
        echo "Missing argument for --only" >&2
        usage
        exit 1
      fi
      IFS=',' read -r -a ONLY_GROUPS <<<"$2"
      shift 2
      ;;
    --skip)
      if [[ $# -lt 2 ]]; then
        echo "Missing argument for --skip" >&2
        usage
        exit 1
      fi
      IFS=',' read -r -a SKIP_GROUPS <<<"$2"
      shift 2
      ;;
    --log-root)
      if [[ $# -lt 2 ]]; then
        echo "Missing argument for --log-root" >&2
        usage
        exit 1
      fi
      LOG_ROOT="$2"
      shift 2
      ;;
    --stop-on-fail)
      STOP_ON_FAIL_FLAG=1
      shift
      ;;
    --sleep)
      if [[ $# -lt 2 ]]; then
        echo "Missing argument for --sleep" >&2
        usage
        exit 1
      fi
      SLEEP_SECONDS="$2"
      shift 2
      ;;
    --summary-format)
      if [[ $# -lt 2 ]]; then
        echo "Missing argument for --summary-format" >&2
        usage
        exit 1
      fi
      SUMMARY_FORMAT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

case "$SUMMARY_FORMAT" in
  tsv|json|both)
    ;;
  *)
    echo "Invalid summary format: $SUMMARY_FORMAT" >&2
    exit 1
    ;;
 esac

normalize_array ONLY_GROUPS
normalize_array SKIP_GROUPS

validate_groups() {
  local -n ref=$1
  local label="$2"
  local item
  for item in "${ref[@]}"; do
    if [[ -z "${KNOWN_GROUPS[$item]:-}" ]]; then
      echo "Unknown $label group: $item" >&2
      echo "Use --list to inspect available groups." >&2
      exit 1
    fi
  done
}

validate_groups ONLY_GROUPS "--only"
validate_groups SKIP_GROUPS "--skip"

if ! [[ "$SLEEP_SECONDS" =~ ^([0-9]+)(\.[0-9]+)?$ ]]; then
  echo "Invalid sleep duration: $SLEEP_SECONDS" >&2
  exit 1
fi

if [[ $LIST_ONLY -eq 1 ]]; then
  echo "Available command groups:"
  for entry in "${COMMAND_GROUPS[@]}"; do
    IFS='|' read -r group_name command <<<"$entry"
    group_name="$(normalize_name "$group_name")"
    echo " - $group_name: $command"
  done
  exit 0
fi

RUN_LOG_DIR="$LOG_ROOT/$TIMESTAMP"
mkdir -p "$RUN_LOG_DIR"
RESULTS_FILE="$RUN_LOG_DIR/summary.tsv"
printf "timestamp\tcommand_group\tcommand\tstatus\tlog_file\n" >"$RESULTS_FILE"

STOP_ON_FAIL="$STOP_ON_FAIL_FLAG"

echo "Starting comprehensive validation run at $TIMESTAMP"
echo "Logs will be saved under $RUN_LOG_DIR"

declare -a SUMMARY

run_command() {
  local group_name="$1"
  local command="$2"
  local sanitized="$(echo "$group_name" | tr ' ' '_' | tr -cd '[:alnum:]_')"
  local log_file="$RUN_LOG_DIR/${sanitized}.log"
  local binary="${command%% *}"

  echo "[RUN] $group_name -> $command"

  if ! command -v "$binary" &>/dev/null; then
    echo "[SKIP] Missing executable: $binary" | tee "$log_file"
    now="$(date --iso-8601=seconds)"
    printf "%s\t%s\t%s\t%s\t%s\n" "$now" "$group_name" "$command" "missing" "$log_file" >>"$RESULTS_FILE"
    SUMMARY+=("$group_name: missing ($binary)")
    return 0
  fi

  set +e
  (
    cd "$REPO_ROOT"
    bash -lc "$command"
  ) &> >(tee "$log_file")
  local exit_code=${PIPESTATUS[0]}
  set -e

  local now status_label
  now="$(date --iso-8601=seconds)"
  if [[ $exit_code -eq 0 ]]; then
    status_label="pass"
    echo "[PASS] $group_name"
  else
    status_label="fail"
    echo "[FAIL] $group_name (exit $exit_code)"
  fi

  printf "%s\t%s\t%s\t%s\t%s\n" "$now" "$group_name" "$command" "$status_label" "$log_file" >>"$RESULTS_FILE"
  SUMMARY+=("$group_name: $status_label (log: $log_file)")

  if [[ $exit_code -ne 0 && -n "${STOP_ON_FAIL:-}" ]]; then
    echo "STOP_ON_FAIL set; aborting"
    return $exit_code
  fi

  return 0
}

for entry in "${COMMAND_GROUPS[@]}"; do
  IFS='|' read -r group_name command <<<"$entry"
  group_name="$(normalize_name "$group_name")"

  if ((${#ONLY_GROUPS[@]})) && ! in_array "$group_name" "${ONLY_GROUPS[@]}"; then
    continue
  fi

  if ((${#SKIP_GROUPS[@]})) && in_array "$group_name" "${SKIP_GROUPS[@]}"; then
    echo "[SKIP] $group_name (per user request)"
    now="$(date --iso-8601=seconds)"
    printf "%s\t%s\t%s\t%s\t%s\n" "$now" "$group_name" "$command" "skipped" "n/a" >>"$RESULTS_FILE"
    SUMMARY+=("$group_name: skipped")
    continue
  fi

  if ! run_command "$group_name" "$command"; then
    break
  fi

  if [[ "$SLEEP_SECONDS" != "0" ]]; then
    sleep "$SLEEP_SECONDS"
  fi

done

echo
echo "Validation summary:"
for item in "${SUMMARY[@]}"; do
  echo " - $item"
done

echo "Summary table written to $RESULTS_FILE"

if [[ "$SUMMARY_FORMAT" == "json" || "$SUMMARY_FORMAT" == "both" ]]; then
  JSON_FILE="$RUN_LOG_DIR/summary.json"
  if ! command -v python &>/dev/null; then
    echo "Unable to render JSON summary: python executable not found" >&2
  else
    python - "$RESULTS_FILE" "$JSON_FILE" <<'PY'
import csv
import json
import sys
from pathlib import Path

tsv_path = Path(sys.argv[1])
json_path = Path(sys.argv[2])

with tsv_path.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    rows = list(reader)

with json_path.open("w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

print(f"JSON summary written to {json_path}")
PY
  fi
fi

if [[ "$SUMMARY_FORMAT" == "json" ]]; then
  echo "(TSV summary retained for compatibility)"
fi

echo "Detailed logs in $RUN_LOG_DIR"
