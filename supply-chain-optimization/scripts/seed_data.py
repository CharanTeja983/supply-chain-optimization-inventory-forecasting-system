"""Insert a small deterministic demo dataset. Safe to rerun: existing SKUs are skipped."""
from datetime import date, timedelta
from sqlalchemy import select
from app.db.database import Base, SessionLocal, engine
from app.db.models import Product, Supplier, PurchaseOrder, StockTransaction, DemandRecord

Base.metadata.create_all(bind=engine)
db = SessionLocal()
today = date.today()
try:
    supplier_specs = [("Reliable Components Ltd", "sales@example.com"), ("Metro Wholesale", "orders@example.com"), ("Northstar Supply", "hello@example.com")]
    suppliers = {}
    for name, email in supplier_specs:
        supplier = db.scalar(select(Supplier).where(Supplier.supplier_name == name))
        if not supplier:
            supplier = Supplier(supplier_name=name, email=email); db.add(supplier); db.flush()
        suppliers[name] = supplier
    specs = [("SKU-1001", "USB-C Cable", 2.5, 5, 40), ("SKU-1002", "Wireless Mouse", 9.0, 10, 25), ("SKU-1003", "Laptop Stand", 14.0, 14, 15)]
    products = {}
    for sku, name, cost, lead, opening in specs:
        p = db.scalar(select(Product).where(Product.sku == sku))
        if not p:
            p = Product(sku=sku, product_name=name, unit_cost=cost, lead_time_days=lead, reorder_point=20); db.add(p); db.flush()
            db.add(StockTransaction(product_id=p.product_id, transaction_date=today-timedelta(days=90), transaction_type="receipt", quantity=opening))
        products[sku] = p
    if not db.scalar(select(PurchaseOrder).limit(1)):
        db.add(PurchaseOrder(supplier_id=suppliers["Reliable Components Ltd"].supplier_id, order_date=today-timedelta(days=25), expected_date=today-timedelta(days=18), received_date=today-timedelta(days=17), status="received"))
        db.add(PurchaseOrder(supplier_id=suppliers["Metro Wholesale"].supplier_id, order_date=today-timedelta(days=15), expected_date=today-timedelta(days=5), received_date=None, status="ordered"))
        db.add(PurchaseOrder(supplier_id=suppliers["Northstar Supply"].supplier_id, order_date=today-timedelta(days=40), expected_date=today-timedelta(days=30), received_date=today-timedelta(days=27), status="received"))
    for sku, product in products.items():
        if not db.scalar(select(DemandRecord).where(DemandRecord.product_id == product.product_id).limit(1)):
            for day_offset in range(89, -1, -1):
                # Stable synthetic demand pattern for demonstration only.
                qty = max(0, ((day_offset * (product.product_id + 2)) % 7) - 1)
                db.add(DemandRecord(product_id=product.product_id, demand_date=today-timedelta(days=day_offset), quantity=qty))
                if qty:
                    db.add(StockTransaction(product_id=product.product_id, transaction_date=today-timedelta(days=day_offset), transaction_type="sale", quantity=qty))
    db.commit()
    print("Demo data ready: 3 suppliers, 3 products, purchase orders, stock movements and 90 days of synthetic demand.")
finally:
    db.close()
