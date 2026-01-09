# Smart Customs Backend API

This is a Django REST Framework backend for the Smart Customs frontend application. It provides comprehensive API endpoints for customs declaration management, HS code classification, duty calculations, and more.

## Features

- User authentication and management
- Customs declaration processing
- HS code classification and search
- Duty and tax calculations
- Product item management
- AI-powered recommendations
- Document generation (XML export)
- Risk assessment and auditing

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up the database:
```bash
python manage.py migrate
```

3. Create a superuser:
```bash
python manage.py createsuperuser
```

4. Start the development server:
```bash
python manage.py runserver
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login

### Customs Operations
- `GET,POST /api/declarations/` - Manage customs declarations
- `GET,POST /api/product-items/` - Manage product items
- `GET,POST /api/hs-codes/` - HS code management
- `GET /api/hs-codes/?search=QUERY` - Search HS codes

### Calculations
- `POST /api/calculate-customs-duties/` - Calculate customs duties
- `POST /api/perform-risk-analysis/` - Perform risk analysis
- `GET /api/declarations/{id}/summary/` - Get declaration summary

### AI Features
- `GET /api/search-hs-codes/?q=QUERY` - Semantic HS code search
- `GET /api/hs-code-details/{code}/` - Get detailed HS code information
- `POST /api/declarations/{id}/audit/` - Perform declaration audit

### Document Generation
- `GET /api/declarations/{id}/export-xml/` - Export declaration as XML

## Models Overview

- **User**: Custom user model with phone authentication
- **Declaration**: Customs declaration with status, products, and metadata
- **ProductItem**: Individual products within declarations
- **HsCode**: HS code database with rates and requirements
- **CalculationResult**: Duty calculation results
- **AuditResult**: Risk assessment results

## Configuration

The backend is configured to work with the frontend at `http://localhost:3000`. CORS settings are already configured in `settings.py`.

## Usage Examples

### Register a new user
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+998901234567",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+998901234567",
    "password": "securepassword123"
  }'
```

### Create a declaration
```bash
curl -X POST http://localhost:8000/api/declarations/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "contract_number": "CONTRACT-2024-001",
    "invoice_date": "2024-01-15",
    "partner_name": "Example Partner LLC",
    "status": "QORALAMA",
    "mode": "IM_40",
    "currency": "USD",
    "products": [
      {
        "name": "Laptop Computer",
        "hs_code": "8471301000",
        "price": 1200.00,
        "quantity": 10,
        "unit": "dona",
        "netto": 2.5,
        "brutto": 3.0
      }
    ]
  }'
```

## Admin Panel

Access the Django admin panel at `http://localhost:8000/admin/` with your superuser credentials to manage data directly.

## Integration with Frontend

The backend is designed to seamlessly integrate with the Smart Customs React frontend. All API endpoints follow RESTful conventions and return JSON responses compatible with the frontend types.

## Error Handling

The API returns appropriate HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Server Error