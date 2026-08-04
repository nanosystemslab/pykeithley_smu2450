#!/usr/bin/env bash
#
# Physical hardware smoke test for the Keithley 2450 SourceMeter.
#
# Connect a known test resistor (default 10 kOhm) across the front-panel
# FORCE HI / FORCE LO terminals, then run:
#
#     ./scripts/hardware_test.sh <ip-address>
#
# Options:
#     --resistor OHMS   Test resistor value (default: 10000)
#     --port PORT       TCP port (default: 5025)
#     --yes             Skip the interactive safety confirmation
#
# Each step's output is written to logs/hardware-test-<timestamp>/ so the
# results can be committed to the repository as a record of the test.

set -u

# ── Argument parsing ────────────────────────────────────────────────

IP=""
RESISTOR=10000
PORT=5025
SKIP_CONFIRM=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --resistor) RESISTOR="$2"; shift 2 ;;
        --port)     PORT="$2"; shift 2 ;;
        --yes)      SKIP_CONFIRM=1; shift ;;
        -h|--help)  sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*)         echo "Unknown option: $1" >&2; exit 2 ;;
        *)          IP="$1"; shift ;;
    esac
done

if [[ -z "$IP" ]]; then
    echo "Usage: $0 <ip-address> [--resistor OHMS] [--port PORT] [--yes]" >&2
    exit 2
fi

# ── Locate the CLI ──────────────────────────────────────────────────

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

if command -v poetry >/dev/null 2>&1 && poetry run pykeithley_smu2450 --help >/dev/null 2>&1; then
    CLI=(poetry run pykeithley_smu2450)
elif command -v pykeithley_smu2450 >/dev/null 2>&1; then
    CLI=(pykeithley_smu2450)
else
    CLI=(env "PYTHONPATH=$REPO_DIR/src" python3 -m pykeithley_smu2450)
fi

# ── Log directory ───────────────────────────────────────────────────

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOGDIR="logs/hardware-test-$TIMESTAMP"
mkdir -p "$LOGDIR"

{
    echo "date:        $(date)"
    echo "host:        $(hostname)"
    echo "user:        $(whoami)"
    echo "ip_address:  $IP"
    echo "port:        $PORT"
    echo "resistor:    $RESISTOR ohm"
    echo "cli:         ${CLI[*]}"
    echo "git_commit:  $(git rev-parse --short HEAD 2>/dev/null || echo 'no commits yet')"
    echo "python:      $(python3 --version 2>&1)"
} > "$LOGDIR/00-meta.log"

# ── Safety confirmation ─────────────────────────────────────────────

echo "════════════════════════════════════════════════════════════════"
echo " Keithley 2450 hardware smoke test"
echo "════════════════════════════════════════════════════════════════"
echo
echo " Instrument:    $IP:$PORT"
echo " Test resistor: $RESISTOR ohm"
echo " Log directory: $LOGDIR"
echo
echo " Before continuing, confirm:"
echo "   1. A ~$RESISTOR ohm resistor is connected across the"
echo "      front-panel FORCE HI / FORCE LO terminals."
echo "   2. The instrument command set is TSP"
echo "      (Menu > Communication > Settings > Command Set)."
echo "   3. The front-panel TERMINAL setting matches where the"
echo "      resistor is connected (FRONT)."
echo
if [[ "$SKIP_CONFIRM" -eq 0 ]]; then
    read -r -p " Press Enter to start the test (Ctrl-C to abort)... "
fi
echo

# ── Test helpers ────────────────────────────────────────────────────

PASS=0
FAIL=0
STEP=0
SUMMARY="$LOGDIR/summary.log"
: > "$SUMMARY"

