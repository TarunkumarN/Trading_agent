"""
MiniMax Trading Dashboard - F&O Contract Resolution & Market Charts Tests
============================================================================
Tests new features in iteration 5:
- F&O Contract Resolution (/api/quant/contract/{symbol})
- Full Pipeline with Contract (/api/quant/pipeline-full/{symbol})
- Market Chart Data (/api/market/chart/{symbol})
- Charts Summary for Market Page (/api/market/charts-summary)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://market-analysis-ai-5.preview.emergentagent.com"


class TestContractResolutionNIFTY:
    """F&O Contract Resolution tests for NIFTY index - /api/quant/contract/{symbol}"""

    def test_nifty_buy_returns_ce_contract(self):
        """GET /api/quant/contract/NIFTY?action=BUY returns CE contract with proper NIFTY price (~23000+)"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/NIFTY", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        # Core structure
        assert data["symbol"] == "NIFTY"
        assert data["action"] == "BUY"
        assert "current_price" in data
        assert data["current_price"] > 23000, f"NIFTY price should be ~23000+, got {data['current_price']}"
        
        # Options contract
        assert "options" in data
        options = data["options"]
        assert options["option_type"] == "CE", "Bullish (BUY) should resolve to CE (Call)"
        assert options["exchange"] == "NFO"
        assert options["lot_size"] == 25, "NIFTY lot size should be 25"
        assert options["direction"] == "BULLISH"
        assert "CE" in options["trading_symbol"]
        assert options["action"] == "BUY CE"
        
        # Futures contract
        assert "futures" in data
        futures = data["futures"]
        assert futures["instrument_type"] == "FUT"
        assert "FUT" in futures["trading_symbol"]
        
        # Recommendation
        assert "recommendation" in data
        assert "BUY CE" in data["recommendation"]
        
        print(f"NIFTY BUY: price={data['current_price']}, trading_symbol={options['trading_symbol']}, strike={options['strike_price']}")

    def test_nifty_sell_returns_pe_contract(self):
        """GET /api/quant/contract/NIFTY?action=SELL returns PE contract"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/NIFTY", params={"action": "SELL"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "NIFTY"
        assert data["action"] == "SELL"
        
        # Options contract
        options = data["options"]
        assert options["option_type"] == "PE", "Bearish (SELL) should resolve to PE (Put)"
        assert options["direction"] == "BEARISH"
        assert "PE" in options["trading_symbol"]
        assert options["action"] == "BUY PE"
        
        # Recommendation
        assert "BUY PE" in data["recommendation"]
        
        print(f"NIFTY SELL: trading_symbol={options['trading_symbol']}, strike={options['strike_price']}")


class TestContractResolutionBANKNIFTY:
    """F&O Contract Resolution tests for BANKNIFTY index"""

    def test_banknifty_sell_returns_pe_with_lot_size_15(self):
        """GET /api/quant/contract/BANKNIFTY?action=SELL returns PE with lot_size 15"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/BANKNIFTY", params={"action": "SELL"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "BANKNIFTY"
        assert data["action"] == "SELL"
        
        # Options contract
        options = data["options"]
        assert options["option_type"] == "PE"
        assert options["lot_size"] == 15, f"BANKNIFTY lot size should be 15, got {options['lot_size']}"
        assert options["exchange"] == "NFO"
        assert "PE" in options["trading_symbol"]
        
        print(f"BANKNIFTY SELL: lot_size={options['lot_size']}, trading_symbol={options['trading_symbol']}")

    def test_banknifty_buy_returns_ce(self):
        """GET /api/quant/contract/BANKNIFTY?action=BUY returns CE contract"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/BANKNIFTY", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        options = data["options"]
        assert options["option_type"] == "CE"
        assert options["lot_size"] == 15
        assert "CE" in options["trading_symbol"]
        
        print(f"BANKNIFTY BUY: trading_symbol={options['trading_symbol']}")


class TestContractResolutionEquity:
    """F&O Contract Resolution tests for equity stocks"""

    def test_reliance_buy_returns_ce_with_lot_size_250(self):
        """GET /api/quant/contract/RELIANCE?action=BUY returns CE with lot_size 250"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/RELIANCE", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "RELIANCE"
        assert data["action"] == "BUY"
        
        # Options contract
        options = data["options"]
        assert options["option_type"] == "CE"
        assert options["lot_size"] == 250, f"RELIANCE lot size should be 250, got {options['lot_size']}"
        assert options["exchange"] == "NFO"
        assert options["direction"] == "BULLISH"
        assert "CE" in options["trading_symbol"]
        
        # Contract details
        assert "strike_price" in options
        assert "atm_strike" in options
        assert "estimated_premium" in options
        assert "capital_required" in options
        assert "expiry" in options
        
        print(f"RELIANCE BUY: lot_size={options['lot_size']}, strike={options['strike_price']}, trading_symbol={options['trading_symbol']}")

    def test_reliance_sell_returns_pe(self):
        """GET /api/quant/contract/RELIANCE?action=SELL returns PE contract"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/RELIANCE", params={"action": "SELL"})
        assert response.status_code == 200
        data = response.json()
        
        options = data["options"]
        assert options["option_type"] == "PE"
        assert options["direction"] == "BEARISH"
        assert "PE" in options["trading_symbol"]
        
        print(f"RELIANCE SELL: trading_symbol={options['trading_symbol']}")

    def test_other_equity_symbols_lot_sizes(self):
        """Test lot sizes for other equity symbols"""
        test_cases = [
            ("HDFCBANK", 550),
            ("TCS", 150),
            ("INFY", 300),
            ("ICICIBANK", 700),
            ("SBIN", 1500),
        ]
        
        for symbol, expected_lot_size in test_cases:
            response = requests.get(f"{BASE_URL}/api/quant/contract/{symbol}", params={"action": "BUY"})
            assert response.status_code == 200
            data = response.json()
            
            options = data["options"]
            assert options["lot_size"] == expected_lot_size, f"{symbol} lot size should be {expected_lot_size}, got {options['lot_size']}"
            
            print(f"{symbol}: lot_size={options['lot_size']} (expected {expected_lot_size})")


class TestFullPipelineWithContract:
    """Full pipeline with contract resolution tests - /api/quant/pipeline-full/{symbol}"""

    def test_pipeline_full_reliance(self):
        """GET /api/quant/pipeline-full/RELIANCE returns pipeline result with contract field"""
        response = requests.get(f"{BASE_URL}/api/quant/pipeline-full/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        
        # Pipeline structure
        assert "pipeline_result" in data
        assert data["pipeline_result"] in ["PASS", "FAIL", "SKIP"]
        assert "steps" in data
        assert "symbol" in data
        assert data["symbol"] == "RELIANCE"
        assert "action" in data
        assert data["action"] in ["BUY", "SELL", "HOLD"]
        
        # Entry/exit levels
        assert "entry" in data
        assert "stop_loss" in data
        assert "target" in data
        assert "risk_reward_ratio" in data
        
        # Contract field (can be null if action is HOLD)
        assert "contract" in data
        if data["action"] != "HOLD":
            contract = data["contract"]
            assert contract is not None
            assert "trading_symbol" in contract
            assert "option_type" in contract
            assert "lot_size" in contract
            print(f"Pipeline RELIANCE: result={data['pipeline_result']}, action={data['action']}, contract={contract['trading_symbol']}")
        else:
            assert data["contract"] is None
            print(f"Pipeline RELIANCE: result={data['pipeline_result']}, action=HOLD, contract=null (expected)")

    def test_pipeline_full_nifty(self):
        """GET /api/quant/pipeline-full/NIFTY returns pipeline for index"""
        response = requests.get(f"{BASE_URL}/api/quant/pipeline-full/NIFTY")
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "NIFTY"
        assert "contract" in data
        
        print(f"Pipeline NIFTY: result={data['pipeline_result']}, action={data['action']}")


class TestMarketChart:
    """Market chart data tests - /api/market/chart/{symbol}"""

    def test_nifty_intraday_chart(self):
        """GET /api/market/chart/NIFTY returns candles array with OHLCV data"""
        response = requests.get(f"{BASE_URL}/api/market/chart/NIFTY")
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "NIFTY"
        assert data["period"] == "intraday"
        assert "candles" in data
        assert isinstance(data["candles"], list)
        assert len(data["candles"]) > 0, "Should have candle data"
        
        # Verify candle structure
        candle = data["candles"][0]
        assert "time" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle
        
        # Verify OHLC logic
        for c in data["candles"][:5]:
            assert c["high"] >= c["low"], f"High should be >= Low: {c}"
            assert c["high"] >= c["open"], f"High should be >= Open: {c}"
            assert c["high"] >= c["close"], f"High should be >= Close: {c}"
            assert c["low"] <= c["open"], f"Low should be <= Open: {c}"
            assert c["low"] <= c["close"], f"Low should be <= Close: {c}"
        
        # Additional data
        assert "current_price" in data
        assert "open_price" in data
        assert "day_high" in data
        assert "day_low" in data
        assert "change" in data
        assert "change_pct" in data
        assert "candle_count" in data
        
        print(f"NIFTY chart: {data['candle_count']} candles, price={data['current_price']}, change={data['change_pct']}%")

    def test_reliance_daily_chart(self):
        """GET /api/market/chart/RELIANCE?period=daily returns daily candles for 30 days"""
        response = requests.get(f"{BASE_URL}/api/market/chart/RELIANCE", params={"period": "daily"})
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "RELIANCE"
        assert data["period"] == "daily"
        assert "candles" in data
        assert len(data["candles"]) > 0
        
        # Daily candles should have date format time
        candle = data["candles"][0]
        assert "-" in candle["time"], f"Daily candle time should be date format: {candle['time']}"
        
        print(f"RELIANCE daily chart: {data['candle_count']} candles, change={data['change_pct']}%")

    def test_banknifty_chart(self):
        """GET /api/market/chart/BANKNIFTY returns chart data"""
        response = requests.get(f"{BASE_URL}/api/market/chart/BANKNIFTY")
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "BANKNIFTY"
        assert len(data["candles"]) > 0
        
        print(f"BANKNIFTY chart: {data['candle_count']} candles")


class TestChartsSummary:
    """Charts summary tests for market page - /api/market/charts-summary"""

    def test_charts_summary_structure(self):
        """GET /api/market/charts-summary returns indices (nifty, banknifty) with points arrays and stocks sparklines"""
        response = requests.get(f"{BASE_URL}/api/market/charts-summary")
        assert response.status_code == 200
        data = response.json()
        
        # Indices section
        assert "indices" in data
        indices = data["indices"]
        
        # NIFTY chart
        assert "nifty" in indices
        nifty = indices["nifty"]
        assert "symbol" in nifty
        assert nifty["symbol"] == "NIFTY"
        assert "points" in nifty
        assert isinstance(nifty["points"], list)
        assert len(nifty["points"]) > 0, "NIFTY should have chart points"
        
        # Verify point structure
        point = nifty["points"][0]
        assert "time" in point
        assert "price" in point
        
        assert "current" in nifty
        assert "previous" in nifty
        assert "change" in nifty
        assert "change_pct" in nifty
        
        # BANKNIFTY chart
        assert "banknifty" in indices
        banknifty = indices["banknifty"]
        assert banknifty["symbol"] == "BANKNIFTY"
        assert len(banknifty["points"]) > 0
        
        print(f"NIFTY: {len(nifty['points'])} points, current={nifty['current']}, change={nifty['change_pct']}%")
        print(f"BANKNIFTY: {len(banknifty['points'])} points, current={banknifty['current']}, change={banknifty['change_pct']}%")

    def test_charts_summary_stocks_sparklines(self):
        """GET /api/market/charts-summary returns stocks sparklines for 8 watchlist stocks"""
        response = requests.get(f"{BASE_URL}/api/market/charts-summary")
        assert response.status_code == 200
        data = response.json()
        
        # Stocks sparklines section
        assert "stocks" in data
        stocks = data["stocks"]
        assert isinstance(stocks, list)
        assert len(stocks) == 8, f"Should have 8 stock sparklines, got {len(stocks)}"
        
        # Verify expected symbols
        expected_symbols = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "SBIN", "ITC", "BAJFINANCE"]
        actual_symbols = [s["symbol"] for s in stocks]
        for sym in expected_symbols:
            assert sym in actual_symbols, f"Missing stock: {sym}"
        
        # Verify stock sparkline structure
        for stock in stocks:
            assert "symbol" in stock
            assert "points" in stock
            assert isinstance(stock["points"], list)
            assert len(stock["points"]) > 0, f"{stock['symbol']} should have sparkline points"
            assert "current" in stock
            assert "change_pct" in stock
            
            print(f"{stock['symbol']}: {len(stock['points'])} points, current={stock['current']}, change={stock['change_pct']}%")


class TestContractResolutionDetails:
    """Additional contract resolution detail tests"""

    def test_contract_has_expiry_date(self):
        """Verify contract has proper expiry date format"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/NIFTY", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        options = data["options"]
        assert "expiry" in options
        # Expiry should be in YYYY-MM-DD format
        assert len(options["expiry"]) == 10, f"Expiry should be YYYY-MM-DD format: {options['expiry']}"
        assert "-" in options["expiry"]
        
        print(f"Expiry date: {options['expiry']}")

    def test_contract_trading_symbol_format(self):
        """Verify trading symbol format includes symbol, expiry code, strike, and option type"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/NIFTY", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        trading_symbol = data["options"]["trading_symbol"]
        # Format: NIFTY{YYMMDD}{STRIKE}{CE/PE}
        assert "NIFTY" in trading_symbol
        assert "CE" in trading_symbol
        
        print(f"Trading symbol: {trading_symbol}")

    def test_contract_capital_required(self):
        """Verify capital required is calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/quant/contract/RELIANCE", params={"action": "BUY"})
        assert response.status_code == 200
        data = response.json()
        
        options = data["options"]
        # Capital required = premium * lot_size
        expected_capital = options["estimated_premium"] * options["lot_size"]
        assert abs(options["capital_required"] - expected_capital) < 1, \
            f"Capital required mismatch: {options['capital_required']} vs {expected_capital}"
        
        print(f"Capital required: {options['capital_required']} (premium={options['estimated_premium']} x lot={options['lot_size']})")


class TestExistingQuantAPIsStillWork:
    """Regression tests - verify existing quant APIs still work"""

    def test_options_flow_still_works(self):
        """GET /api/quant/options-flow/{symbol} still works"""
        response = requests.get(f"{BASE_URL}/api/quant/options-flow/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        assert "signal" in data
        assert "strength" in data
        print(f"Options flow RELIANCE: signal={data['signal']}")

    def test_dark_pool_still_works(self):
        """GET /api/quant/dark-pool/{symbol} still works"""
        response = requests.get(f"{BASE_URL}/api/quant/dark-pool/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        assert "zone_type" in data
        print(f"Dark pool RELIANCE: type={data['zone_type']}")

    def test_ai_prediction_still_works(self):
        """GET /api/quant/ai-prediction/{symbol} still works"""
        response = requests.get(f"{BASE_URL}/api/quant/ai-prediction/HDFCBANK")
        assert response.status_code == 200
        data = response.json()
        assert "predicted_direction" in data
        print(f"AI prediction HDFCBANK: direction={data['predicted_direction']}")

    def test_trade_rank_still_works(self):
        """GET /api/quant/trade-rank/{symbol} still works"""
        response = requests.get(f"{BASE_URL}/api/quant/trade-rank/TCS")
        assert response.status_code == 200
        data = response.json()
        assert "total_score" in data
        print(f"Trade rank TCS: score={data['total_score']}")

    def test_hedge_analysis_still_works(self):
        """GET /api/quant/hedge-analysis still works"""
        response = requests.get(f"{BASE_URL}/api/quant/hedge-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "net_exposure" in data
        print(f"Hedge analysis: exposure={data['net_exposure']}")

    def test_frequency_status_still_works(self):
        """GET /api/quant/frequency-status still works"""
        response = requests.get(f"{BASE_URL}/api/quant/frequency-status")
        assert response.status_code == 200
        data = response.json()
        assert "trading_allowed" in data
        print(f"Frequency status: allowed={data['trading_allowed']}")

    def test_quant_dashboard_still_works(self):
        """GET /api/quant/dashboard still works"""
        response = requests.get(f"{BASE_URL}/api/quant/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "portfolio" in data
        assert "watchlist_intelligence" in data
        print(f"Quant dashboard: portfolio_value={data['portfolio']['value']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
