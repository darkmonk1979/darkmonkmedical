import requests
import sys
import json
from datetime import datetime

class MedicalSearchAPITester:
    def __init__(self, base_url="https://medfinder-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_health_check(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, f"API is healthy: {data}")
                    return True
                else:
                    self.log_test("Health Check", False, f"API status not healthy: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_pbs_search(self, medication="Paracetamol"):
        """Test PBS search endpoint"""
        try:
            payload = {
                "query": medication,
                "search_type": "pbs"
            }
            
            response = requests.post(
                f"{self.api_url}/search/pbs", 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test(f"PBS Search ({medication})", True, f"Found {len(data)} results")
                    return True, data
                else:
                    self.log_test(f"PBS Search ({medication})", False, f"Invalid response format: {type(data)}")
                    return False, []
            else:
                self.log_test(f"PBS Search ({medication})", False, f"Status code: {response.status_code}, Response: {response.text}")
                return False, []
                
        except Exception as e:
            self.log_test(f"PBS Search ({medication})", False, f"Exception: {str(e)}")
            return False, []

    def test_google_search_info(self):
        """Test Google search info endpoint"""
        try:
            response = requests.get(f"{self.api_url}/search/google-info", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "cse_id" in data and "covered_sites" in data:
                    self.log_test("Google Search Info", True, f"CSE ID: {data.get('cse_id')}, Sites: {len(data.get('covered_sites', []))}")
                    return True, data
                else:
                    self.log_test("Google Search Info", False, f"Invalid response format: {data}")
                    return False, {}
            else:
                self.log_test("Google Search Info", False, f"Status code: {response.status_code}, Response: {response.text}")
                return False, {}
                
        except Exception as e:
            self.log_test("Google Search Info", False, f"Exception: {str(e)}")
            return False, {}

    def test_unified_search(self, medication="Insulin"):
        """Test unified search endpoint"""
        try:
            payload = {
                "query": medication,
                "search_type": "unified"
            }
            
            response = requests.post(
                f"{self.api_url}/search/unified", 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "pbs_results" in data and "web_results" in data:
                    pbs_count = len(data.get("pbs_results", []))
                    web_count = len(data.get("web_results", []))
                    self.log_test(f"Unified Search ({medication})", True, 
                                f"PBS: {pbs_count} results, Web: {web_count} results")
                    return True, data
                else:
                    self.log_test(f"Unified Search ({medication})", False, f"Invalid response format: {data}")
                    return False, {}
            else:
                self.log_test(f"Unified Search ({medication})", False, f"Status code: {response.status_code}, Response: {response.text}")
                return False, {}
                
        except Exception as e:
            self.log_test(f"Unified Search ({medication})", False, f"Exception: {str(e)}")
            return False, {}

    def test_search_history(self):
        """Test search history endpoint"""
        try:
            response = requests.get(f"{self.api_url}/search/history", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Search History", True, f"Retrieved {len(data)} search records")
                    return True, data
                else:
                    self.log_test("Search History", False, f"Invalid response format: {type(data)}")
                    return False, []
            else:
                self.log_test("Search History", False, f"Status code: {response.status_code}")
                return False, []
                
        except Exception as e:
            self.log_test("Search History", False, f"Exception: {str(e)}")
            return False, []

    def test_invalid_search(self):
        """Test error handling with invalid search"""
        try:
            payload = {
                "query": "",  # Empty query
                "search_type": "pbs"
            }
            
            response = requests.post(
                f"{self.api_url}/search/pbs", 
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            # Should handle empty query gracefully
            if response.status_code in [200, 400, 422]:
                self.log_test("Invalid Search Handling", True, f"Handled empty query appropriately: {response.status_code}")
                return True
            else:
                self.log_test("Invalid Search Handling", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invalid Search Handling", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🔍 Starting Australian Medical Search API Tests")
        print(f"📍 Testing endpoint: {self.base_url}")
        print("=" * 60)
        
        # Test health check first
        if not self.test_health_check():
            print("❌ API health check failed - stopping tests")
            return False
        
        # Test all search endpoints
        medications_to_test = ["Paracetamol", "Aspirin", "Insulin"]
        
        for med in medications_to_test:
            self.test_pbs_search(med)
            self.test_unified_search(med)
        
        # Test Google search info endpoint
        self.test_google_search_info()
        
        # Test search history
        self.test_search_history()
        
        # Test error handling
        self.test_invalid_search()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
            return False

def main():
    tester = MedicalSearchAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())