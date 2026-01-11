# AnyMind POS - Payment Processing API

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![GraphQL](https://img.shields.io/badge/-GraphQL-E10098?style=for-the-badge&logo=graphql&logoColor=white)  ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white) ![Pytest](https://img.shields.io/badge/pytest-%23ffffff.svg?style=for-the-badge&logo=pytest&logoColor=2f9fe3)
<br>
![Tests](https://github.com//TheOfficialNikolaStoykov/anymind_pos/actions/workflows/test.yml/badge.svg) 
<br>

A GraphQL-based payment processing system built with FastAPI and Strawberry GraphQL.


## Overview

This project implements a Point of Sale (POS) payment processing API that handles multiple payment methods, calculates final prices with modifiers, awards loyalty points, and provides sales reporting functionality.

<br>

## Functional Requirements

1. **Payment Processing**
   - Accept payments with customer ID, price, price modifier, payment method, datetime, and optional additional items
   - Calculate final price based on price modifier
   - Calculate and award loyalty points based on payment method
   - Validate price modifier is within allowed range for each payment method
   - Validate and store additional items based on payment method (last 4 digits for cards, courier for COD, bank details for transfers, etc.)
   - Return final price and points on success, or error message on failure

2. **Payment Method Validation**
   - CASH: modifier 0.9–1.0, 5% points
   - CASH_ON_DELIVERY: modifier 1.0–1.02, 5% points, must include courier (YAMATO or SAGAWA only)
   - VISA/MASTERCARD/JCB: modifier 0.95–1.0, 3%/3%/5% points, must include last 4 digits
   - AMEX: modifier 0.98–1.01, 2% points, must include last 4 digits
   - LINE_PAY/PAYPAY/GRAB_PAY: modifier exactly 1.0, 1% points
   - POINTS: modifier exactly 1.0, 0 points
   - BANK_TRANSFER: modifier exactly 1.0, 0 points, must include bank and account number
   - CHEQUE: modifier 0.9–1.0, 0 points, must include bank and cheque number

3. **Sales Reporting**
   - Query sales within a date range
   - Aggregate results by hour
   - Return datetime, total sales, and total points for each hour

4. **API Design**
   - Must use GraphQL or gRPC

<br>

## Non-Functional Requirements

1. **Database** - Must use PostgreSQL
2. **Version Control** - Must use Git
3. **Code Quality** - Clear, readable code with good practices and patterns
4. **Error Handling** - API must handle incorrect/invalid data gracefully
5. **Architecture** - Must be extendable, testable, and scalable for new payment methods
6. **Execution** - System must be easy to launch (Docker)
7. **Concurrency** - Must handle many concurrent requests (consider multi-threading, multiple servers)
8. **Testing** - System must include tests
9. **Documentation** - Must include instructions for launching the server

<br>

### Python Dependencies

- FastAPI - Web framework
- Strawberry GraphQL - GraphQL library
- SQLAlchemy - ORM with async support
- asyncpg - Async PostgreSQL driver
- Uvicorn - ASGI server
- pytest & pytest-asyncio - Testing framework

<br>

## Architecture

```
┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │
│  GraphQL API    │◄───────►│   PostgreSQL    │
│  (FastAPI +     │         │   Database      │
│   Strawberry)   │         │                 │
└─────────────────┘         └─────────────────┘
        │
        ▼
┌─────────────────┐
│ Payment Methods │
│ Validation &    │
│ Calculation     │
└─────────────────┘
```

<br>

The application follows a layered architecture:

1. **GraphQL Layer** - Handles incoming mutations and queries via Strawberry GraphQL
2. **Business Logic Layer** - Payment validation and calculation logic
3. **Data Layer** - SQLAlchemy ORM models and async database sessions

<br><br>

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point, mounts GraphQL router
│   ├── schema.py            # GraphQL schema definitions (Query, Mutation, types)
│   ├── models.py            # SQLAlchemy ORM models (Payment table)
│   ├── database.py          # Database connection and async session configuration
│   └── payment_methods.py   # Payment method validation rules and calculation logic
├── tests/
│   ├── __init__.py
│   ├── test_payments.py     # Unit tests for payment mutations
│   └── test_sales_report.py # Unit tests for sales report queries
├── docker-compose.yaml      # Docker services configuration (app + PostgreSQL)
├── Dockerfile               # Container build instructions
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (database credentials)
└── README.md
```

<br>

### File Descriptions

| File | Description |
|------|-------------|
| `app/main.py` | Application entry point. Initializes FastAPI, mounts the GraphQL endpoint at `/graphql`, and creates database tables on startup. |
| `app/schema.py` | Defines GraphQL schema using Strawberry. Contains `Mutation` class for `makePayment` and `Query` class for `salesReport`. Includes response types (`PaymentResponse`, `ErrorResponse`, `SalesEntry`). |
| `app/models.py` | SQLAlchemy model for the `payments` table. Stores customer ID, price, modifier, final price, points, payment method, datetime, and additional metadata. |
| `app/database.py` | Configures async SQLAlchemy engine and session factory. Reads database credentials from environment variables. |
| `app/payment_methods.py` | Contains payment method configuration including valid price modifier ranges, point calculation rates, and required additional fields (e.g., `last4` for cards, `courier` for delivery). |

<br><br>

## Payment Methods

| Method | Modifier Range | Points Rate | Required Fields |
|--------|---------------|-------------|-----------------|
| CASH | 0.9 - 1.0 | 0.05 | - |
| CASH_ON_DELIVERY | 1.0 - 1.02 | 0.05 | `courier` |
| VISA | 0.95 - 1.0 | 0.03 | `last4` |
| MASTERCARD | 0.95 - 1.0 | 0.03 | `last4` |
| AMEX | 0.98 - 1.01 | 0.02 | `last4` |
| JCB | 0.95 - 1.0 | 0.05 | `last4` |
| LINE_PAY | 1.0 | 0.01 | - |
| PAYPAY | 1.0 | 0.01 | - |
| POINTS | 1.0 | 0 | - |
| GRAB_PAY | 1.0 | 0.01 | - |
| BANK_TRANSFER | 1.0 | 0 | `bank`, `accountNumber` |
| CHEQUE | 0.9 - 1.0 | 0 | `bank`, `chequeNumber` |

<br><br>

## API Usage

### GraphQL Endpoint

Access the GraphQL Playground at: `http://localhost:8080/graphql`

<br><br>

### Make Payment Mutation

```graphql
mutation {
  makePayment(
    customerId: "12345"
    price: "100.00"
    priceModifier: 0.95
    paymentMethod: "MASTERCARD"
    datetime: "2022-09-01T12:00:00Z"
    additionalItem: {
      last4: "1234"
    }
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
```

<br><br>

### Sales Report Query

```graphql
query {
  salesReport(
    startDatetime: "2022-09-01T00:00:00Z"
    endDatetime: "2022-09-30T23:59:59Z"
  ) {
    datetime
    sales
    points
  }
}
```

<br><br>

### Tests

The project includes comprehensive unit tests using `pytest` and `pytest-asyncio` with an in-memory SQLite database for isolation.

### Test Categories

**Payment Method Tests** - Valid payments for each payment method:
- `test_make_payment_cash` - CASH payment with 0.95 modifier
- `test_make_payment_cash_on_delivery` - COD with YAMATO courier
- `test_make_payment_visa` - VISA with last4 digits
- `test_make_payment_mastercard` - MASTERCARD with last4 digits
- `test_make_payment_amex` - AMEX with last4 digits
- `test_make_payment_jcb` - JCB with last4 digits
- `test_make_payment_line_pay` - LINE_PAY payment
- `test_make_payment_paypay` - PAYPAY payment
- `test_make_payment_points` - POINTS payment (0 points earned)
- `test_make_payment_grab_pay` - GRAB_PAY payment
- `test_make_payment_bank_transfer` - Bank transfer with bank and account number
- `test_make_payment_cheque` - Cheque with bank and cheque number

**Price Modifier Validation Tests:**
- `test_make_payment_cash_max_modifier` - CASH with maximum allowed modifier (1.0)
- `test_make_payment_modifier_at_lower_bound` - Modifier at exact lower bound (0.90)
- `test_make_payment_modifier_out_of_range` - Modifier outside allowed range

**Price Validation Tests:**
- `test_make_payment_negative_price` - Negative price rejected
- `test_make_payment_zero_price` - Zero price accepted
- `test_make_payment_invalid_price_format` - Non-numeric price rejected

**Additional Fields Validation Tests:**
- `test_make_payment_visa_missing_last4` - VISA without required last4
- `test_make_payment_visa_invalid_last4` - VISA with non-numeric last4
- `test_make_payment_cod_missing_courier` - COD without courier
- `test_make_payment_cod_invalid_courier` - COD with unsupported courier (UPS)
- `test_make_payment_bank_transfer_missing_fields` - Bank transfer without required fields

**Input Validation Tests:**
- `test_make_payment_invalid_method` - Unknown payment method (BITCOIN)
- `test_make_payment_empty_customer_id` - Empty customer ID rejected
- `test_make_payment_invalid_datetime` - Invalid datetime format rejected

**Sales Report Tests:**
- `test_sales_report` - Basic sales report query
- `test_sales_report_empty_range` - Report with no payments in range returns empty list
- `test_sales_report_invalid_date_range` - End date before start date rejected
- `test_sales_report_invalid_datetime_format` - Invalid datetime format rejected
<br>

## Test Results

All 30 tests passing ✅

| Test | Status |
|------|--------|
| `test_make_payment_cash` | ✅ |
| `test_make_payment_cash_on_delivery` | ✅ |
| `test_make_payment_visa` | ✅ |
| `test_make_payment_mastercard` | ✅ |
| `test_make_payment_amex` | ✅ |
| `test_make_payment_jcb` | ✅ |
| `test_make_payment_line_pay` | ✅ |
| `test_make_payment_paypay` | ✅ |
| `test_make_payment_points` | ✅ |
| `test_make_payment_grab_pay` | ✅ |
| `test_make_payment_bank_transfer` | ✅ |
| `test_make_payment_cheque` | ✅ |
| `test_make_payment_invalid_method` | ✅ |
| `test_make_payment_modifier_out_of_range` | ✅ |
| `test_make_payment_visa_missing_last4` | ✅ |
| `test_make_payment_visa_invalid_last4` | ✅ |
| `test_make_payment_cod_invalid_courier` | ✅ |
| `test_sales_report` | ✅ |
| `test_make_payment_cash_max_modifier` | ✅ |
| `test_make_payment_negative_price` | ✅ |
| `test_make_payment_zero_price` | ✅ |
| `test_make_payment_invalid_price_format` | ✅ |
| `test_make_payment_empty_customer_id` | ✅ |
| `test_make_payment_invalid_datetime` | ✅ |
| `test_make_payment_cod_missing_courier` | ✅ |
| `test_make_payment_bank_transfer_missing_fields` | ✅ |
| `test_sales_report_empty_range` | ✅ |
| `test_sales_report_invalid_date_range` | ✅ |
| `test_sales_report_invalid_datetime_format` | ✅ |
| `test_make_payment_modifier_at_lower_bound` | ✅ |

<br><br>

### Running Tests

<br>

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_payments.py
```

<br><br>

## Running the Application

### Using Docker Compose (Recommended)
<br>

1. Clone the repository:
```bash
git clone <repository-url>
```
<br>

2. Start the services:
```bash
docker-compose up --build
```
<br>

3. Access the GraphQL Playground at `http://localhost:8080/graphql`
<br>

4. To stop the services:
```bash
# Keep database data
docker-compose down

# Remove database data
docker-compose down -v
```
<br><br>

### Local Development
<br>

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
<br>

2. Install dependencies:
```bash
pip install -r requirements.txt
```
<br>

3. Set up environment variables (create `.env` file):
```env
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=anymind_pos
```
<br>

4. Ensure PostgreSQL is running and the database exists


5. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
<br><br>

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | PostgreSQL username | - |
| `DB_PASSWORD` | PostgreSQL password | - |
| `DB_HOST` | Database host | `db` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | - |

<br><br>

## Scalability Considerations

- **Async Architecture**: The application uses async/await throughout (FastAPI, SQLAlchemy async, asyncpg) to handle many concurrent requests efficiently without thread blocking.

- **Horizontal Scaling**: The Dockerized application can be scaled horizontally by running multiple container instances behind a load balancer (e.g., nginx, AWS ALB, or Cloud Run's auto-scaling).

- **Stateless Design**: The API is stateless - all state lives in PostgreSQL. This allows any instance to handle any request, enabling easy load balancing.

- **Connection Pooling**: SQLAlchemy's connection pool manages database connections efficiently across concurrent requests.
