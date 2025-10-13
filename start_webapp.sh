#!/bin/bash
# Startup script for Stock Financial Metrics Scraper Web Application

echo "=================================================="
echo "Stock Financial Metrics Scraper - Web Application"
echo "=================================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  Warning: .env file not found!"
    echo "   Email functionality will not work without proper configuration."
    echo "   Please create a .env file with your email settings."
    echo "   See WEBAPP_README.md for details."
    echo ""
fi

# Check for config.json
if [ ! -f "config.json" ]; then
    echo ""
    echo "⚠️  Warning: config.json not found!"
    echo "   Copying from config.json.example..."
    if [ -f "config.json.example" ]; then
        cp config.json.example config.json
        echo "✓ config.json created from example"
    fi
    echo ""
fi

# Get port from environment or use default
PORT=${PORT:-5173}

echo ""
echo "=================================================="
echo "Starting web application on port $PORT..."
echo "=================================================="
echo ""
echo "Access the application at:"
echo "   http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python webapp.py
