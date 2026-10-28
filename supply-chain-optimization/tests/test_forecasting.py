from datetime import date, timedelta
from app.db.database import Base, engine, SessionLocal
from app.db.models import Product, DemandRecord
from app.services.forecasting import forecast_summary


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_forecast_returns_future_series_and_holdout_metrics():
    db = SessionLocal()
    try:
        product = Product(sku="FORECAST-1", product_name="Forecast test", unit_cost=2, lead_time_days=5, reorder_point=10)
        db.add(product)
        db.commit()
        db.refresh(product)
        today = date.today()
        db.add_all([
            DemandRecord(product_id=product.product_id, demand_date=today - timedelta(days=offset), quantity=(offset % 5) + 2)
            for offset in range(40, -1, -1)
        ])
        db.commit()
        result = forecast_summary(db, product.product_id, days=14, history_days=30)
        assert result["forecast_horizon_days"] == 14
        assert len(result["forecast_daily"]) == 14
        assert len(result["historical_daily"]) == 30
        assert result["evaluation"]["holdout_days"] > 0
        assert result["evaluation"]["moving_average_mae"] is not None
        assert result["evaluation"]["naive_baseline_mae"] is not None
        assert result["forecast_total_demand"] >= 0
    finally:
        db.close()
