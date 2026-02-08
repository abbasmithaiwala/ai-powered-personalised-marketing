"""Tests for database models"""
import pytest
from uuid import uuid4

from app.models import (
    Brand,
    MenuItem,
    Customer,
    Order,
    OrderItem,
    CustomerPreference,
    IngestionJob,
)


def test_brand_model():
    """Test Brand model can be instantiated"""
    brand = Brand(
        id=uuid4(),
        name="Test Restaurant",
        slug="test-restaurant",
        cuisine_type="Italian",
        is_active=True,
    )
    assert brand.name == "Test Restaurant"
    assert brand.cuisine_type == "Italian"
    assert brand.is_active is True


def test_customer_model():
    """Test Customer model can be instantiated"""
    customer = Customer(
        id=uuid4(),
        external_id="CUST123",
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        city="London",
        total_orders=0,
        total_spend=0,
    )
    assert customer.email == "test@example.com"
    assert customer.external_id == "CUST123"
    assert customer.total_orders == 0


def test_menu_item_model():
    """Test MenuItem model can be instantiated"""
    brand_id = uuid4()
    item = MenuItem(
        id=uuid4(),
        brand_id=brand_id,
        name="Margherita Pizza",
        description="Classic pizza with tomato and mozzarella",
        category="mains",
        cuisine_type="Italian",
        price=12.50,
        dietary_tags=["vegetarian"],
        is_available=True,
    )
    assert item.name == "Margherita Pizza"
    assert item.price == 12.50
    assert "vegetarian" in item.dietary_tags


def test_order_model():
    """Test Order model can be instantiated"""
    from datetime import datetime

    order = Order(
        id=uuid4(),
        external_id="ORD123",
        customer_id=uuid4(),
        brand_id=uuid4(),
        order_date=datetime.now(),
        total_amount=25.50,
        channel="online",
    )
    assert order.external_id == "ORD123"
    assert order.total_amount == 25.50


def test_order_item_model():
    """Test OrderItem model can be instantiated"""
    item = OrderItem(
        id=uuid4(),
        order_id=uuid4(),
        menu_item_id=uuid4(),
        item_name="Margherita Pizza",
        quantity=2,
        unit_price=12.50,
        subtotal=25.00,
    )
    assert item.item_name == "Margherita Pizza"
    assert item.quantity == 2
    assert item.subtotal == 25.00


def test_customer_preference_model():
    """Test CustomerPreference model can be instantiated"""
    pref = CustomerPreference(
        id=uuid4(),
        customer_id=uuid4(),
        favorite_cuisines={"italian": 0.8, "thai": 0.6},
        favorite_categories={"mains": 0.9, "desserts": 0.5},
        dietary_flags={"vegetarian": True},
        price_sensitivity="medium",
        order_frequency="weekly",
        version=1,
    )
    assert pref.favorite_cuisines["italian"] == 0.8
    assert pref.dietary_flags["vegetarian"] is True
    assert pref.price_sensitivity == "medium"


def test_ingestion_job_model():
    """Test IngestionJob model can be instantiated"""
    job = IngestionJob(
        id=uuid4(),
        filename="orders.csv",
        csv_type="orders",
        status="pending",
        total_rows=100,
        processed_rows=0,
        failed_rows=0,
    )
    assert job.filename == "orders.csv"
    assert job.status == "pending"
    assert job.total_rows == 100
