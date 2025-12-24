#!/bin/bash

# Kaaj Frontend Startup Script
# This script starts the React frontend development server

set -e

echo "🎨 Starting Kaaj Frontend"
echo "=========================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file"
    else
        echo "# API Configuration" > .env
        echo "VITE_API_BASE_URL=http://localhost:8000" >> .env
        echo "✅ Created .env file with default values"
    fi
fi

echo ""
echo "🚀 Starting development server..."
echo "Frontend will be available at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the development server
npm run dev

