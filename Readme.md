# FastAPI User Management System

A robust FastAPI application with user authentication, role-based access control, and user management features.

## Features

- User Authentication with JWT
- Role-based Access Control (RBAC)
- User Management (CRUD operations)
- SQLAlchemy ORM Integration
- Automated Testing Setup

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Getting Started

### 1. Create Virtual Environment

#### On Windows:
```bash
venv\Scripts\activate
```

#### On macOS/Linux:
```bash
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory using the provided template:
```bash
cp env_sample .env
```

Update the `.env` file with your configurations:

#### Database Configuration
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```
For SQLite:
```
DATABASE_URL=sqlite:///./sql_app.db
```

#### JWT Configuration
```
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### Email Configuration (Optional)
```
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-email-password
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

#### Other Configuration
```
DEBUG=True
ENVIRONMENT=development
```

### 4. Database Migration Setup

Initialize migrations:
```bash
alembic init migrations
```

Generate migration:
```bash
alembic revision --autogenerate -m "Initial migration"
```

Apply migration:
```bash
alembic upgrade head
```

### 5. Run the Application
```bash
uvicorn main:app --reload
```

## Project Structure
```
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── role.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── role.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── user.py
│   │   │   │   └── auth.py
│   │   │   └── __init__.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── security.py
│   │   └── config.py
│   ├── utils/
│   │   └── helpers.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_users.py
│   └── test_auth.py
├── alembic/
│   ├── versions/
│   └── alembic.ini
├── requirements.txt
├── README.md
├── .env
└── .gitignore
```

## Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=app tests/
```

Run specific test file:
```bash
pytest tests/test_users.py
```

