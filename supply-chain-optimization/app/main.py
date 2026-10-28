from fastapi import FastAPI
from app.db.database import Base, engine
from app.api.routes import products, suppliers, purchase_orders, stock_transactions, analytics

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Supply Chain Optimization and Inventory Forecasting System", version="1.1.0",
              description="End-to-end supply chain optimization and inventory forecasting: REST APIs, reorder-point analysis, supplier delivery performance, demand trends, forecast evaluation, and stock risk flags.")
app.include_router(products.router, prefix="/api/v1")
app.include_router(suppliers.router, prefix="/api/v1")
app.include_router(purchase_orders.router, prefix="/api/v1")
app.include_router(stock_transactions.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
@app.get("/")
def root(): return {"message": "Supply Chain Optimization API", "docs": "/docs", "health": "/health"}
@app.get("/health")
def health(): return {"status": "ok"}
