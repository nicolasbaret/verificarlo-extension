#!/bin/bash
# Example: Analyze archimedes.c

# Set the source file
SOURCE_FILE="/workdir/archimedes/archimedes.c"

# Set configuration
export FUNCTION_NAME="archimedes"
export STRATEGY="single"
export OPT_LEVELS="O0 O3"
export FASTMATH="true"
export PARALLEL="true"
export JOBS="4"
export DD_BACKENDS="rr mca cancellation"

# Run analysis
./orchestrate.sh "$SOURCE_FILE" "results/archimedes_analysis"