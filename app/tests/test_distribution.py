import pytest
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.distribution import DistributionService
from app.services.load_calculator import calculate_operator_load
from app import crud, schemas


def test_distribution_service(client):
    """Тест сервиса распределения"""
    # Используем клиент для создания тестовых данных
    # Создаем оператора
    operator_response = client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 3}
    )
    operator_id = operator_response.json()["id"]
    
    # Создаем источник
    source_response = client.post(
        "/sources/",
        json={"name": "Test Source", "code": "test_source"}
    )
    source_id = source_response.json()["id"]
    
    # Создаем лида
    lead_response = client.post(
        "/leads/",
        json={
            "external_id": "test_lead",
            "phone": "+79123456789",
            "email": "test@example.com"
        }
    )
    lead_id = lead_response.json()["id"]
    
    # Получаем базу данных для прямого тестирования сервиса
    db = next(get_db())
    
    # Проверяем, что оператор доступен
    available_operators = DistributionService.get_available_operators_for_source(db, source_id)
    assert len(available_operators) == 0  # Нет весов для оператора
    
    # Назначаем вес оператору
    from app.models import OperatorSourceWeight
    weight = OperatorSourceWeight(
        operator_id=operator_id,
        source_id=source_id,
        weight=10
    )
    db.add(weight)
    db.commit()
    
    # Теперь оператор должен быть доступен
    available_operators = DistributionService.get_available_operators_for_source(db, source_id)
    assert len(available_operators) == 1
    assert available_operators[0].id == operator_id
    
    # Тестируем распределение
    contact = DistributionService.distribute_contact(
        db=db,
        lead_id=lead_id,
        source_id=source_id,
        message="Test message"
    )
    
    assert contact is not None
    assert contact.operator_id == operator_id
    assert contact.status == "new"
    
    # Проверяем нагрузку оператора
    load = calculate_operator_load(db, operator_id)
    assert load == 1


def test_distribution_with_multiple_operators(client):
    """Тест распределения между несколькими операторами"""
    # Создаем операторов
    operator1_response = client.post(
        "/operators/",
        json={"name": "Operator 1", "email": "op1@example.com", "max_load": 10}
    )
    operator1_id = operator1_response.json()["id"]
    
    operator2_response = client.post(
        "/operators/",
        json={"name": "Operator 2", "email": "op2@example.com", "max_load": 10}
    )
    operator2_id = operator2_response.json()["id"]
    
    # Создаем источник
    source_response = client.post(
        "/sources/",
        json={"name": "Test Source", "code": "test_source"}
    )
    source_id = source_response.json()["id"]
    
    # Создаем лида
    lead_response = client.post(
        "/leads/",
        json={
            "external_id": "test_lead",
            "phone": "+79123456789"
        }
    )
    lead_id = lead_response.json()["id"]
    
    db = next(get_db())
    
    # Назначаем веса операторам
    from app.models import OperatorSourceWeight
    
    weight1 = OperatorSourceWeight(
        operator_id=operator1_id,
        source_id=source_id,
        weight=30  # 75% трафика
    )
    weight2 = OperatorSourceWeight(
        operator_id=operator2_id,
        source_id=source_id,
        weight=10  # 25% трафика
    )
    
    db.add(weight1)
    db.add(weight2)
    db.commit()
    
    # Создаем несколько обращений для проверки распределения
    operator_counts = {operator1_id: 0, operator2_id: 0}
    
    for _ in range(100):
        contact = DistributionService.distribute_contact(
            db=db,
            lead_id=lead_id,
            source_id=source_id,
            message=f"Test message {_}"
        )
        if contact and contact.operator_id:
            operator_counts[contact.operator_id] += 1
    
    # Проверяем, что оба оператора получили обращения
    assert operator_counts[operator1_id] > 0
    assert operator_counts[operator2_id] > 0
    
    # Примерное распределение должно быть около 75%/25%
    ratio = operator_counts[operator1_id] / (operator_counts[operator1_id] + operator_counts[operator2_id])
    # Допускаем погрешность 10%
    assert 0.65 <= ratio <= 0.85


