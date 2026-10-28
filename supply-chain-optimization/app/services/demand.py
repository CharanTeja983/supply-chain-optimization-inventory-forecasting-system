from datetime import date, timedelta
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import DemandRecord

def demand_summary(db: Session, product_id: int | None = None, days: int = 90) -> dict:
    start = date.today() - timedelta(days=max(1, days) - 1)
    query = select(DemandRecord).where(DemandRecord.demand_date >= start)
    if product_id is not None:
        query = query.where(DemandRecord.product_id == product_id)
    records = db.scalars(query).all()
    if not records:
        return {"period_days": days, "total_demand": 0, "average_daily_demand": 0, "daily": []}
    frame = pd.DataFrame([{"date": r.demand_date.isoformat(), "quantity": r.quantity} for r in records])
    daily = frame.groupby("date", as_index=False)["quantity"].sum().sort_values("date")
    return {"period_days": days, "total_demand": int(daily.quantity.sum()),
            "average_daily_demand": round(float(daily.quantity.sum()) / days, 2),
            "daily": [{"date": r.date, "quantity": int(r.quantity)} for r in daily.itertuples()]}

def forecast_summary(db: Session, product_id: int, days: int = 30) -> dict:
    # Transparent baseline: next-period forecast equals recent average daily demand.
    summary = demand_summary(db, product_id, days)
    forecast_daily = summary["average_daily_demand"]
    return {"product_id": product_id, "method": "moving-average baseline",
            "historical_window_days": days, "historical_total_demand": summary["total_demand"],
            "historical_average_daily_demand": forecast_daily,
            "forecast_horizon_days": days, "forecast_total_demand": round(forecast_daily * days, 2),
            "evaluation_note": "Baseline decision-support estimate, not a validated predictive model. Evaluate with a chronological holdout before operational use."}
