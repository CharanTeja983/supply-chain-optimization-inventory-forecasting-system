from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Product, StockTransaction, DemandRecord
from app.schemas.schemas import StockTransactionCreate, StockTransactionOut, DemandCreate, DemandOut

router = APIRouter(tags=["Stock and Demand"])
@router.post("/stock-transactions", response_model=StockTransactionOut, status_code=201)
def create_transaction(payload: StockTransactionCreate, db: Session = Depends(get_db)):
    if not db.get(Product, payload.product_id): raise HTTPException(404, "Product not found")
    obj = StockTransaction(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.get("/stock-transactions", response_model=list[StockTransactionOut])
def list_transactions(product_id: int | None = None, db: Session = Depends(get_db)):
    query = select(StockTransaction).order_by(StockTransaction.transaction_date.desc())
    if product_id is not None: query = query.where(StockTransaction.product_id == product_id)
    return db.scalars(query).all()
@router.post("/demand-records", response_model=DemandOut, status_code=201)
def create_demand(payload: DemandCreate, db: Session = Depends(get_db)):
    if not db.get(Product, payload.product_id): raise HTTPException(404, "Product not found")
    obj = DemandRecord(**payload.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj
@router.get("/demand-records", response_model=list[DemandOut])
def list_demand(product_id: int | None = None, db: Session = Depends(get_db)):
    query = select(DemandRecord).order_by(DemandRecord.demand_date.desc())
    if product_id is not None: query = query.where(DemandRecord.product_id == product_id)
    return db.scalars(query).all()
