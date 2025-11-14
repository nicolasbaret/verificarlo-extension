#!/bin/bash
# Script to run Verificarlo CI tests on verhulst

set -e
export LC_ALL=C

echo "=== Running Verificarlo CI Tests ==="

# Clean previous builds
rm -f verhulst *.vfcrun.h5

# Run the test
echo "Running vfc_ci test..."
vfc_ci test

echo ""
echo "=== Test Complete ==="
echo "Results saved to *.vfcrun.h5"
echo ""
echo "To view the report, run:"
echo "  vfc_ci serve"
echo ""
echo "Then open http://localhost:8080 in your browser"