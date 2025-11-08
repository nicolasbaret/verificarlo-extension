#!/bin/bash
# Script to run VPREC backend on verhulst benchmark

set -e
export LC_ALL=C

# Check all arguments
if [ "$#" -lt 1 ]; then
  echo "usage: run_verhulst_vprec.sh preset"
  echo "   OR: run_verhulst_vprec.sh --precision-binary64=PRECISION [--range-binary64=RANGE]"
  echo ""
  echo "Preset mode:"
  echo "      preset is one of: binary16, binary32, bfloat16, tensorfloat, fp24, PXR24"
  echo ""
  echo "Manual mode:"
  echo "      --precision-binary64=PRECISION  : pseudo-mantissa bit length (e.g., 10, 24, 53)"
  echo "      --range-binary64=RANGE         : exponent bit length (optional, e.g., 8, 11)"
  exit 1
fi

REAL="DOUBLE"

# Determine if using preset or manual mode
if [[ "$1" == --precision-binary64=* ]]; then
  # Manual mode
  MODE="manual"
  VPREC_ARGS="$@"
  # Extract precision value for filename
  PRECISION=$(echo "$1" | sed 's/--precision-binary64=//')
  if [[ "$2" == --range-binary64=* ]]; then
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

# Print options
if [ "$MODE" = "preset" ]; then
  echo "VPREC preset = $VPREC_PRESET, Real Type = $REAL"
else
  echo "VPREC manual mode: $VPREC_ARGS, Real Type = $REAL"
fi

# Compile source code with verificarlo
verificarlo -D ${REAL} verhulst.c -o verhulst

# Run verhulst for all values x in [-1.0:1.0:0.1]
# producing a .tab file with three columns:
#   - i: sample number (always 1 for VPREC since it's deterministic)
#   - x: input value
#   - result: verhulst result on x
echo "setting VFC_BACKENDS for VPREC to: libinterflop_vprec.so $VPREC_ARGS"
export VFC_BACKENDS="libinterflop_vprec.so $VPREC_ARGS"

echo "i x result" > verhulst-${OUTPUT_SUFFIX}.tab
for x in $(seq -1.0 0.01 1.0); do
    # Since VPREC is a deterministic backend only a single run is needed
    echo 1 $(./verhulst $x) >> verhulst-${OUTPUT_SUFFIX}.tab
done

echo "Results saved to verhulst-${OUTPUT_SUFFIX}.tab"
if [ "$MODE" = "preset" ]; then
  echo "You can plot the results using: ./plot_vprec.py verhulst-${OUTPUT_SUFFIX}.tab $VPREC_PRESET"
else
  echo "You can plot the results using: ./plot_vprec.py verhulst-${OUTPUT_SUFFIX}.tab"
fi
exit