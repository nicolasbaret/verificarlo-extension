#!/bin/bash
# Quick analysis with minimal configuration

SOURCE_FILE="$1"

if [ -z "$SOURCE_FILE" ]; then
    echo "Usage: $0 <source_file.c>"
    exit 1
fi

# Minimal configuration
export STRATEGY="minimal"
export OPT_LEVELS="O0"
export FASTMATH="false"
export PARALLEL="false"
export DD_BACKENDS="mca"

./orchestrate.sh "$SOURCE_FILE" "results/quick_$(basename $SOURCE_FILE .c)"