def test_distribution_with_operator_overload(client):
    """Тест распределения при перегрузке оператора"""
    # Создаем оператора с низким лимитом
    operator_response = client.post(
        "/operators/",
        json={"name": "Busy Operator", "email": "busy@example.com", "max_load": 1}
    )
    operator_id = operator_response.json()["id"]
    
    # Создаем источник
    source_response = client.post(
        "/sources/",
        json={"name": "Test Source", "code": "test_source"}
    )
    source_id = source_response.json()["id"]
    
    # Создаем лидов
    lead1_response = client.post(
        "/leads/",
        json={
            "external_id": "lead1",
            "phone": "+79123456781"
        }
    )
    lead1_id = lead1_response.json()["id"]
    
    lead2_response = client.post(
        "/leads/",
        json={
            "external_id": "lead2",
            "phone": "+79123456782"
        }
    )
    lead2_id = lead2_response.json()["id"]
    
    db = next(get_db())
    
    # Назначаем вес оператору
    from app.models import OperatorSourceWeight
    weight = OperatorSourceWeight(
        operator_id=operator_id,
        source_id=source_id,
        weight=10
    )
    db.add(weight)
    db.commit()
    
    # Первое обращение - должно быть назначено
    contact1 = DistributionService.distribute_contact(
        db=db,
        lead_id=lead1_id,
        source_id=source_id,
        message="First message"
    )
    assert contact1 is not None
    assert contact1.operator_id == operator_id
    
    # Второе обращение - оператор перегружен, должно быть без оператора
    contact2 = DistributionService.distribute_contact(
        db=db,
        lead_id=lead2_id,
        source_id=source_id,
        message="Second message"
    )
    assert contact2 is None  # Нет доступных операторов


def test_close_contact_reduces_load(client):
    """Тест что закрытие обращения уменьшает нагрузку оператора"""
    # Создаем оператора
    operator_response = client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 2}
    )
    operator_id = operator_response.json()["id"]
    
    # Создаем источник
    source_response = client.post(
        "/sources/",
        json={"name": "Test Source", "code": "test_source"}
    )
    source_id = source_response.json()["id"]
    
    # Создаем лида
    lead_response = client.post(
        "/leads/",
        json={
            "external_id": "test_lead",
            "phone": "+79123456789"
        }
    )
    lead_id = lead_response.json()["id"]
    
    db = next(get_db())
    
    # Назначаем вес оператору
    from app.models import OperatorSourceWeight
    weight = OperatorSourceWeight(
        operator_id=operator_id,
        source_id=source_id,
        weight=10
    )
    db.add(weight)
    db.commit()
    
    # Создаем обращение через API
    contact_response = client.post(
        "/contacts/",
        json={
            "source_code": "test_source",
            "external_lead_id": "test_lead",
            "phone": "+79123456789",
            "message": "Test message"
        }
    )
    contact_id = contact_response.json()["contact"]["id"]
    
    # Проверяем нагрузку
    load_response = client.get(f"/operators/{operator_id}/load")
    assert load_response.json()["current_load"] == 1
    
    # Закрываем обращение
    close_response = client.put(f"/contacts/{contact_id}/close")
    assert close_response.status_code == 200
    
    # Проверяем что нагрузка уменьшилась
    load_response = client.get(f"/operators/{operator_id}/load")
    assert load_response.json()["current_load"] == 0


def test_lead_with_multiple_contacts(client):
    """Тест что один лид может иметь несколько обращений из разных источников"""
    # Создаем лида
    lead_response = client.post(
        "/leads/",
        json={
            "external_id": "multi_contact_lead",
            "phone": "+79123456789",
            "first_name": "John"
        }
    )
    lead_id = lead_response.json()["id"]
    
    # Создаем два источника
    source1_response = client.post(
        "/sources/",
        json={"name": "Source 1", "code": "source1"}
    )
    source1_id = source1_response.json()["id"]
    
    source2_response = client.post(
        "/sources/",
        json={"name": "Source 2", "code": "source2"}
    )
    
    # Создаем два обращения для одного лида из разных источников
    client.post(
        "/contacts/",
        json={
            "source_code": "source1",
            "external_lead_id": "multi_contact_lead",
            "phone": "+79123456789",
            "message": "Message from source 1"
        }
    )
    
    client.post(
        "/contacts/",
        json={
            "source_code": "source2",
            "external_lead_id": "multi_contact_lead",
            "phone": "+79123456789",
            "message": "Message from source 2"
        }
    )
    
    # Получаем все обращения лида
    response = client.get(f"/contacts/leads/{lead_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["lead"]["id"] == lead_id
    assert len(data["contacts"]) == 2
    assert len(data["sources"]) == 2