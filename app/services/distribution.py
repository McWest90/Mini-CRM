import random
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app import models
from app.services.load_calculator import calculate_operator_load


class DistributionService:
    """Сервис распределения обращений"""
    
    @staticmethod
    def distribute_contact(
        db: Session,
        lead_id: int,
        source_id: int,
        message: Optional[str] = None
    ) -> Optional[models.Contact]:
        """
        Распределить обращение между операторами
        
        Алгоритм:
        1. Получить всех операторов для источника с их весами
        2. Отфильтровать только активных операторов, не превысивших лимит
        3. Если нет доступных операторов - создать обращение без оператора
        4. Среди доступных выбрать оператора с вероятностью, пропорциональной весу
        """
        
        # Получаем веса операторов для источника
        weights = db.query(models.OperatorSourceWeight).filter(
            models.OperatorSourceWeight.source_id == source_id
        ).all()
        
        if not weights:
            # Нет операторов для этого источника
            return None
        
        # Получаем доступных операторов
        available_operators = []
        total_weight = 0
        
        for weight in weights:
            operator = weight.operator
            
            # Проверяем активность и нагрузку
            if operator.is_active:
                current_load = calculate_operator_load(db, operator.id)
                if current_load < operator.max_load:
                    available_operators.append({
                        'operator': operator,
                        'weight': weight.weight,
                        'current_load': current_load
                    })
                    total_weight += weight.weight
        
        if not available_operators:
            # Нет доступных операторов
            return None
        
        # Выбираем оператора с вероятностью, пропорциональной весу
        if total_weight == 0:
            # Все веса равны 0, выбираем случайного
            chosen = random.choice(available_operators)
        else:
            # Взвешенный случайный выбор
            rand_val = random.uniform(0, total_weight)
            cumulative = 0
            
            for op_info in available_operators:
                cumulative += op_info['weight']
                if rand_val <= cumulative:
                    chosen = op_info
                    break
            else:
                chosen = available_operators[-1]
        
        # Создаем обращение
        contact = models.Contact(
            lead_id=lead_id,
            source_id=source_id,
            operator_id=chosen['operator'].id,
            message=message,
            status="new",
            assigned_at=datetime.now()
        )
        
        db.add(contact)
        db.commit()
        db.refresh(contact)
        
        return contact
    
    @staticmethod
    def get_available_operators_for_source(
        db: Session,
        source_id: int
    ) -> List[models.Operator]:
        """Получить доступных операторов для источника"""
        
        weights = db.query(models.OperatorSourceWeight).filter(
            models.OperatorSourceWeight.source_id == source_id
        ).all()
        
        available_operators = []
        
        for weight in weights:
            operator = weight.operator
            
            if operator.is_active:
                current_load = calculate_operator_load(db, operator.id)
                if current_load < operator.max_load:
                    available_operators.append(operator)
        
        return available_operators
    
    @staticmethod
    def calculate_distribution_stats(
        db: Session,
        source_id: Optional[int] = None
    ) -> List:
        """Рассчитать статистику распределения"""
        
        query = db.query(
            models.Operator.id.label('operator_id'),
            models.Operator.name.label('operator_name'),
            models.Source.id.label('source_id'),
            models.Source.name.label('source_name'),
            models.OperatorSourceWeight.weight,
            func.count(models.Contact.id).label('contact_count'),
            func.sum(case(
                [(models.Contact.operator_id.isnot(None), 1)],
                else_=0
            )).label('assigned_count')
        ).join(
            models.OperatorSourceWeight,
            models.Operator.id == models.OperatorSourceWeight.operator_id
        ).join(
            models.Source,
            models.Source.id == models.OperatorSourceWeight.source_id
        ).outerjoin(
            models.Contact,
            (models.Contact.operator_id == models.Operator.id) &
            (models.Contact.source_id == models.Source.id)
        )
        
        if source_id:
            query = query.filter(models.Source.id == source_id)
        
        stats = query.group_by(
            models.Operator.id,
            models.Source.id,
            models.OperatorSourceWeight.weight
        ).all()
        
        return stats