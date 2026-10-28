from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Product
from app.schemas.schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["Products"])
@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    obj = Product(**payload.model_dump()); db.add(obj)
    try: db.commit(); db.refresh(obj)
    except IntegrityError: db.rollback(); raise HTTPException(409, "SKU already exists")
    return obj
@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)): return db.scalars(select(Product).order_by(Product.product_id)).all()
@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    return obj
@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    obj = db.get(Product, product_id)
    if not obj: raise HTTPException(404, "Product not found")
    db.delete(obj); db.commit()
