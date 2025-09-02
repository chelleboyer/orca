#!/bin/bash

echo "🔧 OOUX ORCA CTA Matrix Troubleshooting"
echo "========================================="

# Check if server is running
echo "1. Checking server status..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ Server is running"
else
    echo "   ❌ Server is not running"
    echo "   Starting server..."
    cd /home/michelle/PROJECTS/ooux/orca
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    sleep 3
fi

# Test endpoints
echo ""
echo "2. Testing endpoints..."

endpoints=(
    "/health"
    "/api/v1/test-simple"
    "/api/v1/demo/cta-matrix"
    "/api/v1/demo/cta-matrix-grid"
    "/api/v1/demo/cta-cell/role1/obj1"
)

for endpoint in "${endpoints[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$endpoint)
    if [ "$status" = "200" ]; then
        echo "   ✅ $endpoint ($status)"
    else
        echo "   ❌ $endpoint ($status)"
    fi
done

# Test static files
echo ""
echo "3. Testing static files..."

static_files=(
    "/static/css/matrix.css"
    "/static/js/cta-matrix.js"
    "/static/css/dashboard.css"
)

for file in "${static_files[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000$file)
    if [ "$status" = "200" ]; then
        echo "   ✅ $file ($status)"
    else
        echo "   ❌ $file ($status)"
    fi
done

echo ""
echo "4. Quick Start URLs:"
echo "   🧪 Simple Test:    http://localhost:8000/api/v1/test-simple"
echo "   🎯 Demo Matrix:     http://localhost:8000/api/v1/demo/cta-matrix"
echo "   📚 API Docs:        http://localhost:8000/docs"
echo ""
echo "5. If you see 'Not Found' errors:"
echo "   - Check browser console for JavaScript errors"
echo "   - Verify HTMX is loading: https://unpkg.com/htmx.org@1.9.6"
echo "   - Try the simple test page first"
echo "   - Check server logs in terminal"
echo ""
echo "✅ Troubleshooting complete!"
