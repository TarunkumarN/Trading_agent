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
    
    def test_portfolio_endpoint(self):
        """Test GET /api/portfolio returns initial_capital, current_equity, equity_curve, daily_pnl_chart, win_rate, profit_factor, max_drawdown"""
        success, response = self.make_request('GET', '/api/portfolio')
        
        if success:
            required_fields = ["initial_capital", "current_equity", "equity_curve", "daily_pnl_chart", "win_rate", "profit_factor", "max_drawdown"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.log_test("Portfolio endpoint", True, 
                             f"Portfolio: ₹{response.get('current_equity')}, Win Rate: {response.get('win_rate')}%")
            else:
                self.log_test("Portfolio endpoint", False, 
                             f"Missing portfolio fields: {missing_fields}", response)
        else:
            self.log_test("Portfolio endpoint", False, "Failed to fetch portfolio data", response)
    
    def test_open_positions_endpoint(self):
        """Test GET /api/open-positions returns positions array with strategy and unrealised_pnl"""
        success, response = self.make_request('GET', '/api/open-positions')
        
        if success and "positions" in response:
            positions = response.get("positions", [])
            self.log_test("Open positions endpoint", True, 
                         f"Found {len(positions)} open positions")
            
            if positions:
                pos = positions[0]
                required_fields = ["strategy", "unrealised_pnl"]
                missing_fields = [f for f in required_fields if f not in pos]
                if missing_fields:
                    self.log_test("Open positions structure", False, 
                                 f"Missing position fields: {missing_fields}", pos)
                else:
                    self.log_test("Open positions structure", True, "Position structure valid")
        else:
            self.log_test("Open positions endpoint", False, 
                         "Missing 'positions' in response", response)
    
    def test_trades_endpoint(self):
        """Test GET /api/trades returns trades grouped by_date with total count"""
        success, response = self.make_request('GET', '/api/trades')
        
        if success:
            trades = response.get("trades", [])
            by_date = response.get("by_date", [])
            total = response.get("total", 0)
            
            self.log_test("Trades endpoint", True, 
                         f"Found {len(trades)} trades, grouped by {len(by_date)} dates, total: {total}")
        else:
            self.log_test("Trades endpoint", False, "Failed to fetch trades data", response)
    
    def test_trade_detail_endpoint(self):
        """Test GET /api/trades/{symbol} returns trade detail with ai_validation, market_regime, prediction_probability"""
        # First try to get available trades
        trades_success, trades_response = self.make_request('GET', '/api/trades')
        if trades_success and trades_response.get("trades"):
            first_trade = trades_response["trades"][0]
            trade_symbol = first_trade['symbol']
            
            success, response = self.make_request('GET', f'/api/trades/{trade_symbol}')
            
            if success:
                required_fields = ["ai_validation", "market_regime", "prediction_probability"]
                missing_fields = [f for f in required_fields if f not in response]
                
                if not missing_fields:
                    self.log_test("Trade detail endpoint", True, 
                                 f"Trade detail for {trade_symbol}: Market regime: {response.get('market_regime')}, Confidence: {response.get('ai_validation', {}).get('confidence', 'N/A')}%")
                else:
                    self.log_test("Trade detail endpoint", False, 
                                 f"Missing trade detail fields: {missing_fields}", response)
            else:
                self.log_test("Trade detail endpoint", False, 
                             f"Failed to fetch trade detail for {trade_symbol}", response)
        else:
            self.log_test("Trade detail endpoint", False, "No trades available to test", trades_response)
    
    def test_strategies_performance_endpoint(self):
        """Test GET /api/strategies/performance returns 4 strategies with metrics"""
        success, response = self.make_request('GET', '/api/strategies/performance')
        
        if success and "strategies" in response:
            strategies = response.get("strategies", [])
            
            if len(strategies) >= 4:
                # Check first strategy has required metrics
                if strategies:
                    strat = strategies[0]
                    metrics = strat.get("metrics", {})
                    required_metrics = ["total_trades", "win_rate", "total_pnl", "avg_pnl", "max_drawdown"]
                    missing_metrics = [m for m in required_metrics if m not in metrics]
                    
                    if not missing_metrics:
                        self.log_test("Strategy performance endpoint", True, 
                                     f"Found {len(strategies)} strategies with complete metrics")
                    else:
                        self.log_test("Strategy performance endpoint", False, 
                                     f"Missing strategy metrics: {missing_metrics}", metrics)
                else:
                    self.log_test("Strategy performance endpoint", False, "No strategies found", response)
            else:
                self.log_test("Strategy performance endpoint", False, 
                             f"Expected 4+ strategies, found {len(strategies)}", response)
        else:
            self.log_test("Strategy performance endpoint", False, 
                         "Missing 'strategies' in response", response)
    
    def test_market_premarket_endpoint(self):
        """Test GET /api/market/premarket returns indices, gap_ups, gap_downs, volume_leaders, ai_recommendation"""
        success, response = self.make_request('GET', '/api/market/premarket')
        
        if success:
            required_fields = ["indices", "gap_ups", "gap_downs", "volume_leaders", "ai_recommendation"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                indices = response.get("indices", {})
                gap_ups = response.get("gap_ups", [])
                self.log_test("Market premarket endpoint", True, 
                             f"Premarket data: {len(indices)} indices, {len(gap_ups)} gap ups")
            else:
                self.log_test("Market premarket endpoint", False, 
                             f"Missing premarket fields: {missing_fields}", response)
        else:
            self.log_test("Market premarket endpoint", False, "Failed to fetch premarket data", response)
    
    def test_market_postmarket_endpoint(self):
        """Test GET /api/market/postmarket returns trading_summary, market_summary, best_performers, worst_performers"""
        success, response = self.make_request('GET', '/api/market/postmarket')
        
        if success:
            required_fields = ["trading_summary", "market_summary", "best_performers", "worst_performers"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                trading_summary = response.get("trading_summary", {})
                self.log_test("Market postmarket endpoint", True, 
                             f"Postmarket: {trading_summary.get('total_trades', 0)} trades today")
            else:
                self.log_test("Market postmarket endpoint", False, 
                             f"Missing postmarket fields: {missing_fields}", response)
        else:
            self.log_test("Market postmarket endpoint", False, "Failed to fetch postmarket data", response)
    
    def test_market_gainers_endpoint(self):
        """Test GET /api/market/gainers returns gainers array"""
        success, response = self.make_request('GET', '/api/market/gainers')
        
        if success and "gainers" in response:
            gainers = response.get("gainers", [])
            self.log_test("Market gainers endpoint", True, f"Found {len(gainers)} gainers")
        else:
            self.log_test("Market gainers endpoint", False, "Missing 'gainers' in response", response)
    
    def test_market_losers_endpoint(self):
        """Test GET /api/market/losers returns losers array"""
        success, response = self.make_request('GET', '/api/market/losers')
        
        if success and "losers" in response:
            losers = response.get("losers", [])
            self.log_test("Market losers endpoint", True, f"Found {len(losers)} losers")
        else:
            self.log_test("Market losers endpoint", False, "Missing 'losers' in response", response)
    
    def test_ai_decisions_endpoint(self):
        """Test GET /api/ai-decisions returns decisions with reasoning chain, confidence, ai_accuracy"""
        success, response = self.make_request('GET', '/api/ai-decisions')
        
        if success:
            required_fields = ["decisions", "ai_accuracy"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                decisions = response.get("decisions", [])
                ai_accuracy = response.get("ai_accuracy", 0)
                
                if decisions:
                    decision = decisions[0]
                    required_decision_fields = ["reasoning", "confidence"]
                    missing_decision_fields = [f for f in required_decision_fields if f not in decision]
                    
                    if not missing_decision_fields:
                        self.log_test("AI decisions endpoint", True, 
                                     f"Found {len(decisions)} decisions, AI accuracy: {ai_accuracy}%")
                    else:
                        self.log_test("AI decisions endpoint", False, 
                                     f"Missing decision fields: {missing_decision_fields}", decision)
                else:
                    self.log_test("AI decisions endpoint", True, 
                                 f"No decisions yet, AI accuracy: {ai_accuracy}%")
            else:
                self.log_test("AI decisions endpoint", False, 
                             f"Missing AI decisions fields: {missing_fields}", response)
        else:
            self.log_test("AI decisions endpoint", False, "Failed to fetch AI decisions", response)
    
    def test_analytics_summary_endpoint(self):
        """Test GET /api/analytics/summary returns hour_distribution, pnl_distribution"""
        success, response = self.make_request('GET', '/api/analytics/summary')
        
        if success:
            required_fields = ["hour_distribution", "pnl_distribution"]
            missing_fields = [f for f in required_fields if f not in response]
            
            if not missing_fields:
                self.log_test("Analytics summary endpoint", True, 
                             f"Analytics data with hour and PnL distributions")
            else:
                self.log_test("Analytics summary endpoint", False, 
                             f"Missing analytics fields: {missing_fields}", response)
        else:
            self.log_test("Analytics summary endpoint", False, "Failed to fetch analytics summary", response)
    
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
        
        # Test core endpoints
        print("\n📡 Testing Core API Endpoints...")
        self.test_health_endpoint()
        self.test_dashboard_data_endpoint()
        self.test_risk_endpoint()
        self.test_strategies_endpoint()
        self.test_logs_endpoint()
        self.test_audit_endpoint()
        self.test_config_endpoint()
        
        # Test portfolio endpoints
        print("\n💼 Testing Portfolio Endpoints...")
        self.test_portfolio_endpoint()
        self.test_open_positions_endpoint()
        
        # Test trading endpoints
        print("\n📈 Testing Trading Endpoints...")
        self.test_trades_endpoint()
        self.test_trade_detail_endpoint()
        self.test_strategies_performance_endpoint()
        
        # Test market data endpoints
        print("\n📊 Testing Market Data Endpoints...")
        self.test_market_premarket_endpoint()
        self.test_market_postmarket_endpoint()
        self.test_market_gainers_endpoint()
        self.test_market_losers_endpoint()
        
        # Test AI and analytics endpoints
        print("\n🤖 Testing AI & Analytics Endpoints...")
        self.test_ai_decisions_endpoint()
        self.test_analytics_summary_endpoint()
        
        # Test utility endpoints
        print("\n🔧 Testing Utility Endpoints...")
        self.test_fo_calculate_endpoint()
        
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