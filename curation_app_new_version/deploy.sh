#!/bin/bash

# Production deployment script for Curation Signal Optimizer
# This script builds and runs the app in production mode

set -e  # Exit on any error

echo "🚀 Starting production deployment..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Navigate to the app directory
cd "$(dirname "$0")"

echo "📦 Installing dependencies..."
npm install

echo "🔨 Building the application..."
npm run build

echo "🔍 Checking if port 5174 is available..."
if lsof -Pi :5174 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 5174 is already in use. Please stop the existing process or choose a different port."
    echo "To see what's using the port: lsof -i :5174"
    exit 1
fi

echo "🌐 Starting production server on port 5174..."
echo "📍 Your app will be available at:"
echo "   - Local: http://localhost:5174"
echo "   - Network: http://$(hostname -I | awk '{print $1}'):5174"
echo ""
echo "🛑 To stop the server, press Ctrl+C"
echo ""

# Start the production server
npm run prod
