#!/bin/bash
# OOUX ORCA CTA Matrix - One-line startup
# Usage: ./quick_start.sh

echo "🎯 OOUX ORCA CTA Matrix - Quick Start"
echo "Starting server on http://localhost:8000"
echo "Test Guide: http://localhost:8000/api/v1/test-guide"
echo "Demo Matrix: http://localhost:8000/api/v1/demo/cta-matrix"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start database services quietly
docker compose up -d postgres redis 2>/dev/null || echo "⚠️ Database services not available (using mock data)"

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
