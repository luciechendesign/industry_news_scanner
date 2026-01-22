#!/bin/bash
# Start the Industry News Scanner API server

echo "Starting Industry News Scanner API..."
echo "Server will be available at http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

