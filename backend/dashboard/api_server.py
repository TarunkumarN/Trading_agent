"""
api_server.py — Dashboard API server module
Registers all dashboard routers with the main FastAPI app.
"""
from dashboard.routes_portfolio import router as portfolio_router
from dashboard.routes_trades import router as trades_router
from dashboard.routes_market import router as market_router
from dashboard.routes_analytics import router as analytics_router
from dashboard.routes_quant import router as quant_router


def register_dashboard_routes(app):
    """Include all dashboard route modules into the FastAPI app."""
    app.include_router(portfolio_router)
    app.include_router(trades_router)
    app.include_router(market_router)
    app.include_router(analytics_router)
    app.include_router(quant_router)
