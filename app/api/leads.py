from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/", response_model=schemas.Lead)
def create_lead(
    lead: schemas.LeadCreate,
    db: Session = Depends(get_db)
):
    """Создать нового лида"""
    db_lead = crud.get_lead_by_external_id(db, external_id=lead.external_id)
    if db_lead:
        raise HTTPException(status_code=400, detail="Lead already exists")
    return crud.create_lead(db=db, lead=lead)


@router.get("/", response_model=List[schemas.Lead])
def read_leads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список лидов"""
    return crud.get_leads(db, skip=skip, limit=limit)


@router.get("/{lead_id}", response_model=schemas.Lead)
def read_lead(lead_id: int, db: Session = Depends(get_db)):
    """Получить лида по ID"""
    db_lead = crud.get_lead(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return db_lead