run_step() {
    # run_step <name> <command...>
    local name="$1"; shift
    STEP=$((STEP + 1))
    local logfile
    logfile="$LOGDIR/$(printf '%02d' "$STEP")-$name.log"
    echo "── Step $STEP: $name"
    echo "   \$ $*"
    if "$@" > >(tee "$logfile") 2> >(tee -a "$logfile" >&2); then
        echo "   PASS"
        echo "step $STEP $name: PASS" >> "$SUMMARY"
        PASS=$((PASS + 1))
        return 0
    else
        echo "   FAIL (see $logfile)"
        echo "step $STEP $name: FAIL" >> "$SUMMARY"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

check_within() {
    # check_within <name> <measured> <expected> <tolerance-fraction>
    local name="$1" measured="$2" expected="$3" tol="$4"
    awk -v m="$measured" -v e="$expected" -v t="$tol" -v n="$name" '
        BEGIN {
            m = (m < 0) ? -m : m
            e = (e < 0) ? -e : e
            err = (e == 0) ? 0 : (m - e) / e
            err = (err < 0) ? -err : err
            printf "   %s: measured=%.6e expected=%.6e error=%.1f%%\n", \
                n, m, e, err * 100
            exit (err <= t) ? 0 : 1
        }'
}

# ── Tests ───────────────────────────────────────────────────────────

# 1. Identify -- proves TCP connectivity and TSP command set
run_step "identify" "${CLI[@]}" "$IP" --port "$PORT" identify
IDN="$(cat "$LOGDIR/01-identify.log" 2>/dev/null || true)"
if [[ "$IDN" != *2450* ]]; then
    echo "   WARNING: identity string does not mention 2450: '$IDN'"
    echo "warning: unexpected identity string" >> "$SUMMARY"
fi

# 2. Reset to a known state
run_step "reset" "${CLI[@]}" "$IP" --port "$PORT" reset

# 3. Source 1 V, measure current (expect ~V/R through the resistor)
SRC_V=1.0
EXPECTED_I="$(awk -v v="$SRC_V" -v r="$RESISTOR" 'BEGIN { printf "%.6e", v / r }')"
if run_step "source-voltage" "${CLI[@]}" "$IP" --port "$PORT" \
        sourcev "$SRC_V" --limit 0.01 --nplc 10 -n 3 -d 0.2; then
    MEASURED_I="$(tail -n 1 "$LOGDIR/03-source-voltage.log")"
    if check_within "current" "$MEASURED_I" "$EXPECTED_I" 0.20; then
        echo "current check: PASS" >> "$SUMMARY"
    else
        echo "   FAIL: measured current is >20% from expected"
        echo "current check: FAIL" >> "$SUMMARY"
        FAIL=$((FAIL + 1))
    fi
fi

# 4. Source 100 uA, measure voltage (expect ~I*R across the resistor)
SRC_I=100e-6
EXPECTED_V="$(awk -v i="$SRC_I" -v r="$RESISTOR" 'BEGIN { printf "%.6e", i * r }')"
VLIMIT="$(awk -v e="$EXPECTED_V" 'BEGIN {
    v = e * 2; if (v < 2) v = 2; if (v > 20) v = 20; printf "%.3f", v }')"
if run_step "source-current" "${CLI[@]}" "$IP" --port "$PORT" \
        sourcei "$SRC_I" --limit "$VLIMIT" --nplc 10 -n 3 -d 0.2; then
    MEASURED_V="$(tail -n 1 "$LOGDIR/04-source-current.log")"
    if check_within "voltage" "$MEASURED_V" "$EXPECTED_V" 0.20; then
        echo "voltage check: PASS" >> "$SUMMARY"
    else
        echo "   FAIL: measured voltage is >20% from expected"
        echo "voltage check: FAIL" >> "$SUMMARY"
        FAIL=$((FAIL + 1))
    fi
fi

# 5. I-V sweep 0 -> 1 V (expect a straight line through the resistor)
if run_step "iv-sweep" "${CLI[@]}" "$IP" --port "$PORT" \
        sweep 0 1.0 --points 11 --limit 0.01; then
    LINES="$(wc -l < "$LOGDIR/05-iv-sweep.log" | tr -d ' ')"
    if [[ "$LINES" -eq 12 ]]; then  # header + 11 points
        echo "   sweep returned all 11 points"
        echo "sweep point count: PASS" >> "$SUMMARY"
    else
        echo "   FAIL: expected 12 CSV lines, got $LINES"
        echo "sweep point count: FAIL" >> "$SUMMARY"
        FAIL=$((FAIL + 1))
    fi
fi

# 6. Ensure the output is off before leaving the bench
run_step "output-off" "${CLI[@]}" "$IP" --port "$PORT" off

# ── Summary ─────────────────────────────────────────────────────────

echo
echo "════════════════════════════════════════════════════════════════"
echo " Results: $PASS passed, $FAIL failed"
echo " Logs:    $LOGDIR"
echo "════════════════════════════════════════════════════════════════"
cat "$SUMMARY"
echo

if [[ "$FAIL" -eq 0 ]]; then
    echo "All hardware tests passed."
    echo
    echo "Commit the test logs as a record of the verified instrument:"
    echo
    echo "    git add $LOGDIR"
    echo "    git commit -m \"Add passing 2450 hardware test logs ($TIMESTAMP)\""
    echo
    exit 0
else
    echo "Some tests FAILED -- review the logs before committing:"
    echo
    echo "    less $SUMMARY"
    echo
    echo "Common causes: wrong resistor value (pass --resistor), SCPI"
    echo "command set instead of TSP, or resistor on the wrong terminals."
    exit 1
fi
