#!/bin/bash
# Build the verificarlo-analysis Docker image

set -e

IMAGE_NAME="verificarlo-analysis"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Building Verificarlo Analysis Docker Image             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if required files exist
echo "📋 Checking required files..."
REQUIRED_FILES=("Dockerfile" "archimedes_analyzer.py" "visualize_results.py")
MISSING=0

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing!)"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "❌ Missing required files. Please ensure all files are in the current directory."
    exit 1
fi

echo ""
echo "🔨 Building Docker image: $IMAGE_NAME"
echo "   Base: verificarlo/verificarlo:latest"
echo "   Adding: Python deps + analysis scripts"
echo ""

# Build with progress
docker build -t $IMAGE_NAME .

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                 ✅ BUILD SUCCESSFUL                        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📦 Image: $IMAGE_NAME"
    echo "🚀 To start: ./start_analysis_container.sh"
    echo ""
    echo "Image details:"
    docker images $IMAGE_NAME
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi