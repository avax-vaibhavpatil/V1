"""Test APIs to verify everything is working."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api(endpoint, method="GET", data=None):
    """Test an API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"\n{'='*60}")
        print(f"{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            print("✅ SUCCESS")
            try:
                result = response.json()
                if isinstance(result, list):
                    print(f"   Returned {len(result)} items")
                    if len(result) > 0:
                        print(f"   First item: {json.dumps(result[0], indent=2, default=str)[:200]}...")
                else:
                    print(f"   Response: {json.dumps(result, indent=2, default=str)[:300]}")
            except:
                print(f"   Response: {response.text[:200]}")
        else:
            print("❌ FAILED")
            print(f"   Error: {response.text[:200]}")
        
        return response.status_code < 400
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"{method} {endpoint}")
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("🧪 Testing Analytics Studio APIs\n")
    
    results = []
    
    # Test health
    results.append(("Health Check", test_api("/health")))
    
    # Test Projects
    results.append(("List Projects", test_api("/api/v1/projects")))
    results.append(("Get Project", test_api("/api/v1/projects/1")))
    
    # Test Datasets
    results.append(("List Datasets (all)", test_api("/api/v1/datasets")))
    results.append(("List Datasets (project 1)", test_api("/api/v1/datasets?project_id=1")))
    results.append(("Get Dataset", test_api("/api/v1/datasets/sales_data")))
    
    # Test Dashboards
    results.append(("List Dashboards (all)", test_api("/api/v1/dashboards")))
    results.append(("List Dashboards (project 1)", test_api("/api/v1/dashboards?project_id=1")))
    results.append(("Get Dashboard", test_api("/api/v1/dashboards/1")))
    
    # Test Semantic
    semantic_schema = {
        "grain": "daily",
        "time_columns": ["sale_date"],
        "dimensions": [{"name": "region", "column": "region_name", "type": "string"}],
        "measures": [{"name": "revenue", "column": "amount", "type": "numeric", "aggregations": ["SUM"]}]
    }
    results.append(("Validate Semantic", test_api("/api/v1/semantic/validate", "POST", {"schema_json": semantic_schema})))
    
    # Test Calculations
    results.append(("Validate Formula", test_api("/api/v1/calculations/validate", "POST", {
        "formula": "revenue * 1.1",
        "available_fields": ["revenue", "cost"]
    })))
    
    # Test Dependency Safety
    results.append(("Check Dataset Usage", test_api("/api/v1/dependency-safety/dataset/sales_data/usage")))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print(f"\n{'='*60}")

if __name__ == "__main__":
    main()

