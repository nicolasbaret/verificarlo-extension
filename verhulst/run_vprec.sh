#!/bin/bash
# Script to run VPREC backend on verhulst benchmark

set -e
export LC_ALL=C

# Check all arguments
if [ "$#" -lt 1 ]; then
  echo "usage: run_vprec.sh preset [--error-mode=MODE]"
  echo "   OR: run_vprec.sh --precision-binary64=PRECISION [--range-binary64=RANGE] [--error-mode=MODE]"
  echo ""
  echo "Preset mode:"
  echo "      preset is one of: binary16, binary32, bfloat16, tensorfloat, fp24, PXR24"
  echo ""
  echo "Manual mode:"
  echo "      --precision-binary64=PRECISION  : pseudo-mantissa bit length (e.g., 10, 24, 53)"
  echo "      --range-binary64=RANGE         : exponent bit length (optional, e.g., 8, 11)"
  echo ""
  echo "Error mode (optional for both preset and manual):"
  echo "      --error-mode=MODE              : error mode (rel, abs, all)"
  exit 1
fi

REAL="DOUBLE"
ERROR_MODE=""

# Parse error mode from arguments (can be anywhere)
for arg in "$@"; do
  if [[ "$arg" == --error-mode=* ]]; then
    ERROR_MODE="$arg"
    break
  fi
done

# Determine if using preset or manual mode
if [[ "$1" == --precision-binary64=* ]]; then
  # Manual mode
  MODE="manual"
  VPREC_ARGS="$1"
  PRECISION=$(echo "$1" | sed 's/--precision-binary64=//')
  
  # Check for range parameter
  if [[ "$2" == --range-binary64=* ]]; then
    VPREC_ARGS="$VPREC_ARGS $2"
    RANGE=$(echo "$2" | sed 's/--range-binary64=//')
    OUTPUT_SUFFIX="prec${PRECISION}_range${RANGE}"
  else
    OUTPUT_SUFFIX="prec${PRECISION}"
  fi
else
  # Preset mode
  MODE="preset"
  VPREC_PRESET=$1
  VPREC_ARGS="--preset=$VPREC_PRESET"
  OUTPUT_SUFFIX="$VPREC_PRESET"
fi

# Add error mode to VPREC_ARGS if provided
if [ -n "$ERROR_MODE" ]; then
  VPREC_ARGS="$VPREC_ARGS $ERROR_MODE"
  # Extract error mode value for filename
  ERROR_MODE_VALUE=$(echo "$ERROR_MODE" | sed 's/--error-mode=//')
  OUTPUT_SUFFIX="${OUTPUT_SUFFIX}_${ERROR_MODE_VALUE}"
fi

# Print options
if [ "$MODE" = "preset" ]; then
  echo "VPREC preset = $VPREC_PRESET, Real Type = $REAL"
else
  echo "VPREC manual mode: $VPREC_ARGS, Real Type = $REAL"
fi

# Compile source code with verificarlo
verificarlo -D ${REAL} verhulst.c -o verhulst

# Run verhulst for all values x in [-1.0:1.0:0.1]
echo "setting VFC_BACKENDS for VPREC to: libinterflop_vprec.so $VPREC_ARGS"
export VFC_BACKENDS="libinterflop_vprec.so $VPREC_ARGS"

echo "i x result" > verhulst-${OUTPUT_SUFFIX}.tab
for x in $(seq -1.0 0.01 1.0); do
    echo 1 $(./verhulst $x) >> verhulst-${OUTPUT_SUFFIX}.tab
done

echo "Results saved to verhulst-${OUTPUT_SUFFIX}.tab"
if [ "$MODE" = "preset" ]; then
  echo "You can plot the results using: ./plot_vprec.py verhulst-${OUTPUT_SUFFIX}.tab $VPREC_PRESET"
else
  echo "You can plot the results using: ./plot_vprec.py verhulst-${OUTPUT_SUFFIX}.tab"
fi