#!/bin/bash
# Simplified Verificarlo Analysis - All modes supported

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${YELLOW}[STEP $1/7]${NC} $2"; }

# Usage
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <source_file> -mode <single|all|pairs|single_and_pairs> [variable_name]"
    echo ""
    echo "Modes:"
    echo "  single <var>       - Test single variable with all opt levels + fastmath variations"
    echo "  all                - Test all variables individually with all opt levels + fastmath"
    echo "  pairs              - Test all combinations of 2 variables with all opt levels + fastmath"
    echo "  single_and_pairs   - Test all singles AND all pairs with all opt levels + fastmath"
    echo ""
    echo "Examples:"
    echo "  $0 archimedes.c -mode single ti"
    echo "  $0 archimedes.c -mode all"
    echo "  $0 archimedes.c -mode pairs"
    echo "  $0 archimedes.c -mode single_and_pairs"
    exit 1
fi

SOURCE_FILE="$1"
MODE_FLAG="$2"
MODE="$3"
VARIABLE="${4:-}"

if [ "$MODE_FLAG" != "-mode" ]; then
    log_error "Second argument must be -mode"
    exit 1
fi

if [ "$MODE" != "single" ] && [ "$MODE" != "all" ] && [ "$MODE" != "pairs" ] && [ "$MODE" != "single_and_pairs" ]; then
    log_error "Mode must be 'single', 'all', 'pairs', or 'single_and_pairs'"
    exit 1
fi

if [ "$MODE" = "single" ] && [ -z "$VARIABLE" ]; then
    log_error "Single mode requires a variable name"
    exit 1
fi

if [ ! -f "$SOURCE_FILE" ]; then
    log_error "Source file not found: $SOURCE_FILE"
    exit 1
fi

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"
OUTPUT_DIR="/workdir/results/$(basename $SOURCE_FILE .c)_${MODE}"
if [ "$MODE" = "single" ]; then
    OUTPUT_DIR="${OUTPUT_DIR}_${VARIABLE}"
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== Verificarlo Analysis ==="
log_info "Source: $SOURCE_FILE"
log_info "Mode: $MODE"
if [ "$MODE" = "single" ]; then
    log_info "Variable: $VARIABLE"
fi
log_info "Output: $OUTPUT_DIR"
echo ""

# Step 1: Analyze source
log_step 1 "Analyzing source..."
python3 "$SCRIPTS_DIR/01_analyze_source.py" \
    --source "$SOURCE_FILE" \
    --output "$OUTPUT_DIR/manifest.json"
[ $? -ne 0 ] && log_error "Step 1 failed" && exit 1
log_success "Analysis complete"
echo ""

# Step 2: Generate variants
log_step 2 "Generating variants..."
case "$MODE" in
    single)
        python3 "$SCRIPTS_DIR/02_generate_variants.py" \
            --manifest "$OUTPUT_DIR/manifest.json" \
            --mode single \
            --variable "$VARIABLE" \
            --output "$OUTPUT_DIR/variants"
        ;;
    all)
        python3 "$SCRIPTS_DIR/02_generate_variants.py" \
            --manifest "$OUTPUT_DIR/manifest.json" \
            --mode all \
            --output "$OUTPUT_DIR/variants"
        ;;
    pairs)
        python3 "$SCRIPTS_DIR/02_generate_variants.py" \
            --manifest "$OUTPUT_DIR/manifest.json" \
            --mode pairs \
            --output "$OUTPUT_DIR/variants"
        ;;
    single_and_pairs)
        python3 "$SCRIPTS_DIR/02_generate_variants.py" \
            --manifest "$OUTPUT_DIR/manifest.json" \
            --mode single_and_pairs \
            --output "$OUTPUT_DIR/variants"
        ;;
esac
[ $? -ne 0 ] && log_error "Step 2 failed" && exit 1
log_success "Variants generated"
echo ""

# Step 3: Compile
log_step 3 "Compiling..."
python3 "$SCRIPTS_DIR/03_compile_variants.py" \
    --variants "$OUTPUT_DIR/variants/manifest.json" \
    --output "$OUTPUT_DIR/binaries"
[ $? -ne 0 ] && log_error "Step 3 failed" && exit 1
log_success "Compilation complete"
echo ""

# Step 4: Validate
log_step 4 "Validating..."
python3 "$SCRIPTS_DIR/04_validate_outputs.py" \
    --binaries "$OUTPUT_DIR/binaries/manifest.json" \
    --output "$OUTPUT_DIR/validation.json"
[ $? -ne 0 ] && log_error "Step 4 failed" && exit 1
log_success "Validation complete"
echo ""

# Step 5: Setup DD
log_step 5 "Setting up Delta-Debug..."
python3 "$SCRIPTS_DIR/05_setup_ddebug.py" \
    --validation "$OUTPUT_DIR/validation.json" \
    --output "$OUTPUT_DIR/ddebug_setup"
[ $? -ne 0 ] && log_error "Step 5 failed" && exit 1
log_success "DD setup complete"
echo ""

# Step 6: Run DD
log_step 6 "Running Delta-Debug..."
python3 "$SCRIPTS_DIR/06_run_ddebug.py" \
    --setup "$OUTPUT_DIR/ddebug_setup/manifest.json" \
    --output "$OUTPUT_DIR/ddebug_results.json"
[ $? -ne 0 ] && log_error "Step 6 failed" && exit 1
log_success "DD complete"
echo ""

# Step 7: Report
log_step 7 "Generating reports..."
python3 "$SCRIPTS_DIR/07_analyze_results.py" \
    --results "$OUTPUT_DIR" \
    --output "$OUTPUT_DIR/report"
[ $? -ne 0 ] && log_error "Step 7 failed" && exit 1
log_success "Reports generated"
echo ""

log_success "=== Analysis Complete ==="
log_info "Results: $OUTPUT_DIR"
log_info "Report: $OUTPUT_DIR/report/report.html"