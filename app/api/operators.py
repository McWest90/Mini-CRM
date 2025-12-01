from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db
from app.services.load_calculator import calculate_operator_load

router = APIRouter(prefix="/operators", tags=["operators"])


@router.post("/", response_model=schemas.Operator)
def create_operator(
    operator: schemas.OperatorCreate,
    db: Session = Depends(get_db)
):
    """Создать нового оператора"""
    db_operator = crud.get_operator_by_email(db, email=operator.email)
    if db_operator:
        raise HTTPException(status_code=400, detail="Operator already exists")
    return crud.create_operator(db=db, operator=operator)


@router.get("/", response_model=List[schemas.Operator])
def read_operators(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Получить список операторов"""
    operators = crud.get_operators(db, skip=skip, limit=limit)
    
    if active_only:
        operators = [op for op in operators if op.is_active]
    
    result = []
    for operator in operators:
        op_dict = operator.__dict__.copy()
        op_dict['current_load'] = calculate_operator_load(db, operator.id)
        result.append(schemas.Operator(**op_dict))
    
    return result


@router.get("/{operator_id}", response_model=schemas.Operator)
def read_operator(operator_id: int, db: Session = Depends(get_db)):
    """Получить оператора по ID"""
    db_operator = crud.get_operator(db, operator_id=operator_id)
    if db_operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    op_dict = db_operator.__dict__.copy()
    op_dict['current_load'] = calculate_operator_load(db, operator_id)
    
    return schemas.Operator(**op_dict)


@router.put("/{operator_id}", response_model=schemas.Operator)
def update_operator(
    operator_id: int,
    operator_update: schemas.OperatorUpdate,
    db: Session = Depends(get_db)
):
    """Обновить оператора"""
    db_operator = crud.update_operator(db, operator_id, operator_update)
    if db_operator is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    op_dict = db_operator.__dict__.copy()
    op_dict['current_load'] = calculate_operator_load(db, operator_id)
    
    return schemas.Operator(**op_dict)


@router.post("/{operator_id}/weights", response_model=schemas.OperatorWeight)
def add_operator_weight(
    operator_id: int,
    weight: schemas.OperatorWeightCreate,
    db: Session = Depends(get_db)
):
    """Добавить/обновить вес оператора для источника"""
    operator = crud.get_operator(db, operator_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    source = crud.get_source(db, weight.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    existing = db.query(models.OperatorSourceWeight).filter(
        models.OperatorSourceWeight.operator_id == operator_id,
        models.OperatorSourceWeight.source_id == weight.source_id
    ).first()
    
    if existing:
        existing.weight = weight.weight
    else:
        existing = models.OperatorSourceWeight(
            operator_id=operator_id,
            source_id=weight.source_id,
            weight=weight.weight
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    return existing


@router.get("/{operator_id}/load", response_model=schemas.LoadInfo)
def get_operator_load(operator_id: int, db: Session = Depends(get_db)):
    """Получить информацию о нагрузке оператора"""
    from app.services.load_calculator import get_operator_load_info
    
    load_info = get_operator_load_info(db, operator_id)
    if not load_info:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    return load_info