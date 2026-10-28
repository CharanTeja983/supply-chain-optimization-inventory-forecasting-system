from datetime import date
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    supplier_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(255))
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="supplier")

class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    demand_records: Mapped[list["DemandRecord"]] = relationship(back_populates="product", cascade="all, delete-orphan")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    po_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.supplier_id"), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[date | None] = mapped_column(Date)
    received_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="ordered")
    supplier: Mapped[Supplier] = relationship(back_populates="purchase_orders")

class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)  # receipt, sale, adjustment_in, adjustment_out
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    product: Mapped[Product] = relationship(back_populates="stock_transactions")

class DemandRecord(Base):
    __tablename__ = "demand_records"
    demand_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    demand_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    product: Mapped[Product] = relationship(back_populates="demand_records")
