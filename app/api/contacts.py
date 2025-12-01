from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas, models
from app.database import get_db
from app.services.distribution import DistributionService

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=schemas.ContactResponse)
def create_contact(
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новое обращение
    
    Логика:
    1. Найти или создать лида по external_id
    2. Найти источник по коду
    3. Распределить обращение между операторами
    4. Создать запись об обращении
    """
    
    lead = crud.get_lead_by_external_id(db, contact.external_lead_id)
    if not lead:
        lead_data = schemas.LeadCreate(
            external_id=contact.external_lead_id,
            phone=contact.phone,
            email=contact.email,
            first_name=contact.first_name,
            last_name=contact.last_name
        )
        lead = crud.create_lead(db, lead_data)
    
    source = crud.get_source_by_code(db, contact.source_code)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    distributed_contact = DistributionService.distribute_contact(
        db=db,
        lead_id=lead.id,
        source_id=source.id,
        message=contact.message
    )
    
    if not distributed_contact:
        
        distributed_contact = models.Contact(
            lead_id=lead.id,
            source_id=source.id,
            message=contact.message,
            status="new"
        )
        db.add(distributed_contact)
        db.commit()
        db.refresh(distributed_contact)
    
    operator = None
    if distributed_contact.operator_id:
        operator = crud.get_operator(db, distributed_contact.operator_id)
    
    return {
        "contact": distributed_contact,
        "operator": operator,
        "lead": lead,
        "source": source
    }


@router.get("/", response_model=List[schemas.Contact])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    operator_id: Optional[int] = None,
    source_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить список обращений"""
    return crud.get_contacts(
        db,
        skip=skip,
        limit=limit,
        operator_id=operator_id,
        source_id=source_id,
        lead_id=lead_id
    )


@router.get("/stats/distribution")
def get_distribution_stats(
    source_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить статистику распределения"""
    stats = DistributionService.calculate_distribution_stats(db, source_id)
    return {"stats": stats}


@router.put("/{contact_id}/close")
def close_contact(contact_id: int, db: Session = Depends(get_db)):
    """Закрыть обращение"""
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.status = "closed"
    contact.closed_at = datetime.now()
    
    db.commit()
    db.refresh(contact)
    
    return contact


@router.get("/leads/{lead_id}")
def get_lead_contacts(lead_id: int, db: Session = Depends(get_db)):
    """Получить все обращения лида"""
    lead = crud.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "lead": lead,
        "contacts": lead.contacts,
        "sources": list(set([contact.source for contact in lead.contacts]))
    }