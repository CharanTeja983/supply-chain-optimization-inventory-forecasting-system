from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import PurchaseOrder, Supplier
from app.schemas.schemas import PurchaseOrderCreate, PurchaseOrderOut

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])
@router.post("", response_model=PurchaseOrderOut, status_code=201)
def create_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)):
    if not db.get(Supplier, payload.supplier_id): raise HTTPException(404, "Supplier not found")
    obj = PurchaseOrder(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.get("", response_model=list[PurchaseOrderOut])
def list_orders(db: Session = Depends(get_db)): return db.scalars(select(PurchaseOrder).order_by(PurchaseOrder.po_id.desc())).all()
