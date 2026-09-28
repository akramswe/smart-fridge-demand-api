from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Product, Sale


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_product(client):
    created = client.post(
        "/api/products",
        json={"name": "Vegan Bowl", "category": "Main"},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Vegan Bowl"

    listed = client.get("/api/products")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_product_analytics(client, db_session):
    product = Product(name="Pasta", category="Main")
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    start = date(2026, 1, 1)
    for offset, sold in enumerate([10, 12, 14]):
        db_session.add(
            Sale(
                product_id=product.id,
                sale_date=start + timedelta(days=offset),
                quantity_sold=sold,
                waste_quantity=2,
            )
        )
    db_session.commit()

    response = client.get(f"/api/products/{product.id}/analytics")
    assert response.status_code == 200

    payload = response.json()
    assert payload["days_observed"] == 3
    assert payload["total_quantity_sold"] == 36
    assert payload["average_daily_demand"] == 12.0


def test_forecast_with_history(client, db_session):
    product = Product(name="Salad", category="Salad")
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    start = date(2026, 1, 1)
    for offset in range(40):
        db_session.add(
            Sale(
                product_id=product.id,
                sale_date=start + timedelta(days=offset),
                quantity_sold=25 + (offset % 7),
                waste_quantity=1,
            )
        )
    db_session.commit()

    response = client.post(
        "/api/forecast",
        json={
            "product_id": product.id,
            "target_date": "2026-02-15",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["predicted_demand"] >= 0
    assert payload["training_samples"] >= 14
    assert payload["model"] == "RandomForestRegressor"
