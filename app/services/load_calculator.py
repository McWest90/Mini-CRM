from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models


def calculate_operator_load(db: Session, operator_id: int) -> int:
    """
    Рассчитать текущую нагрузку оператора
    Нагрузка = количество активных обращений (status != 'closed')
    """
    load = db.query(func.count(models.Contact.id)).filter(
        models.Contact.operator_id == operator_id,
        models.Contact.status != 'closed'
    ).scalar()
    
    return load or 0


def get_operator_load_info(db: Session, operator_id: int) -> dict:
    """Получить информацию о нагрузке оператора"""
    operator = db.query(models.Operator).get(operator_id)
    if not operator:
        return None
    
    current_load = calculate_operator_load(db, operator_id)
    
    return {
        'operator_id': operator_id,
        'operator_name': operator.name,
        'current_load': current_load,
        'max_load': operator.max_load,
        'is_available': current_load < operator.max_load and operator.is_active
    }