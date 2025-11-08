#!/bin/bash
# Compile verhulst.c using Verificarlo with MCA backend

set -e
export LC_ALL=C

# Check all arguments
if [ "$#" -ne 3 ]; then
  echo "usage: run_verhulst.sh [FLOAT | DOUBLE] vprecision mode"
  echo "      vprecision is the MCA Virtual Precision (a positive integer)"
  echo "      mode is MCA Mode, one of [ mca | pb | rr ]"
  exit 1
fi

REAL=$1
VERIFICARLO_PRECISION=$2
VERIFICARLO_MCAMODE=$3

# Check real
case "${REAL}" in
    FLOAT) ;;
    DOUBLE) ;;
    *)
	echo "Inexisting precision "${REAL}", choose between [FLOAT | DOUBLE]"
	exit 1
esac

# Print options
echo "Verificarlo Precision = $VERIFICARLO_PRECISION, Real Type = $REAL"

# Compile source code with verificarlo
verificarlo -D ${REAL} verhulst.c -o verhulst

# Run 20 iterations of verhulst for all values x in [-1:1.0:0.1]
# producing a .tab file with three columns:
#   - i: sample number
#   - x: input value
#   - result: verhulst result on x
export VFC_BACKENDS="libinterflop_mca.so --precision-binary32=$VERIFICARLO_PRECISION --precision-binary64=$VERIFICARLO_PRECISION --mode $VERIFICARLO_MCAMODE"

echo "i x result" > verhulst-${REAL}-${VERIFICARLO_PRECISION}.tab
for x in $(seq -1.0 0.01 1.0); do
    for i in $(seq 1 20); do
      echo $i $(./verhulst $x) >> verhulst-${REAL}-${VERIFICARLO_PRECISION}.tab
    done
done

echo "Results saved to verhulst-${REAL}-${VERIFICARLO_PRECISION}.tab"
echo "You can plot the results using: ./plot.py verhulst-${REAL}-${VERIFICARLO_PRECISION}.tab $VERIFICARLO_PRECISION"
exit