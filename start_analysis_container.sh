#!/bin/bash
# Start Verificarlo Analysis Container
# This script launches the custom verificarlo container with your current directory mounted

set -e

IMAGE_NAME="verificarlo-analysis"
CONTAINER_NAME="verificarlo-analysis-session"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Verificarlo Analysis Container Launcher             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if image exists
if ! docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
    echo "⚠️  Image '$IMAGE_NAME' not found."
    echo "📦 Building the image first..."
    echo ""
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile" ]; then
        echo "❌ Error: Dockerfile not found in current directory!"
        echo "   Please ensure Dockerfile, archimedes_analyzer.py, and visualize_results.py are present."
        exit 1
    fi
    
    # Build the image
    docker build -t $IMAGE_NAME .
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Image built successfully!"
        echo ""
    else
        echo "❌ Image build failed!"
        exit 1
    fi
fi

# Remove any existing container with the same name
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🧹 Removing existing container..."
    docker rm -f $CONTAINER_NAME >/dev/null 2>&1
fi

echo "🚀 Starting container..."
echo "📁 Mounting current directory: $(pwd)"
echo ""
echo "   Inside the container, your files will be at: /workdir"
echo "   Results will be saved to: $(pwd)/analysis_results"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the container interactively
# -v mounts current directory to /workdir
# -it gives interactive terminal
# --rm removes container on exit
# --name gives it a recognizable name

docker run \
    -v "$(pwd)":/workdir \
    -it \
    --rm \
    --name $CONTAINER_NAME \
    $IMAGE_NAME

echo ""
echo "👋 Container session ended."
echo "   Results (if any) are saved in: $(pwd)/analysis_results"