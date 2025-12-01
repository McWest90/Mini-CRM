from sqlalchemy.orm import Session
from app import models, schemas
from typing import List, Optional


# Операторы
def get_operator(db: Session, operator_id: int):
    return db.query(models.Operator).filter(models.Operator.id == operator_id).first()


def get_operator_by_email(db: Session, email: str):
    return db.query(models.Operator).filter(models.Operator.email == email).first()


def get_operators(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Operator).offset(skip).limit(limit).all()


def create_operator(db: Session, operator: schemas.OperatorCreate):
    db_operator = models.Operator(
        name=operator.name,
        email=operator.email,
        is_active=operator.is_active,
        max_load=operator.max_load
    )
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator


def update_operator(db: Session, operator_id: int, operator_update: schemas.OperatorUpdate):
    db_operator = get_operator(db, operator_id)
    if not db_operator:
        return None
    
    update_data = operator_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_operator, field, value)
    
    db.commit()
    db.refresh(db_operator)
    return db_operator


# Лиды
def get_lead(db: Session, lead_id: int):
    return db.query(models.Lead).filter(models.Lead.id == lead_id).first()


def get_lead_by_external_id(db: Session, external_id: str):
    return db.query(models.Lead).filter(models.Lead.external_id == external_id).first()


def get_leads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Lead).offset(skip).limit(limit).all()


def create_lead(db: Session, lead: schemas.LeadCreate):
    db_lead = models.Lead(
        external_id=lead.external_id,
        phone=lead.phone,
        email=lead.email,
        first_name=lead.first_name,
        last_name=lead.last_name
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


# Источники
def get_source(db: Session, source_id: int):
    return db.query(models.Source).filter(models.Source.id == source_id).first()


def get_source_by_code(db: Session, code: str):
    return db.query(models.Source).filter(models.Source.code == code).first()


def get_sources(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Source).offset(skip).limit(limit).all()


def create_source(db: Session, source: schemas.SourceCreate):
    db_source = models.Source(
        name=source.name,
        code=source.code
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


# Обращения
def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()


def get_contacts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    operator_id: Optional[int] = None,
    source_id: Optional[int] = None,
    lead_id: Optional[int] = None
):
    query = db.query(models.Contact)
    
    if operator_id is not None:
        query = query.filter(models.Contact.operator_id == operator_id)
    if source_id is not None:
        query = query.filter(models.Contact.source_id == source_id)
    if lead_id is not None:
        query = query.filter(models.Contact.lead_id == lead_id)
    
    return query.offset(skip).limit(limit).all()


def create_contact(db: Session, contact: schemas.ContactCreate):
    db_contact = models.Contact(
        lead_id=contact.lead_id,
        source_id=contact.source_id,
        operator_id=contact.operator_id,
        message=contact.message
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact