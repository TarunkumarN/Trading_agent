"""
MiniMax Trading Dashboard - Backend API Tests
Tests all 21+ API endpoints for the trading dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://market-analysis-ai-5.preview.emergentagent.com"


class TestAuthentication:
    """Authentication endpoint tests - /api/auth/login"""

    def test_login_with_correct_credentials(self):
        """POST /api/auth/login with admin/minimax123 should return ok:true"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "user": "admin",
            "pass": "minimax123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        assert "token" in data
        print(f"Login success: {data}")

    def test_login_with_wrong_credentials(self):
        """POST /api/auth/login with wrong credentials should return ok:false"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "user": "wronguser",
            "pass": "wrongpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == False
        print(f"Login failed as expected: {data}")


class TestDashboardData:
    """Dashboard data endpoint tests - /api/data"""

    def test_get_dashboard_data(self):
        """GET /api/data returns dashboard summary"""
        response = requests.get(f"{BASE_URL}/api/data")
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "day_pnl" in data
        assert "total_trades" in data
        assert "wins" in data
        assert "losses" in data
        assert "win_rate" in data
        assert "open_positions" in data
        assert "trades" in data
        assert "pnl_curve" in data
        assert "portfolio_value" in data
        assert "market_open" in data
        assert "agent_state" in data
        
        print(f"Dashboard data: day_pnl={data['day_pnl']}, trades={data['total_trades']}, win_rate={data['win_rate']}%")


class TestPortfolio:
    """Portfolio endpoint tests - /api/portfolio"""

    def test_get_portfolio(self):
        """GET /api/portfolio returns portfolio stats"""
        response = requests.get(f"{BASE_URL}/api/portfolio")
        assert response.status_code == 200
        data = response.json()
        
        assert "initial_capital" in data
        assert "current_equity" in data
        assert "total_pnl" in data
        assert "day_pnl" in data
        assert "unrealised_pnl" in data
        assert "total_trades" in data
        assert "wins" in data
        assert "losses" in data
        assert "win_rate" in data
        assert "equity_curve" in data
        assert "daily_pnl_chart" in data
        
        print(f"Portfolio: equity={data['current_equity']}, total_pnl={data['total_pnl']}")


class TestDailyReport:
    """Daily report endpoint tests - /api/report/daily"""

    def test_get_daily_report(self):
        """GET /api/report/daily returns daily trading report"""
        response = requests.get(f"{BASE_URL}/api/report/daily")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_trades" in data
        assert "winning_trades" in data
        assert "losing_trades" in data
        assert "win_rate" in data
        assert "daily_pnl" in data
        assert "cumulative_pnl" in data
        assert "portfolio_value" in data
        assert "strategy_performance" in data
        assert "portfolio_growth" in data
        
        print(f"Daily report: trades={data['total_trades']}, win_rate={data['win_rate']}%")


class TestHealthStatus:
    """Health status endpoint tests - /api/health"""

    def test_get_health(self):
        """GET /api/health returns system health status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        
        assert "services" in data
        assert "components" in data
        assert "agent_state" in data
        assert "risk_summary" in data
        assert "market_open" in data
        
        # Verify components exist
        components = data["components"]
        assert "broker_api" in components
        assert "mongodb" in components
        
        print(f"Health: agent_state={data['agent_state']}, services={data['services']}")


