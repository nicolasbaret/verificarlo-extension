#!/bin/bash
# Build the verificarlo-analysis Docker image

set -e

IMAGE_NAME="verificarlo-analysis"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Building Verificarlo Analysis Docker Image             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

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
