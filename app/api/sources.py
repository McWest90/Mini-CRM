from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("/", response_model=schemas.Source)
def create_source(
    source: schemas.SourceCreate,
    db: Session = Depends(get_db)
):
    """Создать новый источник"""
    db_source = crud.get_source_by_code(db, code=source.code)
    if db_source:
        raise HTTPException(status_code=400, detail="Source already exists")
    return crud.create_source(db=db, source=source)


@router.get("/", response_model=List[schemas.Source])
def read_sources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список источников"""
    return crud.get_sources(db, skip=skip, limit=limit)


@router.get("/{source_id}", response_model=schemas.Source)
def read_source(source_id: int, db: Session = Depends(get_db)):
    """Получить источник по ID"""
    db_source = crud.get_source(db, source_id=source_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source


@router.get("/{source_id}/operators")
def get_source_operators(source_id: int, db: Session = Depends(get_db)):
    """Получить операторов для источника с их весами"""
    source = crud.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    operators_with_weights = []
    for weight in source.operator_weights:
        operators_with_weights.append({
            "operator_id": weight.operator_id,
            "operator_name": weight.operator.name,
            "weight": weight.weight,
            "is_active": weight.operator.is_active
        })
    
    return {
        "source_id": source_id,
        "source_name": source.name,
        "operators": operators_with_weights
    }