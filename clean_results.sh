#!/bin/bash
# clean_results.sh - Delete results from verificarlo analysis

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default results directory
RESULTS_DIR="${1:-/workdir/results}"

echo -e "${YELLOW}🗑️  Verificarlo Results Cleanup${NC}"
echo ""

# Check if results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo -e "${RED}✗ Results directory not found: $RESULTS_DIR${NC}"
    exit 1
fi

# Count subdirectories
NUM_ANALYSES=$(find "$RESULTS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)

if [ "$NUM_ANALYSES" -eq 0 ]; then
    echo -e "${YELLOW}ℹ️  No analyses found in $RESULTS_DIR${NC}"
    exit 0
fi

# Show what will be deleted
echo "Found $NUM_ANALYSES analysis result(s) in:"
echo "  $RESULTS_DIR"
echo ""
echo "Contents:"
ls -lh "$RESULTS_DIR" | tail -n +2
echo ""

# Prompt for confirmation
read -p "Delete all results? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deleting...${NC}"
    rm -rf "$RESULTS_DIR"/*
    echo -e "${GREEN}✓ Results cleaned${NC}"
else
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi