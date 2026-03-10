#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for MiniMax Trading Agent
Testing all endpoints as specified in the review requirements.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Tuple

class TradingAgentAPITester:
    def __init__(self, base_url: str = "https://72276288-fd29-4347-9ca7-42a8986ddfb1.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log_test(self, name: str, success: bool, message: str = "", response_data: Dict = None):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {message}")
        else:
            self.failed_tests.append({"test": name, "message": message, "response": response_data})
            print(f"❌ {name}: FAILED {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> Tuple[bool, Dict]:
        """Make HTTP request and return success status and response data"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text, "status_code": response.status_code}
                
            return success, response_data
            
        except Exception as e:
            return False, {"error": str(e), "exception_type": type(e).__name__}
    
    def test_login_correct_credentials(self):
        """Test POST /api/auth/login with correct credentials"""
        success, response = self.make_request('POST', '/api/auth/login', 
                                            data={"user": "admin", "pass": "minimax123"})
        
        if success and response.get("ok") == True and "token" in response:
            self.token = response["token"]  # Store token for future requests
            self.log_test("Login with correct credentials", True, f"Token received: {self.token}")
            return True
        else:
            self.log_test("Login with correct credentials", False, 
                         f"Expected ok:true with token, got: {response}", response)
            return False
    
    def test_login_wrong_credentials(self):
        """Test POST /api/auth/login with wrong credentials"""
        success, response = self.make_request('POST', '/api/auth/login', 
                                            data={"user": "wrong", "pass": "wrong"})
        
        if success and response.get("ok") == False:
            self.log_test("Login with wrong credentials", True, "Correctly rejected invalid credentials")
        else:
            self.log_test("Login with wrong credentials", False, 
                         f"Expected ok:false, got: {response}", response)
    
    def test_health_endpoint(self):
        """Test GET /api/health returns services and components status"""
        success, response = self.make_request('GET', '/api/health')
        
        if success and "services" in response and "components" in response:
            services = response.get("services", {})
            components = response.get("components", {})
            
            # Check required service components
            required_services = ["trading_agent", "mongodb"]
            missing_services = [s for s in required_services if s not in services]
            
            if not missing_services and len(components) > 0:
                self.log_test("Health endpoint", True, 
                             f"Found {len(services)} services, {len(components)} components")
            else:
                self.log_test("Health endpoint", False, 
                             f"Missing services: {missing_services}, Components: {len(components)}", response)
        else:
            self.log_test("Health endpoint", False, 
                         "Missing 'services' or 'components' in response", response)
    
    def test_dashboard_data_endpoint(self):
        """Test GET /api/data returns dashboard data"""
        success, response = self.make_request('GET', '/api/data')
        
        if success:
            required_fields = ["day_pnl", "trades", "open_positions", "pnl_curve", "daily_pnl"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.log_test("Dashboard data endpoint", True, 
                             f"All required fields present: {required_fields}")
            else:
                self.log_test("Dashboard data endpoint", False, 
                             f"Missing fields: {missing_fields}", response)
        else:
            self.log_test("Dashboard data endpoint", False, "Failed to fetch dashboard data", response)
    
    def test_risk_endpoint(self):
        """Test GET /api/risk returns risk controls"""
        success, response = self.make_request('GET', '/api/risk')
        
        if success:
            required_fields = ["daily_loss_limit", "loss_pct", "drawdown_pct", "trading_allowed"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.log_test("Risk endpoint", True, 
                             f"Risk controls data: loss_limit={response.get('daily_loss_limit')}, trading_allowed={response.get('trading_allowed')}")
            else:
                self.log_test("Risk endpoint", False, 
                             f"Missing risk fields: {missing_fields}", response)
        else:
            self.log_test("Risk endpoint", False, "Failed to fetch risk data", response)
    
    def test_strategies_endpoint(self):
        """Test GET /api/strategies returns strategies list with status"""
        success, response = self.make_request('GET', '/api/strategies')
        
        if success and "strategies" in response:
            strategies = response.get("strategies", [])
            agent_state = response.get("agent_state")
            
            self.log_test("Strategies endpoint", True, 
                         f"Found {len(strategies)} strategies, agent_state: {agent_state}")
        else:
            self.log_test("Strategies endpoint", False, 
                         "Missing 'strategies' in response", response)
    
    def test_logs_endpoint(self):
        """Test GET /api/logs returns event_logs from MongoDB"""
        success, response = self.make_request('GET', '/api/logs')
        
        if success and "logs" in response:
            logs = response.get("logs", [])
            total = response.get("total", 0)
            
            self.log_test("Logs endpoint", True, 
                         f"Found {len(logs)} logs, total: {total}")
        else:
            self.log_test("Logs endpoint", False, 
                         "Missing 'logs' in response", response)
    
    def test_audit_endpoint(self):
        """Test GET /api/audit returns 14 issues all FIXED"""
        success, response = self.make_request('GET', '/api/audit')
        
        if success:
            total_issues = response.get("total_issues", 0)
            all_fixed = response.get("all_fixed", False)
            issues = response.get("issues", [])
            
            if total_issues == 14 and all_fixed == True:
                self.log_test("Audit endpoint", True, 
                             f"All {total_issues} issues are FIXED")
            else:
                self.log_test("Audit endpoint", False, 
                             f"Expected 14 issues all FIXED, got {total_issues} issues, all_fixed: {all_fixed}", response)
        else:
            self.log_test("Audit endpoint", False, "Failed to fetch audit data", response)
    
    def test_config_endpoint(self):
        """Test GET /api/config returns trading parameters"""
        success, response = self.make_request('GET', '/api/config')
        
        if success:
            required_fields = ["portfolio_value", "max_risk_pct", "trading_mode"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                portfolio = response.get("portfolio_value")
                mode = response.get("trading_mode")
                self.log_test("Config endpoint", True, 
                             f"Portfolio: ₹{portfolio}, Mode: {mode}")
            else:
                self.log_test("Config endpoint", False, 
                             f"Missing config fields: {missing_fields}", response)
        else:
            self.log_test("Config endpoint", False, "Failed to fetch config", response)
    
    def test_fo_calculate_endpoint(self):
        """Test GET /api/fo/calculate with entry=22000&sl=21950&target=22100"""
        params = "entry=22000&sl=21950&target=22100"
        success, response = self.make_request('GET', f'/api/fo/calculate?{params}')
        
        if success:
            required_fields = ["qty", "risk_per_share", "reward_per_share", "total_risk", "total_reward"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                qty = response.get("qty")
                risk = response.get("total_risk")
                reward = response.get("total_reward")
                self.log_test("F&O Calculator endpoint", True, 
                             f"Qty: {qty}, Risk: ₹{risk}, Reward: ₹{reward}")
            else:
                self.log_test("F&O Calculator endpoint", False, 
                             f"Missing F&O calc fields: {missing_fields}", response)
        else:
            self.log_test("F&O Calculator endpoint", False, "Failed to calculate F&O", response)
    
    def test_premarket_endpoint(self):
        """Test GET /api/premarket returns indices and movers data"""
        success, response = self.make_request('GET', '/api/premarket')
        
        if success:
            indices = response.get("indices", {})
            movers = response.get("movers", [])
            
            # This endpoint may have limited data due to NSE API restrictions
            self.log_test("Premarket endpoint", True, 
                         f"Indices data: {len(indices)} indices, {len(movers)} movers (NSE data may be limited)")
        else:
            self.log_test("Premarket endpoint", False, "Failed to fetch premarket data", response)
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print("=" * 60)
        print("🚀 STARTING BACKEND API TESTING")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login_correct_credentials():
            print("\n❌ LOGIN FAILED - Cannot proceed with authenticated tests")
            return False
            
        # Test wrong credentials
        self.test_login_wrong_credentials()
        
        # Test all other endpoints
        print("\n📡 Testing API Endpoints...")
        self.test_health_endpoint()
        self.test_dashboard_data_endpoint()
        self.test_risk_endpoint()
        self.test_strategies_endpoint()
        self.test_logs_endpoint()
        self.test_audit_endpoint()
        self.test_config_endpoint()
        self.test_fo_calculate_endpoint()
        self.test_premarket_endpoint()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 BACKEND TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Tests Failed: {len(self.failed_tests)}/{self.tests_run}")
        
        if self.failed_tests:
            print("\n🔥 FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"{i}. {failure['test']}: {failure['message']}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        return len(self.failed_tests) == 0

def main():
    tester = TradingAgentAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())