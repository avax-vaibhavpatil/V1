#!/bin/bash

BASE_URL="http://localhost:8000"

echo "🧪 Testing Analytics Studio APIs"
echo ""

test_endpoint() {
    method=$1
    endpoint=$2
    data=$3
    
    url="${BASE_URL}${endpoint}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo "✅ Status: $http_code"
        item_count=$(echo "$body" | grep -o '"id"' | wc -l || echo "0")
        if [ "$item_count" -gt 0 ]; then
            echo "   Found $item_count item(s)"
        fi
        echo "$body" | head -c 200
        echo "..."
    else
        echo "❌ Status: $http_code"
        echo "$body" | head -c 200
    fi
    echo ""
}

# Test health
test_endpoint "GET" "/health"

# Test Projects
test_endpoint "GET" "/api/v1/projects"
test_endpoint "GET" "/api/v1/projects/1"

# Test Datasets
test_endpoint "GET" "/api/v1/datasets"
test_endpoint "GET" "/api/v1/datasets?project_id=1"
test_endpoint "GET" "/api/v1/datasets/sales_data"

# Test Dashboards
test_endpoint "GET" "/api/v1/dashboards"
test_endpoint "GET" "/api/v1/dashboards?project_id=1"
test_endpoint "GET" "/api/v1/dashboards/1"

# Test Semantic Validation
test_endpoint "POST" "/api/v1/semantic/validate" '{"schema_json":{"grain":"daily","time_columns":["sale_date"],"dimensions":[{"name":"region","column":"region_name","type":"string"}],"measures":[{"name":"revenue","column":"amount","type":"numeric","aggregations":["SUM"]}]}}'

# Test Calculation Validation
test_endpoint "POST" "/api/v1/calculations/validate" '{"formula":"revenue * 1.1","available_fields":["revenue","cost"]}'

# Test Dependency Safety
test_endpoint "GET" "/api/v1/dependency-safety/dataset/sales_data/usage"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ API Testing Complete!"
echo ""

