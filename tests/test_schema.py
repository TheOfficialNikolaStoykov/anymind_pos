import pytest

from app.database import *
from app.main import *
from app import models
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        # Create engine INSIDE the TestClient context (same event loop)
        test_engine = create_async_engine(
            TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        TestingSessionLocal = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async def override_get_session():
            async with TestingSessionLocal() as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        
        yield c
        
        app.dependency_overrides.clear()



# GraphQL queries/mutations
MAKE_PAYMENT_MUTATION = """
mutation MakePayment(
    $customerId: String!,
    $price: String!,
    $priceModifier: Float!,
    $paymentMethod: String!,
    $datetime: String!,
    $additionalItem: AdditionalItemInput
) {
    makePayment(
        customerId: $customerId,
        price: $price,
        priceModifier: $priceModifier,
        paymentMethod: $paymentMethod,
        datetime: $datetime,
        additionalItem: $additionalItem
    ) {
        ... on PaymentResponse {
            finalPrice
            points
        }
        ... on ErrorResponse {
            error
        }
    }
}
"""

SALES_REPORT_QUERY = """
query SalesReport($startDatetime: String!, $endDatetime: String!) {
    salesReport(startDatetime: $startDatetime, endDatetime: $endDatetime) {
        datetime
        sales
        points
    }
}
"""


def test_make_payment_cash(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.95,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "95.00"
    assert result["points"] == 5

def test_make_payment_cash_on_delivery(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH_ON_DELIVERY",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"courier": "YAMATO"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "100.00"
    assert result["points"] == 5

def test_make_payment_visa(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.95,
                "paymentMethod": "VISA",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"last4": "1234"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "95.00"
    assert result["points"] == 3


def test_make_payment_mastercard(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.95,
                "paymentMethod": "MASTERCARD",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"last4": "5678"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "95.00"
    assert result["points"] == 3


def test_make_payment_amex(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.98,
                "paymentMethod": "AMEX",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"last4": "9012"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "98.00"
    assert result["points"] == 2


def test_make_payment_jcb(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.95,
                "paymentMethod": "JCB",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"last4": "3456"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "95.00"
    assert result["points"] == 5


def test_make_payment_line_pay(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "LINE_PAY",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "100.00"
    assert result["points"] == 1


def test_make_payment_paypay(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "PAYPAY",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "100.00"
    assert result["points"] == 1


def test_make_payment_points(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "POINTS",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "100.00"
    assert result["points"] == 0


def test_make_payment_grab_pay(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "GRAB_PAY",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "100.00"
    assert result["points"] == 1

def test_make_payment_bank_transfer(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "500.00",
                "priceModifier": 1.0,
                "paymentMethod": "BANK_TRANSFER",
                "datetime": "2022-09-01T10:00:00Z",
                "additionalItem": {"bank": "Chase", "accountNumber": "123456789"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "500.00"
    assert result["points"] == 0


def test_make_payment_cheque(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.90,
                "paymentMethod": "CHEQUE",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"bank": "Chase", "chequeNumber": "12345678"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "90.00"
    assert result["points"] == 0


def test_make_payment_invalid_method(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "BITCOIN",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_modifier_out_of_range(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.5,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_visa_missing_last4(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.98,
                "paymentMethod": "VISA",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_visa_invalid_last4(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.98,
                "paymentMethod": "VISA",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"last4": "12AB"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_cod_invalid_courier(client):
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH_ON_DELIVERY",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": {"courier": "UPS"}
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    result = data["data"]["makePayment"]
    assert "error" in result

def test_sales_report(client):
    response = client.post(
        "/graphql",
        json={
            "query": SALES_REPORT_QUERY,
            "variables": {
                "startDatetime": "2022-09-01T00:00:00Z",
                "endDatetime": "2022-09-01T23:59:59Z"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data, f"GraphQL errors: {data.get('errors')}"
    assert "salesReport" in data["data"]

def test_make_payment_cash_max_modifier(client):
    """Test CASH with maximum allowed price modifier"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "100.00"


def test_make_payment_negative_price(client):
    """Test with negative price"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "-100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_zero_price(client):
    """Test with zero price"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "0.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "0.00"
    assert result["points"] == 0


def test_make_payment_invalid_price_format(client):
    """Test with invalid price format"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "abc",
                "priceModifier": 1.0,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_empty_customer_id(client):
    """Test with empty customer ID"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_invalid_datetime(client):
    """Test with invalid datetime format"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH",
                "datetime": "not-a-date",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_cod_missing_courier(client):
    """Test CASH_ON_DELIVERY without courier"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "CASH_ON_DELIVERY",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert "error" in result


def test_make_payment_bank_transfer_missing_fields(client):
    """Test BANK_TRANSFER without required fields"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 1.0,
                "paymentMethod": "BANK_TRANSFER",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    result = data["data"]["makePayment"]
    assert "error" in result

def test_sales_report_empty_range(client):
    """Test sales report with no payments in range"""
    response = client.post(
        "/graphql",
        json={
            "query": SALES_REPORT_QUERY,
            "variables": {
                "startDatetime": "2020-01-01T00:00:00Z",
                "endDatetime": "2020-01-01T23:59:59Z"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    assert data["data"]["salesReport"] == []


def test_sales_report_invalid_date_range(client):
    """Test sales report with end before start"""
    response = client.post(
        "/graphql",
        json={
            "query": SALES_REPORT_QUERY,
            "variables": {
                "startDatetime": "2022-09-02T00:00:00Z",
                "endDatetime": "2022-09-01T00:00:00Z"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert "Start date must be before end date" in data["errors"][0]["message"]


def test_sales_report_invalid_datetime_format(client):
    """Test sales report with invalid datetime"""
    response = client.post(
        "/graphql",
        json={
            "query": SALES_REPORT_QUERY,
            "variables": {
                "startDatetime": "invalid",
                "endDatetime": "2022-09-01T23:59:59Z"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    # Should contain an error
    assert "errors" in data or "error" in str(data)

def test_make_payment_modifier_at_lower_bound(client):
    """Test with modifier at exact lower bound"""
    response = client.post(
        "/graphql",
        json={
            "query": MAKE_PAYMENT_MUTATION,
            "variables": {
                "customerId": "12345",
                "price": "100.00",
                "priceModifier": 0.90,  # Assuming CASH lower bound is 0.90
                "paymentMethod": "CASH",
                "datetime": "2022-09-01T00:00:00Z",
                "additionalItem": None
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    result = data["data"]["makePayment"]
    assert result["finalPrice"] == "90.00"