from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import PurchaseOrder, Supplier

def supplier_summary(db: Session) -> list[dict]:
    suppliers = db.scalars(select(Supplier)).all()
    results = []
    for supplier in suppliers:
        orders = db.scalars(select(PurchaseOrder).where(PurchaseOrder.supplier_id == supplier.supplier_id)).all()
        received = [o for o in orders if o.received_date is not None]
        lead_times = [(o.received_date - o.order_date).days for o in received]
        on_time = [o for o in received if o.expected_date is not None and o.received_date <= o.expected_date]
        expected_orders = [o for o in received if o.expected_date is not None]
        results.append({"supplier_id": supplier.supplier_id, "supplier_name": supplier.supplier_name,
                        "total_orders": len(orders), "received_orders": len(received),
                        "average_actual_lead_time_days": round(sum(lead_times) / len(lead_times), 2) if lead_times else None,
                        "on_time_delivery_rate_pct": round(100 * len(on_time) / len(expected_orders), 2) if expected_orders else None,
                        "open_orders": sum(1 for o in orders if o.received_date is None)})
    return results
