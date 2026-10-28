from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Product
from app.services.inventory import inventory_assessment
from app.services.demand import demand_summary
from app.services.forecasting import forecast_summary
from app.services.supplier import supplier_summary

router = APIRouter(prefix="/analytics", tags=["Analytics"])
@router.get("/inventory")
def inventory_report(safety_stock_days: int | None = None, lookback_days: int = 30, db: Session = Depends(get_db)):
    if lookback_days < 1 or lookback_days > 365: raise HTTPException(400, "lookback_days must be between 1 and 365")
    if safety_stock_days is not None and not 0 <= safety_stock_days <= 365: raise HTTPException(400, "safety_stock_days must be between 0 and 365")
    products = db.scalars(select(Product).order_by(Product.product_id)).all()
    return {"assumptions": {"demand_window_days": lookback_days, "safety_stock_days": safety_stock_days if safety_stock_days is not None else 7,
            "reorder_point_formula": "ceil(average daily demand * supplier lead time days + average daily demand * safety stock days)",
            "units": "product units; lead and safety stock are days", "order_placement": "not automatic"},
            "items": [inventory_assessment(db, p, lookback_days, safety_stock_days) for p in products]}
@router.get("/demand")
def demand_report(product_id: int | None = None, days: int = 90, db: Session = Depends(get_db)):
    if days < 1 or days > 730: raise HTTPException(400, "days must be between 1 and 730")
    return demand_summary(db, product_id, days)
@router.get("/forecast/{product_id}")
def forecast_report(product_id: int, days: int = 30, history_days: int = 90, db: Session = Depends(get_db)):
    if not db.get(Product, product_id): raise HTTPException(404, "Product not found")
    if days < 1 or days > 365: raise HTTPException(400, "days must be between 1 and 365")
    if history_days < 14 or history_days > 730: raise HTTPException(400, "history_days must be between 14 and 730")
    return forecast_summary(db, product_id, days, history_days)
@router.get("/suppliers")
def supplier_report(db: Session = Depends(get_db)): return supplier_summary(db)
