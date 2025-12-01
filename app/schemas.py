from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr


# Операторы
class OperatorBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True
    max_load: int = 10


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    max_load: Optional[int] = None


class Operator(OperatorBase):
    id: int
    current_load: int = 0  # Текущая нагрузка (вычисляемое поле)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Лиды
class LeadBase(BaseModel):
    external_id: str  # Уникальный идентификатор (телефон или email)
    phone: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class Lead(LeadBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Источники
class SourceBase(BaseModel):
    name: str
    code: str


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Веса операторов
class OperatorWeightBase(BaseModel):
    operator_id: int
    source_id: int
    weight: int = 1


class OperatorWeightCreate(OperatorWeightBase):
    pass


class OperatorWeightUpdate(BaseModel):
    weight: int


class OperatorWeight(OperatorWeightBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Обращения
class ContactBase(BaseModel):
    lead_id: Optional[int] = None
    source_code: str  # Код источника
    external_lead_id: str  # Внешний ID лида
    phone: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    message: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class Contact(BaseModel):
    id: int
    lead_id: int
    source_id: int
    operator_id: Optional[int] = None
    status: str
    message: Optional[str] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContactResponse(BaseModel):
    contact: Contact
    operator: Optional[Operator] = None
    lead: Lead
    source: Source


# Статистика
class DistributionStats(BaseModel):
    operator_id: int
    operator_name: str
    source_id: int
    source_name: str
    contact_count: int
    assigned_count: int
    weight: int


class LoadInfo(BaseModel):
    operator_id: int
    operator_name: str
    current_load: int
    max_load: int
    is_available: bool