from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    product_name: str = Field(min_length=1, max_length=200)
    unit_cost: float = Field(default=0, ge=0)
    lead_time_days: int = Field(default=7, ge=0)
    reorder_point: int = Field(default=0, ge=0)
class ProductOut(ProductCreate, ORMModel):
    product_id: int

class SupplierCreate(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=150)
    email: str | None = None
class SupplierOut(SupplierCreate, ORMModel):
    supplier_id: int

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    order_date: date
    expected_date: date | None = None
    received_date: date | None = None
    status: str = "ordered"
class PurchaseOrderOut(PurchaseOrderCreate, ORMModel):
    po_id: int

class StockTransactionCreate(BaseModel):
    product_id: int
    transaction_date: date = Field(default_factory=date.today)
    transaction_type: str = Field(pattern="^(receipt|sale|adjustment_in|adjustment_out)$")
    quantity: int = Field(gt=0)
class StockTransactionOut(StockTransactionCreate, ORMModel):
    transaction_id: int

class DemandCreate(BaseModel):
    product_id: int
    demand_date: date
    quantity: int = Field(ge=0)
class DemandOut(DemandCreate, ORMModel):
    demand_id: int
