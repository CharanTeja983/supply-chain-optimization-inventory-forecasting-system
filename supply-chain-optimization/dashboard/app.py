import os
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

API = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/") + "/api/v1"
st.set_page_config(page_title="Supply Chain Optimization & Inventory Forecasting System", page_icon="📦", layout="wide")
st.title("📦 Supply Chain Optimization & Inventory Forecasting")
st.caption("Decision-support estimates only. Review recommendations before placing purchase orders.")

@st.cache_data(ttl=30)
def get_json(path, params=None):
    response = requests.get(f"{API}{path}", params=params, timeout=8)
    response.raise_for_status()
    return response.json()

try:
    products = get_json("/products")
    inventory = get_json("/analytics/inventory", {"lookback_days": 30})
    suppliers = get_json("/analytics/suppliers")
except requests.RequestException as exc:
    st.error(f"Cannot reach API at {API}. Start the API and database, then refresh. Details: {exc}")
    st.stop()

items = inventory.get("items", [])
frame = pd.DataFrame(items)
shortages = int((frame.get("risk_status", pd.Series(dtype=str)) == "shortage_risk").sum()) if not frame.empty else 0
excess = int((frame.get("risk_status", pd.Series(dtype=str)) == "excess_risk").sum()) if not frame.empty else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric("Products", len(products)); c2.metric("Shortage risks", shortages); c3.metric("Excess-stock risks", excess); c4.metric("Suppliers", len(suppliers))
st.subheader("Inventory risk and reorder recommendations")
st.caption("Reorder point = average daily demand × lead time + average daily demand × safety-stock days. Default safety stock: 7 days.")
if frame.empty:
    st.info("No products yet. Add products and stock/demand records through the API docs at /docs.")
else:
    display_cols = [c for c in ["sku", "product_name", "current_stock", "average_daily_demand", "lead_time_days", "calculated_reorder_point", "suggested_order_quantity", "risk_status"] if c in frame.columns]
    st.dataframe(frame[display_cols], use_container_width=True, hide_index=True)
    st.download_button("Download inventory report CSV", frame.to_csv(index=False).encode("utf-8"), "inventory_report.csv", "text/csv")
    chart = frame.set_index("product_name")[["current_stock", "calculated_reorder_point"]]
    st.bar_chart(chart)

st.subheader("Supplier delivery performance")
supplier_frame = pd.DataFrame(suppliers)
if supplier_frame.empty:
    st.info("No supplier data yet.")
else:
    st.dataframe(supplier_frame, use_container_width=True, hide_index=True)
    valid = supplier_frame.dropna(subset=["average_actual_lead_time_days"])
    if not valid.empty:
        fig, ax = plt.subplots()
        ax.bar(valid["supplier_name"], valid["average_actual_lead_time_days"])
        ax.set_ylabel("Average actual lead time (days)"); ax.set_xlabel("Supplier")
        ax.tick_params(axis="x", rotation=25); fig.tight_layout(); st.pyplot(fig); plt.close(fig)

st.subheader("Demand trend, forecast, and model evaluation")
if products:
    labels = {f"{p['sku']} — {p['product_name']}": p["product_id"] for p in products}
    chosen = st.selectbox("Choose a product for forecasting", list(labels))
    forecast_days = st.slider("Forecast horizon (days)", min_value=7, max_value=90, value=30, step=1)
    history_days = st.select_slider("Historical window (days)", options=[30, 60, 90, 180, 365], value=90)
    try:
        forecast = get_json(f"/analytics/forecast/{labels[chosen]}", {"days": forecast_days, "history_days": history_days})
        history_frame = pd.DataFrame(forecast.get("historical_daily", []))
        future_frame = pd.DataFrame(forecast.get("forecast_daily", []))
        if not history_frame.empty:
            history_frame["date"] = pd.to_datetime(history_frame["date"])
            history_frame = history_frame.rename(columns={"actual_quantity": "Actual demand"}).set_index("date")
            history_frame["Forecast"] = float("nan")
            if not future_frame.empty:
                future_frame["date"] = pd.to_datetime(future_frame["date"])
                future_frame = future_frame.rename(columns={"forecast_quantity": "Forecast"}).set_index("date")
                future_frame["Actual demand"] = float("nan")
                plot_frame = pd.concat([history_frame[["Actual demand", "Forecast"]], future_frame[["Actual demand", "Forecast"]]]).sort_index()
            else:
                plot_frame = history_frame[["Actual demand", "Forecast"]]
            st.line_chart(plot_frame)
        else:
            st.info("No historical demand records are available for this product. The forecast will be zero until demand data is added.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Recent daily average", f"{forecast['recent_average_daily_demand']} units")
        m2.metric(f"Forecast ({forecast_days} days)", f"{forecast['forecast_total_demand']} units")
        m3.metric("Evaluation holdout", f"{forecast['evaluation']['holdout_days']} days")
        st.caption(f"Forecast method: {forecast['method']}. {forecast['evaluation_note']}")
        st.markdown("**Forecast evaluation against a naive baseline**")
        evaluation = forecast.get("evaluation", {})
        st.dataframe(pd.DataFrame([
            {"Model": "7-day moving average", "MAE": evaluation.get("moving_average_mae"), "RMSE": evaluation.get("moving_average_rmse")},
            {"Model": "Previous-day naive baseline", "MAE": evaluation.get("naive_baseline_mae"), "RMSE": evaluation.get("naive_baseline_rmse")},
        ]), use_container_width=True, hide_index=True)
        st.write(f"**Lower-MAE comparison:** {evaluation.get('better_baseline', 'insufficient_history')}")
        st.download_button("Download forecast JSON", pd.Series(forecast).to_json(indent=2), f"forecast_product_{labels[chosen]}.json", "application/json")
    except requests.RequestException as exc:
        st.warning(f"Forecast report unavailable: {exc}")
