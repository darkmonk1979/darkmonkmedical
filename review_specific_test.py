#!/usr/bin/env python3
"""
Specific tests for the review request requirements
"""
import requests
import json
import sys

def test_health_endpoint():
    """Test GET /api/health as specified in review request"""
    print("Testing GET /api/health...")
    try:
        response = requests.get("https://medfinder-9.preview.emergentagent.com/api/health", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Expected 200 OK, got {response.status_code}")
            return False
            
        data = response.json()
        
        # Check required fields
        if data.get("status") != "healthy":
            print(f"❌ Expected status: 'healthy', got: {data.get('status')}")
            return False
            
        if not data.get("services", {}).get("database") == "connected":
            print(f"❌ Expected services.database: 'connected', got: {data.get('services', {}).get('database')}")
            return False
            
        print("✅ Health endpoint test passed")
        print(f"   Response: {json.dumps(data, indent=2)}")
        return True
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

def test_pbs_search():
    """Test POST /api/search/pbs as specified in review request"""
    print("\nTesting POST /api/search/pbs...")
    try:
        payload = {"query": "paracetamol", "search_type": "pbs"}
        response = requests.post(
            "https://medfinder-9.preview.emergentagent.com/api/search/pbs",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Expected 200 OK, got {response.status_code}")
            return False
            
        data = response.json()
        
        # Check it's an array
        if not isinstance(data, list):
            print(f"❌ Expected JSON array, got {type(data)}")
            return False
            
        # Check length >= 1
        if len(data) < 1:
            print(f"❌ Expected array length >= 1, got {len(data)}")
            return False
            
        # Validate required keys in at least one object
        first_item = data[0]
        if "drug_name" not in first_item:
            print(f"❌ Expected 'drug_name' key in response objects")
            return False
            
        print("✅ PBS search endpoint test passed")
        print(f"   Found {len(data)} results")
        print(f"   First result keys: {list(first_item.keys())}")
        return True
        
    except Exception as e:
        print(f"❌ PBS search test failed: {e}")
        return False

def test_unified_search():
    """Test POST /api/search/unified as specified in review request"""
    print("\nTesting POST /api/search/unified...")
    try:
        payload = {"query": "aspirin", "search_type": "unified"}
        response = requests.post(
            "https://medfinder-9.preview.emergentagent.com/api/search/unified",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Expected 200 OK, got {response.status_code}")
            return False
            
        data = response.json()
        
        # Check it's an object
        if not isinstance(data, dict):
            print(f"❌ Expected JSON object, got {type(data)}")
            return False
            
        # Check required keys
        required_keys = ["query", "pbs_results", "web_results"]
        for key in required_keys:
            if key not in data:
                print(f"❌ Expected key '{key}' in response")
                return False
                
        # Check pbs_results is array
        if not isinstance(data["pbs_results"], list):
            print(f"❌ Expected pbs_results to be array, got {type(data['pbs_results'])}")
            return False
            
        # Check web_results is array  
        if not isinstance(data["web_results"], list):
            print(f"❌ Expected web_results to be array, got {type(data['web_results'])}")
            return False
            
        print("✅ Unified search endpoint test passed")
        print(f"   Query: {data['query']}")
        print(f"   PBS results: {len(data['pbs_results'])}")
        print(f"   Web results: {len(data['web_results'])}")
        return True
        
    except Exception as e:
        print(f"❌ Unified search test failed: {e}")
        return False

def test_search_history():
    """Test GET /api/search/history as specified in review request"""
    print("\nTesting GET /api/search/history...")
    try:
        response = requests.get("https://medfinder-9.preview.emergentagent.com/api/search/history", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Expected 200 OK, got {response.status_code}")
            return False
            
        data = response.json()
        
        # Check it's an array
        if not isinstance(data, list):
            print(f"❌ Expected JSON array, got {type(data)}")
            return False
            
        # Check length >= 1 (should have history from previous tests)
        if len(data) < 1:
            print(f"❌ Expected array length >= 1 after previous searches, got {len(data)}")
            return False
            
        # Validate each item contains query and search_type
        first_item = data[0]
        if "query" not in first_item:
            print(f"❌ Expected 'query' key in history items")
            return False
            
        if "search_type" not in first_item:
            print(f"❌ Expected 'search_type' key in history items")
            return False
            
        print("✅ Search history endpoint test passed")
        print(f"   Found {len(data)} history records")
        print(f"   Latest search: {first_item.get('query')} ({first_item.get('search_type')})")
        return True
        
    except Exception as e:
        print(f"❌ Search history test failed: {e}")
        return False

def main():
    """Run all review-specific tests"""
    print("🔍 Running Review-Specific Backend API Tests")
    print("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_pbs_search, 
        test_unified_search,
        test_search_history
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Review Tests Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All review requirements met!")
        return 0
    else:
        print("⚠️  Some review requirements not met.")
        return 1

if __name__ == "__main__":
    sys.exit(main())