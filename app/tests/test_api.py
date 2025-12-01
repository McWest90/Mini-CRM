import pytest
from app.services.load_calculator import calculate_operator_load


def test_create_operator(client):
    """Тест создания оператора"""
    response = client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Operator"
    assert data["email"] == "test@example.com"
    assert data["max_load"] == 5
    assert data["is_active"] is True
    assert "id" in data


def test_get_operators(client):
    """Тест получения списка операторов"""
    # Сначала создаем оператора
    client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 5}
    )
    
    response = client.get("/operators/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["name"] == "Test Operator"


def test_update_operator(client):
    """Тест обновления оператора"""
    # Создаем оператора
    create_response = client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 5}
    )
    operator_id = create_response.json()["id"]
    
    # Обновляем оператора
    update_response = client.put(
        f"/operators/{operator_id}",
        json={"is_active": False, "max_load": 10}
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["is_active"] is False
    assert data["max_load"] == 10


def test_create_source(client):
    """Тест создания источника"""
    response = client.post(
        "/sources/",
        json={"name": "Telegram Bot", "code": "tg_bot"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Telegram Bot"
    assert data["code"] == "tg_bot"
    assert "id" in data


def test_create_lead(client):
    """Тест создания лида"""
    response = client.post(
        "/leads/",
        json={
            "external_id": "user123",
            "phone": "+79123456789",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["external_id"] == "user123"
    assert data["phone"] == "+79123456789"
    assert data["email"] == "user@example.com"


def test_create_contact_with_distribution(client):
    """Тест создания обращения с распределением"""
    # Сначала создаем оператора
    operator_response = client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 5}
    )
    operator_id = operator_response.json()["id"]
    
    # Создаем источник
    source_response = client.post(
        "/sources/",
        json={"name": "Telegram Bot", "code": "tg_bot"}
    )
    source_id = source_response.json()["id"]
    
    # Назначаем вес оператору для источника
    weight_response = client.post(
        f"/operators/{operator_id}/weights",
        json={"source_id": source_id, "weight": 10}
    )
    assert weight_response.status_code == 200
    
    # Создаем обращение
    contact_response = client.post(
        "/contacts/",
        json={
            "source_code": "tg_bot",
            "external_lead_id": "user123",
            "phone": "+79123456789",
            "message": "Hello, I need help"
        }
    )
    assert contact_response.status_code == 200
    data = contact_response.json()
    assert data["contact"]["operator_id"] == operator_id
    assert data["contact"]["status"] == "new"
    assert data["operator"]["id"] == operator_id


def test_get_operator_load(client):
    """Тест получения нагрузки оператора"""
    # Создаем оператора
    operator_response = client.post(
        "/operators/",
        json={"name": "Test Operator", "email": "test@example.com", "max_load": 5}
    )
    operator_id = operator_response.json()["id"]
    
    # Получаем нагрузку
    response = client.get(f"/operators/{operator_id}/load")
    assert response.status_code == 200
    data = response.json()
    assert data["operator_id"] == operator_id
    assert data["current_load"] == 0
    assert data["max_load"] == 5
    assert data["is_available"] is True


def test_contact_without_available_operator(client):
    """Тест создания обращения без доступных операторов"""
    # Создаем неактивного оператора
    operator_response = client.post(
        "/operators/",
        json={"name": "Inactive Operator", "email": "inactive@example.com", "max_load": 5, "is_active": False}
    )
    
    # Создаем источник
    source_response = client.post(
        "/sources/",
        json={"name": "Telegram Bot", "code": "tg_bot"}
    )
    
    # Создаем обращение - должно быть без оператора
    contact_response = client.post(
        "/contacts/",
        json={
            "source_code": "tg_bot",
            "external_lead_id": "user123",
            "phone": "+79123456789",
            "message": "Hello"
        }
    )
    assert contact_response.status_code == 200
    data = contact_response.json()
    assert data["contact"]["operator_id"] is None
    assert data["operator"] is None


def test_get_distribution_stats(client):
    """Тест получения статистики распределения"""
    response = client.get("/contacts/stats/distribution")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert isinstance(data["stats"], list)