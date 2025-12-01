from sqlalchemy import (
    Column, Integer, String, Boolean, 
    ForeignKey, DateTime, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Operator(Base):
    """Модель оператора"""
    __tablename__ = "operators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    max_load = Column(Integer, default=10)  # Максимальное количество активных лидов
    
    # Связь с источниками через веса
    source_weights = relationship("OperatorSourceWeight", back_populates="operator", cascade="all, delete-orphan")
    # Обращения, назначенные оператору
    contacts = relationship("Contact", back_populates="operator")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Lead(Base):
    """Модель лида"""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, nullable=False)  # Уникальный идентификатор (телефон, email и т.д.)
    phone = Column(String, nullable=False)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    
    # Все обращения лида
    contacts = relationship("Contact", back_populates="lead", cascade="all, delete-orphan")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Source(Base):
    """Модель источника/бота"""
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)  # Уникальный код источника
    
    # Веса операторов для этого источника
    operator_weights = relationship("OperatorSourceWeight", back_populates="source", cascade="all, delete-orphan")
    # Обращения из этого источника
    contacts = relationship("Contact", back_populates="source")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OperatorSourceWeight(Base):
    """Вес оператора для конкретного источника"""
    __tablename__ = "operator_source_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id", ondelete="CASCADE"))
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"))
    weight = Column(Integer, default=1)  # Вес распределения
    
    # Связи
    operator = relationship("Operator", back_populates="source_weights")
    source = relationship("Source", back_populates="operator_weights")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Contact(Base):
    """Модель обращения/контакта"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"))
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"))
    operator_id = Column(Integer, ForeignKey("operators.id", ondelete="SET NULL"), nullable=True)
    message = Column(String)
    
    # Статус обращения: new, in_progress, closed
    status = Column(String, default="new")
    
    # Время назначения оператора
    assigned_at = Column(DateTime(timezone=True))
    # Время закрытия обращения
    closed_at = Column(DateTime(timezone=True))
    
    # Связи
    lead = relationship("Lead", back_populates="contacts")
    source = relationship("Source", back_populates="contacts")
    operator = relationship("Operator", back_populates="contacts")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())