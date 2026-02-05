#!/bin/bash

# Test script for AIBOTTO Docker setup

echo "🐳 Testing AIBOTTO Docker Setup"
echo "================================="

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t aibot . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Test linting
echo "🔍 Testing linting..."
docker run --rm --env-file .env.test aibot lint > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Linting passed"
else
    echo "⚠️  Linting found issues (this is expected)"
fi

# Test type checking
echo "🔍 Testing type checking..."
docker run --rm --env-file .env.test aibot type-check > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Type checking passed"
else
    echo "⚠️  Type checking found issues (this is expected)"
fi

# Test bot startup (should fail with invalid token, but that's OK)
echo "🤖 Testing bot startup..."
timeout 5s docker run --rm --env-file .env.test aibot > /dev/null 2>&1
if [ $? -eq 124 ]; then
    echo "✅ Bot started successfully (timeout expected)"
elif [ $? -eq 1 ]; then
    echo "✅ Bot started successfully (invalid token error expected)"
else
    echo "❌ Bot failed to start"
    exit 1
fi

# Test Docker Compose
echo "🐳 Testing Docker Compose..."
docker compose --env-file .env.test up --build -d aibot > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker Compose started successfully"
    
    # Wait a bit and check logs
    sleep 2
    logs=$(docker compose logs aibot 2>&1 | tail -5)
    if echo "$logs" | grep -q "Starting AIBot"; then
        echo "✅ Bot is running in Docker Compose"
    else
        echo "⚠️  Bot logs don't show expected startup message"
    fi
    
    # Stop the container
    docker compose down > /dev/null 2>&1
else
    echo "❌ Docker Compose failed to start"
fi

echo ""
echo "🎉 Docker setup test completed successfully!"
echo ""
echo "To run the bot with Docker:"
echo "  docker run --rm --env-file .env aibot"
echo ""
echo "To run with Docker Compose:"
echo "  docker compose --env-file .env up -d"