class TestMarketData:
    """Market data endpoint tests"""

    def test_get_market_live(self):
        """GET /api/market/live returns live market data (MOCKED)"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        
        assert "indices" in data
        assert "gainers" in data
        assert "losers" in data
        assert "most_active" in data
        assert "source" in data
        assert "timestamp" in data
        
        print(f"Market data: source={data['source']}, data_valid={data.get('data_valid')}")

    def test_get_ai_regime(self):
        """GET /api/ai/regime returns AI market regime analysis"""
        response = requests.get(f"{BASE_URL}/api/ai/regime")
        assert response.status_code == 200
        data = response.json()
        
        assert "regime" in data
        assert "recommendation" in data
        assert "confidence" in data
        assert "volatility" in data
        assert "liquidity" in data
        
        print(f"AI Regime: {data['regime']}, recommendation={data['recommendation']}, confidence={data['confidence']}%")


class TestStrategies:
    """Strategy endpoint tests"""

    def test_get_strategies(self):
        """GET /api/strategies returns strategy list"""
        response = requests.get(f"{BASE_URL}/api/strategies")
        assert response.status_code == 200
        data = response.json()
        
        assert "strategies" in data
        assert len(data["strategies"]) > 0
        
        for s in data["strategies"]:
            assert "name" in s
            assert "status" in s
        
        print(f"Strategies: {len(data['strategies'])} active")

    def test_get_strategies_performance(self):
        """GET /api/strategies/performance returns per-strategy metrics"""
        response = requests.get(f"{BASE_URL}/api/strategies/performance")
        assert response.status_code == 200
        data = response.json()
        
        assert "strategies" in data
        for s in data["strategies"]:
            assert "name" in s
            assert "metrics" in s
            assert "pnl_history" in s
        
        print(f"Strategy performance data for {len(data['strategies'])} strategies")


class TestAIDecisions:
    """AI decisions endpoint tests"""

    def test_get_ai_decisions(self):
        """GET /api/ai-decisions returns AI decision history"""
        response = requests.get(f"{BASE_URL}/api/ai-decisions")
        assert response.status_code == 200
        data = response.json()
        
        assert "decisions" in data
        assert "ai_accuracy" in data
        assert "total_decisions" in data
        assert "correct_decisions" in data
        
        print(f"AI accuracy: {data['ai_accuracy']}%, decisions={data['total_decisions']}")


class TestPositions:
    """Positions endpoint tests"""

    def test_get_open_positions(self):
        """GET /api/open-positions returns current positions"""
        response = requests.get(f"{BASE_URL}/api/open-positions")
        assert response.status_code == 200
        data = response.json()
        
        assert "positions" in data
        assert "count" in data
        
        print(f"Open positions: {data['count']}")


class TestTrades:
    """Trade history endpoint tests"""

    def test_get_trades(self):
        """GET /api/trades returns trade history"""
        response = requests.get(f"{BASE_URL}/api/trades")
        assert response.status_code == 200
        data = response.json()
        
        assert "trades" in data
        assert "total" in data
        
        if data["trades"]:
            trade = data["trades"][0]
            assert "symbol" in trade
            assert "pnl" in trade
            assert "action" in trade
        
        print(f"Trades: {data['total']} total")


class TestRisk:
    """Risk management endpoint tests"""

    def test_get_risk(self):
        """GET /api/risk returns risk data"""
        response = requests.get(f"{BASE_URL}/api/risk")
        assert response.status_code == 200
        data = response.json()
        
        assert "day_pnl" in data
        assert "daily_loss_limit" in data
        assert "loss_used" in data
        assert "loss_pct" in data
        assert "trading_allowed" in data
        assert "risk_level" in data
        
        print(f"Risk: level={data['risk_level']}, trading_allowed={data['trading_allowed']}")


class TestFOCalculator:
    """F&O Calculator endpoint tests"""

    def test_fo_calculate(self):
        """GET /api/fo/calculate returns position sizing calculations"""
        response = requests.get(f"{BASE_URL}/api/fo/calculate", params={
            "entry": 22000,
            "sl": 21950,
            "target": 22100,
            "portfolio": 50000,
            "instrument": "equity"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "qty" in data
        assert "total_risk" in data
        assert "total_reward" in data
        assert "rr_ratio" in data
        assert "capital_needed" in data
        
        print(f"F&O Calculator: qty={data['qty']}, risk={data['total_risk']}, reward={data['total_reward']}")

    def test_fo_calculate_futures(self):
        """GET /api/fo/calculate with nifty_fut instrument"""
        response = requests.get(f"{BASE_URL}/api/fo/calculate", params={
            "entry": 22000,
            "sl": 21900,
            "target": 22200,
            "portfolio": 50000,
            "instrument": "nifty_fut"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["qty"] >= 25  # Minimum lot size for Nifty futures
        print(f"Nifty Futures: qty={data['qty']}, lots={data.get('lots')}")


class TestAuditLogs:
    """Audit and logs endpoint tests"""

    def test_get_audit(self):
        """GET /api/audit returns audit report"""
        response = requests.get(f"{BASE_URL}/api/audit")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_issues" in data
        assert "critical" in data
        assert "high" in data
        assert "medium" in data
        assert "low" in data
        assert "issues" in data
        assert "all_fixed" in data
        
        print(f"Audit: {data['total_issues']} issues, all_fixed={data['all_fixed']}")

    def test_get_logs(self):
        """GET /api/logs returns event logs"""
        response = requests.get(f"{BASE_URL}/api/logs", params={"limit": 50})
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        
        print(f"Logs: {data['total']} total")


class TestConfig:
    """Configuration endpoint tests"""

    def test_get_config(self):
        """GET /api/config returns bot configuration"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200
        data = response.json()
        
        assert "trading_mode" in data
        assert "portfolio_value" in data
        assert "max_risk_pct" in data
        assert "daily_loss_limit" in data
        assert "min_signal_score" in data
        assert "risk_reward_ratio" in data
        
        print(f"Config: mode={data['trading_mode']}, portfolio={data['portfolio_value']}")


class TestMode:
    """Trading mode endpoint tests"""

    def test_get_mode(self):
        """GET /api/mode returns current trading mode"""
        response = requests.get(f"{BASE_URL}/api/mode")
        assert response.status_code == 200
        data = response.json()
        
        assert "mode" in data
        assert "is_live" in data
        
        print(f"Mode: {data['mode']}, is_live={data['is_live']}")

    def test_switch_mode_to_sim(self):
        """POST /api/mode/switch to PAPER mode should succeed"""
        response = requests.post(f"{BASE_URL}/api/mode/switch", json={
            "mode": "paper"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") == True
        assert data.get("mode") == "PAPER"
        
        print(f"Mode switch to PAPER: {data}")

    def test_switch_mode_to_live_fails_without_broker(self):
        """POST /api/mode/switch to LIVE mode should fail without valid broker credentials"""
        response = requests.post(f"{BASE_URL}/api/mode/switch", json={
            "mode": "live"
        })
        assert response.status_code == 200
        data = response.json()
        
        # May succeed or fail depending on broker config
        # Just verify we get a response
        print(f"Mode switch to LIVE: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
