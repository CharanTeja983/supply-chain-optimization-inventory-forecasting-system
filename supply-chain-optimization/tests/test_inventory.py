from datetime import date, timedelta
from app.db.database import Base, engine, SessionLocal
from app.db.models import Product, StockTransaction, DemandRecord
from app.services.inventory import current_stock, inventory_assessment

def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_current_stock_and_reorder_point():
    db = SessionLocal()
    try:
        p = Product(sku="TEST-1", product_name="Test item", unit_cost=1, lead_time_days=5, reorder_point=10)
        db.add(p); db.commit(); db.refresh(p)
        db.add_all([
            StockTransaction(product_id=p.product_id, transaction_date=date.today(), transaction_type="receipt", quantity=30),
            StockTransaction(product_id=p.product_id, transaction_date=date.today(), transaction_type="sale", quantity=8),
            DemandRecord(product_id=p.product_id, demand_date=date.today(), quantity=10),
        ]); db.commit()
        assert current_stock(db, p.product_id) == 22
        result = inventory_assessment(db, p, lookback_days=1, safety_stock_days=2)
        assert result["calculated_reorder_point"] == 70
        assert result["suggested_order_quantity"] == 48
        assert result["risk_status"] == "shortage_risk"
    finally: db.close()
