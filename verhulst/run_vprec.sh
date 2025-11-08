#!/bin/bash
# Script to run VPREC backend on verhulst benchmark

set -e
export LC_ALL=C

# Check all arguments
if [ "$#" -ne 2 ]; then
  echo "usage: run_verhulst_vprec.sh [FLOAT | DOUBLE] preset"
  echo "      preset is one of the VPREC presets: binary16, binary32, bfloat16, tensorfloat, fp24, PXR24"
  echo "      or use custom format like: --precision-binary64=PRECISION"
  exit 1
fi

REAL=$1
VPREC_PRESET=$2

# Check real
case "${REAL}" in
    FLOAT) ;;
    DOUBLE) ;;
    *)
	echo "Inexisting precision "${REAL}", choose between [FLOAT | DOUBLE]"
	exit 1
esac

# Print options
echo "VPREC preset = $VPREC_PRESET, Real Type = $REAL"

# Compile source code with verificarlo
verificarlo -D ${REAL} verhulst.c -o verhulst

# Run verhulst for all values x in [-1.0:1.0:0.1]
# producing a .tab file with three columns:
#   - i: sample number (always 1 for VPREC since it's deterministic)
#   - x: input value
#   - result: verhulst result on x
export VFC_BACKENDS="libinterflop_vprec.so --preset=$VPREC_PRESET"

echo "i x result" > verhulst-${REAL}-${VPREC_PRESET}.tab
for x in $(seq -1.0 0.01 1.0); do
    # Since VPREC is a deterministic backend only a single run is needed
    echo 1 $(./verhulst $x) >> verhulst-${REAL}-${VPREC_PRESET}.tab
done

echo "Results saved to verhulst-${REAL}-${VPREC_PRESET}.tab"
echo "You can plot the results using: ./plot_vprec.py verhulst-${REAL}-${VPREC_PRESET}.tab $VPREC_PRESET"
exit