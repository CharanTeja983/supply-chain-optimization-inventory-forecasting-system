"""Transparent demand forecasting and chronological baseline evaluation."""
from datetime import date, timedelta
import math
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import DemandRecord


def _daily_series(db: Session, product_id: int, days: int) -> pd.Series:
    end = date.today()
    start = end - timedelta(days=days - 1)
    records = db.scalars(select(DemandRecord).where(
        DemandRecord.product_id == product_id,
        DemandRecord.demand_date >= start,
        DemandRecord.demand_date <= end,
    )).all()
    index = pd.date_range(start=start, end=end, freq="D")
    if not records:
        return pd.Series(0.0, index=index)
    frame = pd.DataFrame([{"date": pd.Timestamp(r.demand_date), "quantity": r.quantity} for r in records])
    grouped = frame.groupby("date")["quantity"].sum()
    return grouped.reindex(index, fill_value=0).astype(float)


def _mae(actual, predicted) -> float:
    return round(float(np.mean(np.abs(np.asarray(actual) - np.asarray(predicted)))), 3)


def _rmse(actual, predicted) -> float:
    return round(float(np.sqrt(np.mean((np.asarray(actual) - np.asarray(predicted)) ** 2))), 3)


def forecast_summary(db: Session, product_id: int, days: int = 30, history_days: int = 90) -> dict:
    """Forecast with recent mean and compare it to a naive holdout baseline.

    The evaluation reserves the final 20% (at least 7 days where available) of
    historical observations as a chronological holdout. No future data is used.
    """
    history_days = max(14, min(history_days, 730))
    series = _daily_series(db, product_id, history_days)
    mean_window = min(7, max(1, len(series)))
    recent_mean = float(series.tail(mean_window).mean()) if len(series) else 0.0
    forecast_dates = pd.date_range(start=date.today() + timedelta(days=1), periods=days, freq="D")
    future = [{"date": d.date().isoformat(), "forecast_quantity": round(max(0.0, recent_mean), 2)} for d in forecast_dates]

    holdout_size = min(max(7, int(math.ceil(len(series) * 0.2))), max(0, len(series) - 7))
    evaluation = {"holdout_days": 0, "moving_average_mae": None, "moving_average_rmse": None,
                  "naive_baseline_mae": None, "naive_baseline_rmse": None,
                  "better_baseline": "insufficient_history"}
    if holdout_size > 0:
        values = series.to_numpy(dtype=float)
        split = len(values) - holdout_size
        actual = values[split:]
        moving_predictions, naive_predictions = [], []
        for position in range(split, len(values)):
            prior = values[max(0, position - 7):position]
            moving_predictions.append(float(np.mean(prior)) if len(prior) else 0.0)
            naive_predictions.append(float(values[position - 1]) if position else 0.0)
        moving_mae, naive_mae = _mae(actual, moving_predictions), _mae(actual, naive_predictions)
        evaluation = {"holdout_days": holdout_size,
                      "moving_average_mae": moving_mae,
                      "moving_average_rmse": _rmse(actual, moving_predictions),
                      "naive_baseline_mae": naive_mae,
                      "naive_baseline_rmse": _rmse(actual, naive_predictions),
                      "better_baseline": "moving_average" if moving_mae < naive_mae else "naive" if naive_mae < moving_mae else "tie"}

    total = float(series.sum())
    return {
        "product_id": product_id,
        "method": f"{mean_window}-day moving-average baseline",
        "historical_window_days": history_days,
        "historical_total_demand": int(total),
        "historical_average_daily_demand": round(float(series.mean()), 2) if len(series) else 0,
        "recent_average_daily_demand": round(recent_mean, 2),
        "forecast_horizon_days": days,
        "forecast_total_demand": round(max(0.0, recent_mean) * days, 2),
        "historical_daily": [{"date": idx.date().isoformat(), "actual_quantity": int(value)} for idx, value in series.items()],
        "forecast_daily": future,
        "evaluation": evaluation,
        "evaluation_note": "Chronological holdout metrics compare a trailing 7-day moving average with a previous-day naive baseline. Lower MAE/RMSE is better. This is decision support, not a guarantee; sparse or synthetic data may not represent future demand.",
    }
