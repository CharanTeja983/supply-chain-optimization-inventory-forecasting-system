from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Product, StockTransaction, DemandRecord
from app.core.config import settings

INBOUND = {"receipt", "adjustment_in"}
OUTBOUND = {"sale", "adjustment_out"}

def current_stock(db: Session, product_id: int) -> int:
    rows = db.scalars(select(StockTransaction).where(StockTransaction.product_id == product_id)).all()
    return sum(t.quantity if t.transaction_type in INBOUND else -t.quantity for t in rows)

def average_daily_demand(db: Session, product_id: int, lookback_days: int = 30) -> float:
    from datetime import date, timedelta
    start = date.today() - timedelta(days=max(1, lookback_days) - 1)
    records = db.scalars(select(DemandRecord).where(DemandRecord.product_id == product_id, DemandRecord.demand_date >= start)).all()
    # Divide by the entire window, including zero-demand days.
    return sum(r.quantity for r in records) / max(1, lookback_days)

def inventory_assessment(db: Session, product: Product, lookback_days: int = 30, safety_stock_days: int | None = None) -> dict:
    safety_days = settings.safety_stock_days if safety_stock_days is None else max(0, safety_stock_days)
    daily = average_daily_demand(db, product.product_id, lookback_days)
    lead_demand = daily * product.lead_time_days
    safety_stock = daily * safety_days
    calculated_rop = int(__import__('math').ceil(lead_demand + safety_stock))
    stock = current_stock(db, product.product_id)
    status = "shortage_risk" if stock <= calculated_rop else ("excess_risk" if daily > 0 and stock > daily * (product.lead_time_days + safety_days + 60) else "healthy")
    return {"product_id": product.product_id, "sku": product.sku, "product_name": product.product_name,
            "current_stock": stock, "average_daily_demand": round(daily, 2), "lead_time_days": product.lead_time_days,
            "safety_stock_days": safety_days, "estimated_lead_time_demand": round(lead_demand, 2),
            "estimated_safety_stock": round(safety_stock, 2), "calculated_reorder_point": calculated_rop,
            "stored_reorder_point": product.reorder_point, "suggested_order_quantity": max(0, calculated_rop - stock),
            "risk_status": status, "note": "Decision support only; review supplier constraints and open orders before ordering."}
