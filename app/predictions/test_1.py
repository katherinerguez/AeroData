from fastapi.testclient import TestClient
from main import app
import pytest
import pandas as pd 

client = TestClient(app)

# Fixture para mock de datos (se ejecuta una vez para todos los tests)
@pytest.fixture
def mock_flights(monkeypatch):
    """Mock de la función get_flights para todas las pruebas"""
    def mock_get_flights():
        return pd.DataFrame({
            "departure_airport_name": ["Test Airport"],
            "arrival_airport_name": ["Test Destination"],
            "airline_name": ["Test Airline"],
            "op_carrier_fl_num": ["123"],
            "flight_status": ["scheduled"],
            "distance": [500],
            "predicted_delay": [0],
            "scheduled_dep": ["2023-01-01 12:00:00"],  # Campo necesario
            "scheduled_dep_time": ["12:00"],  # Campo necesario
            "scheduled_arr_time": ["14:00"],  # Campo necesario
            "flight_date": ["2023-01-01"]  # Campo necesario
        })
    monkeypatch.setattr("main.get_flights", mock_get_flights)


def test_show_search_form():
    """Test básico para el endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    assert "form" in response.text.lower()

def test_search_basic(mock_flights):  # Usa el fixture mock_flights
    """Test combinado de búsqueda con y sin parámetros"""
    # Test sin parámetros
    response_empty = client.post("/search")
    assert response_empty.status_code == 200
    
    # Test con parámetros mínimos
    response_with_params = client.post("/search", data={
        "origin_airport_id": "Test Airport"
    })
    assert response_with_params.status_code == 200
    assert "Test Airport" in response_with_params.text

def test_about_page():
    """Test simplificado para about"""
    response = client.get("/about")
    assert response.status_code == 200
