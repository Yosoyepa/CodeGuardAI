"""
Tests for main FastAPI application
"""
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "service" in data


def test_root_endpoint():
    """Test root endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert data["docs"] == "/docs"


def test_docs_endpoint_accessible():
    """Test Swagger docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
