from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Supplier
from app.schemas.schemas import SupplierCreate, SupplierOut

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])
@router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    obj = Supplier(**payload.model_dump()); db.add(obj)
    try: db.commit(); db.refresh(obj)
    except IntegrityError: db.rollback(); raise HTTPException(409, "Supplier name already exists")
    return obj
@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)): return db.scalars(select(Supplier).order_by(Supplier.supplier_id)).all()
@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    obj = db.get(Supplier, supplier_id)
    if not obj: raise HTTPException(404, "Supplier not found")
    return obj
