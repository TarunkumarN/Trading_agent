"""
MiniMax Trading Dashboard - Quant Intelligence Module Tests
=============================================================
Tests all new quant intelligence API endpoints:
- Pipeline Analysis
- Options Flow Analysis
- Dark Pool Detection
- AI Market Prediction
- Correlation Filter
- Trade Ranking
- Hedge Analysis
- Frequency Status
- Quant Dashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://market-analysis-ai-5.preview.emergentagent.com"

# Test symbols
SYMBOLS = ["RELIANCE", "HDFCBANK", "TCS", "ICICIBANK", "INFY"]


class TestQuantPipeline:
    """Pipeline analysis endpoint tests - /api/quant/pipeline/{symbol}"""

    def test_pipeline_reliance(self):
        """GET /api/quant/pipeline/RELIANCE returns pipeline analysis with steps array"""
        response = requests.get(f"{BASE_URL}/api/quant/pipeline/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        
        # Core pipeline structure
        assert "pipeline_result" in data
        assert data["pipeline_result"] in ["PASS", "FAIL", "SKIP"]
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert "steps_passed" in data
        assert "steps_total" in data
        assert "reason" in data
        assert "trade_score" in data
        assert "timestamp" in data
        assert "symbol" in data
        assert data["symbol"] == "RELIANCE"
        
        # Entry/exit levels
        assert "entry" in data
        assert "stop_loss" in data
        assert "target" in data
        assert "action" in data
        assert data["action"] in ["BUY", "SELL", "HOLD"]
        assert "risk_reward_ratio" in data
        
        print(f"Pipeline RELIANCE: result={data['pipeline_result']}, action={data['action']}, score={data['trade_score']}")

    def test_pipeline_hdfcbank(self):
        """GET /api/quant/pipeline/HDFCBANK returns pipeline result"""
        response = requests.get(f"{BASE_URL}/api/quant/pipeline/HDFCBANK")
        assert response.status_code == 200
        data = response.json()
        
        assert "pipeline_result" in data
        assert "steps" in data
        assert "symbol" in data
        assert data["symbol"] == "HDFCBANK"
        
        print(f"Pipeline HDFCBANK: result={data['pipeline_result']}, steps={data['steps_passed']}/{data['steps_total']}")

    def test_pipeline_all_symbols(self):
        """GET /api/quant/pipeline/{symbol} works for all watchlist symbols"""
        for symbol in SYMBOLS:
            response = requests.get(f"{BASE_URL}/api/quant/pipeline/{symbol}")
            assert response.status_code == 200
            data = response.json()
            assert "pipeline_result" in data
            assert data["symbol"] == symbol
            print(f"Pipeline {symbol}: {data['pipeline_result']}")


class TestOptionsFlow:
    """Options flow analysis endpoint tests - /api/quant/options-flow/{symbol}"""

    def test_options_flow_reliance(self):
        """GET /api/quant/options-flow/RELIANCE returns signal, strength, details"""
        response = requests.get(f"{BASE_URL}/api/quant/options-flow/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "signal" in data
        assert data["signal"] in ["bullish_flow", "bearish_flow", "neutral"]
        assert "strength" in data
        assert isinstance(data["strength"], int)
        assert 0 <= data["strength"] <= 100
        assert "details" in data
        assert "unusual_activity" in data
        assert isinstance(data["unusual_activity"], bool)
        assert "symbol" in data
        assert data["symbol"] == "RELIANCE"
        assert "timestamp" in data
        
        # Additional metrics
        assert "volume_ratio" in data
        assert "volume_zscore" in data
        assert "price_momentum_1" in data
        assert "price_momentum_5" in data
        
        print(f"Options Flow RELIANCE: signal={data['signal']}, strength={data['strength']}")

    def test_options_flow_tcs(self):
        """GET /api/quant/options-flow/TCS returns valid options flow data"""
        response = requests.get(f"{BASE_URL}/api/quant/options-flow/TCS")
        assert response.status_code == 200
        data = response.json()
        
        assert "signal" in data
        assert "strength" in data
        assert data["symbol"] == "TCS"
        
        print(f"Options Flow TCS: signal={data['signal']}, strength={data['strength']}, block_trade={data.get('block_trade')}")


class TestDarkPool:
    """Dark pool detection endpoint tests - /api/quant/dark-pool/{symbol}"""

    def test_dark_pool_reliance(self):
        """GET /api/quant/dark-pool/RELIANCE returns zone_price, zone_type, confidence"""
        response = requests.get(f"{BASE_URL}/api/quant/dark-pool/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "zone_price" in data
        assert "zone_type" in data
        assert data["zone_type"] in ["accumulation", "distribution", "none"]
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert "zones" in data
        assert isinstance(data["zones"], list)
        assert "total_zones_detected" in data
        assert "institutional_activity" in data
        assert isinstance(data["institutional_activity"], bool)
        assert "vwap" in data
        assert "symbol" in data
        assert data["symbol"] == "RELIANCE"
        assert "timestamp" in data
        
        print(f"Dark Pool RELIANCE: type={data['zone_type']}, confidence={data['confidence']}%, zones={data['total_zones_detected']}")

    def test_dark_pool_icicibank(self):
        """GET /api/quant/dark-pool/ICICIBANK returns dark pool zones"""
        response = requests.get(f"{BASE_URL}/api/quant/dark-pool/ICICIBANK")
        assert response.status_code == 200
        data = response.json()
        
        assert "zone_type" in data
        assert "institutional_activity" in data
        assert data["symbol"] == "ICICIBANK"
        
        print(f"Dark Pool ICICIBANK: institutional={data['institutional_activity']}")


class TestAIPrediction:
    """AI prediction endpoint tests - /api/quant/ai-prediction/{symbol}"""

    def test_ai_prediction_hdfcbank(self):
        """GET /api/quant/ai-prediction/HDFCBANK returns predicted_direction, confidence, trade_allowed"""
        response = requests.get(f"{BASE_URL}/api/quant/ai-prediction/HDFCBANK")
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "predicted_direction" in data
        assert data["predicted_direction"] in ["bullish", "bearish", "neutral"]
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0 <= data["confidence"] <= 100
        assert "trade_allowed" in data
        assert isinstance(data["trade_allowed"], bool)
        assert "factors" in data
        assert isinstance(data["factors"], dict)
        assert "timestamp" in data
        
        # Score breakdown
        assert "bullish_score" in data
        assert "bearish_score" in data
        assert "net_score" in data
        
        print(f"AI Prediction HDFCBANK: direction={data['predicted_direction']}, confidence={data['confidence']}%, trade_allowed={data['trade_allowed']}")

    def test_ai_prediction_infy(self):
        """GET /api/quant/ai-prediction/INFY returns valid prediction with factors"""
        response = requests.get(f"{BASE_URL}/api/quant/ai-prediction/INFY")
        assert response.status_code == 200
        data = response.json()
        
        assert "predicted_direction" in data
        assert "factors" in data
        
        # Verify factor structure
        factors = data["factors"]
        expected_factors = ["ema_trend", "rsi", "vwap", "momentum"]
        for factor in expected_factors:
            if factor in factors:
                assert "weight" in factors[factor]
        
        print(f"AI Prediction INFY: direction={data['predicted_direction']}, factors={len(factors)}")


class TestCorrelation:
    """Correlation filter endpoint tests - /api/quant/correlation/{symbol}"""

    def test_correlation_reliance_buy(self):
        """GET /api/quant/correlation/RELIANCE?action=BUY returns correlation_strength, confirmation"""
        response = requests.get(f"{BASE_URL}/api/quant/correlation/RELIANCE", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "correlation_strength" in data
        assert isinstance(data["correlation_strength"], (int, float))
        assert 0 <= data["correlation_strength"] <= 100
        assert "confirmation" in data
        assert isinstance(data["confirmation"], bool)
        assert "pairs_checked" in data
        assert "pairs_confirmed" in data
        assert "details" in data
        assert "symbol" in data
        assert data["symbol"] == "RELIANCE"
        assert "action" in data
        assert data["action"] == "BUY"
        assert "timestamp" in data
        
        print(f"Correlation RELIANCE BUY: strength={data['correlation_strength']}, confirmed={data['pairs_confirmed']}/{data['pairs_checked']}")

    def test_correlation_hdfcbank_sell(self):
        """GET /api/quant/correlation/HDFCBANK?action=SELL returns correlation data"""
        response = requests.get(f"{BASE_URL}/api/quant/correlation/HDFCBANK", params={"action": "SELL"})
        assert response.status_code == 200
        data = response.json()
        
        assert "correlation_strength" in data
        assert "confirmation" in data
        assert data["symbol"] == "HDFCBANK"
        assert data["action"] == "SELL"
        
        print(f"Correlation HDFCBANK SELL: strength={data['correlation_strength']}, confirmation={data['confirmation']}")


class TestTradeRank:
    """Trade ranking endpoint tests - /api/quant/trade-rank/{symbol}"""

    def test_trade_rank_reliance(self):
        """GET /api/quant/trade-rank/RELIANCE returns total_score, components, trade_allowed"""
        response = requests.get(f"{BASE_URL}/api/quant/trade-rank/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "total_score" in data
        assert isinstance(data["total_score"], (int, float))
        assert 0 <= data["total_score"] <= 100
        assert "max_score" in data
        assert data["max_score"] == 100
        assert "components" in data
        assert isinstance(data["components"], dict)
        assert "trade_allowed" in data
        assert isinstance(data["trade_allowed"], bool)
        assert "min_required" in data
        assert "action" in data
        assert "reasoning" in data
        assert isinstance(data["reasoning"], list)
        assert "grade" in data
        assert data["grade"] in ["A+", "A", "B+", "B", "C", "D"]
        assert "timestamp" in data
        
        print(f"Trade Rank RELIANCE: score={data['total_score']}/100, grade={data['grade']}, allowed={data['trade_allowed']}")

    def test_trade_rank_tcs_has_six_components(self):
        """GET /api/quant/trade-rank/TCS returns rank with 6 components"""
        response = requests.get(f"{BASE_URL}/api/quant/trade-rank/TCS")
        assert response.status_code == 200
        data = response.json()
        
        assert "components" in data
        components = data["components"]
        
        # Verify all 6 components exist
        expected_components = [
            "trend_strength",
            "dark_pool_alignment", 
            "order_block_strength",
            "options_flow_alignment",
            "gamma_level_alignment",
            "ai_prediction"
        ]
        for comp in expected_components:
            assert comp in components, f"Missing component: {comp}"
            assert isinstance(components[comp], (int, float))
        
        assert len(components) == 6
        
        print(f"Trade Rank TCS: score={data['total_score']}, components={list(components.keys())}")


class TestHedgeAnalysis:
    """Hedge analysis endpoint tests - /api/quant/hedge-analysis"""

    def test_hedge_analysis(self):
        """GET /api/quant/hedge-analysis returns exposure data with hedge_needed boolean"""
        response = requests.get(f"{BASE_URL}/api/quant/hedge-analysis")
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "bullish_exposure_pct" in data
        assert isinstance(data["bullish_exposure_pct"], (int, float))
        assert "bearish_exposure_pct" in data
        assert isinstance(data["bearish_exposure_pct"], (int, float))
        assert "net_exposure" in data
        assert data["net_exposure"] in ["FLAT", "BALANCED", "LONG BIASED", "SHORT BIASED", "HEAVY LONG", "HEAVY SHORT"]
        assert "hedge_needed" in data
        assert isinstance(data["hedge_needed"], bool)
        assert "positions_analysis" in data
        assert isinstance(data["positions_analysis"], list)
        assert "timestamp" in data
        
        # hedge_recommendation can be null or object
        assert "hedge_recommendation" in data
        
        print(f"Hedge Analysis: exposure={data['net_exposure']}, hedge_needed={data['hedge_needed']}")


class TestFrequencyStatus:
    """Frequency status endpoint tests - /api/quant/frequency-status"""

    def test_frequency_status(self):
        """GET /api/quant/frequency-status returns trades_today, consecutive_losses, trading_allowed"""
        response = requests.get(f"{BASE_URL}/api/quant/frequency-status")
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert "trades_today" in data
        assert isinstance(data["trades_today"], int)
        assert "max_trades_per_day" in data
        assert data["max_trades_per_day"] == 4
        assert "consecutive_losses" in data
        assert isinstance(data["consecutive_losses"], int)
        assert "max_consecutive_losses" in data
        assert data["max_consecutive_losses"] == 3
        assert "daily_pnl" in data
        assert "daily_drawdown_pct" in data
        assert "daily_drawdown_limit_pct" in data
        assert data["daily_drawdown_limit_pct"] == 4.0
        assert "trading_allowed" in data
        assert isinstance(data["trading_allowed"], bool)
        assert "reason" in data
        assert "quant_trading_hours" in data
        assert isinstance(data["quant_trading_hours"], bool)
        assert "trading_window" in data
        assert "09:30" in data["trading_window"] or "9:30" in data["trading_window"]
        assert "14:45" in data["trading_window"]
        assert "min_rr_ratio" in data
        assert data["min_rr_ratio"] == 2.0
        assert "timestamp" in data
        
        print(f"Frequency Status: trades={data['trades_today']}/{data['max_trades_per_day']}, allowed={data['trading_allowed']}, reason={data['reason']}")


class TestQuantDashboard:
    """Quant dashboard endpoint tests - /api/quant/dashboard"""

    def test_quant_dashboard(self):
        """GET /api/quant/dashboard returns portfolio, frequency_control, hedge_analysis, watchlist_intelligence, strategy_performance"""
        response = requests.get(f"{BASE_URL}/api/quant/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Portfolio section
        assert "portfolio" in data
        portfolio = data["portfolio"]
        assert "value" in portfolio
        assert "initial_capital" in portfolio
        assert "total_pnl" in portfolio
        assert "day_pnl" in portfolio
        assert "total_trades" in portfolio
        assert "win_rate" in portfolio
        assert "max_drawdown" in portfolio
        assert "equity_curve" in portfolio
        
        # Frequency control section
        assert "frequency_control" in data
        fc = data["frequency_control"]
        assert "trades_today" in fc
        assert "max_per_day" in fc
        assert "consecutive_losses" in fc
        assert "max_consec_losses" in fc
        assert "allowed" in fc
        assert "reason" in fc
        
        # Hedge analysis section
        assert "hedge_analysis" in data
        hedge = data["hedge_analysis"]
        assert "net_exposure" in hedge
        assert "bullish_pct" in hedge
        assert "bearish_pct" in hedge
        assert "hedge_needed" in hedge
        
        # Watchlist intelligence section
        assert "watchlist_intelligence" in data
        wi = data["watchlist_intelligence"]
        assert isinstance(wi, list)
        assert len(wi) > 0
        
        # Check watchlist item structure
        for item in wi:
            assert "symbol" in item
            assert "price" in item
            assert "signal_action" in item
            assert "signal_score" in item
            assert "options_flow" in item
            assert "flow_strength" in item
            assert "ai_direction" in item
            assert "ai_confidence" in item
            assert "rsi" in item
        
        # Strategy performance section
        assert "strategy_performance" in data
        sp = data["strategy_performance"]
        assert isinstance(sp, list)
        
        # Additional metadata
        assert "quant_trading_hours" in data
        assert "trading_window" in data
        assert "min_rr_ratio" in data
        assert "min_rank_score" in data
        assert "timestamp" in data
        
        print(f"Quant Dashboard: portfolio_value={portfolio['value']}, watchlist_symbols={len(wi)}, strategies={len(sp)}")

    def test_quant_dashboard_equity_curve(self):
        """Verify equity curve data structure"""
        response = requests.get(f"{BASE_URL}/api/quant/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        equity_curve = data["portfolio"]["equity_curve"]
        if len(equity_curve) > 0:
            for point in equity_curve:
                assert "date" in point
                assert "equity" in point
                assert isinstance(point["equity"], (int, float))
        
        print(f"Equity curve points: {len(equity_curve)}")


class TestTradingWindowAndRRRatio:
    """Tests for updated trading window (09:30-14:45) and R:R ratio (1:2)"""

    def test_trading_window_in_frequency_status(self):
        """Verify trading window is 09:30-14:45 IST"""
        response = requests.get(f"{BASE_URL}/api/quant/frequency-status")
        assert response.status_code == 200
        data = response.json()
        
        # Trading window should be 09:30 - 14:45
        trading_window = data["trading_window"]
        assert "14:45" in trading_window, f"Expected 14:45 in trading window, got {trading_window}"
        assert ("09:30" in trading_window or "9:30" in trading_window), f"Expected 09:30 in trading window, got {trading_window}"
        
        print(f"Trading window: {trading_window}")

    def test_rr_ratio_is_1_to_2(self):
        """Verify minimum R:R ratio is 2.0 (1:2)"""
        response = requests.get(f"{BASE_URL}/api/quant/frequency-status")
        assert response.status_code == 200
        data = response.json()
        
        min_rr = data["min_rr_ratio"]
        assert min_rr == 2.0, f"Expected min R:R ratio of 2.0 (1:2), got {min_rr}"
        
        print(f"Min R:R ratio: 1:{min_rr}")

    def test_rr_ratio_in_dashboard(self):
        """Verify R:R ratio displayed in dashboard"""
        response = requests.get(f"{BASE_URL}/api/quant/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Should be "1:2" format
        assert "min_rr_ratio" in data
        assert "1:2" in data["min_rr_ratio"] or data["min_rr_ratio"] == "1:2"
        
        print(f"Dashboard R:R ratio: {data['min_rr_ratio']}")


class TestPipelineSteps:
    """Test pipeline step structure when steps are present"""

    def test_pipeline_step_structure(self):
        """Verify pipeline steps have correct structure when signal is actionable"""
        # Test multiple symbols to find one with steps
        for symbol in SYMBOLS:
            response = requests.get(f"{BASE_URL}/api/quant/pipeline/{symbol}")
            assert response.status_code == 200
            data = response.json()
            
            if len(data["steps"]) > 0:
                step = data["steps"][0]
                assert "step" in step
                assert "name" in step
                assert "passed" in step
                assert isinstance(step["passed"], bool)
                assert "details" in step
                
                print(f"Pipeline step structure for {symbol}: step={step['step']}, name={step['name']}, passed={step['passed']}")
                break
        else:
            print("All symbols returned HOLD/SKIP with no steps (expected outside trading hours)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
