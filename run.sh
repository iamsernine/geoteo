#!/bin/bash

# AirWatch Startup Script

echo "🌍 Starting AirWatch - Global Air Quality Dashboard"
echo "=================================================="

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your OpenAQ API key"
    echo "   Get your key from: https://explore.openaq.org"
    exit 1
fi

# Check if OpenAQ API key is set
if ! grep -q "OPENAQ_API_KEY=your_openaq_api_key_here" .env; then
    echo "✅ API key configured"
else
    echo "⚠️  Please configure your OpenAQ API key in .env file"
    echo "   Get your key from: https://explore.openaq.org"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ] && [ ! -f "poetry.lock" ]; then
    echo "📦 Installing dependencies..."
    poetry install
fi

# Create necessary directories
mkdir -p data/cache logs exports

echo ""
echo "🚀 Starting application..."
echo "📍 Access the dashboard at: http://localhost:8050"
echo "📋 Press Ctrl+C to stop"
echo ""

# Run the application
poetry run python app.py
