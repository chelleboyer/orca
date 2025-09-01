# OOUX ORCA Project Builder

A collaborative web application for Object-Oriented UX methodology, enabling teams to work together on ORCA matrices with real-time collaboration and comprehensive export capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git

### Local Development Setup

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd orca
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Verify setup:**
```bash
python check_setup.py
```

3. **Environment configuration:**
```bash
cp .env.example .env
# Edit .env with your local settings
```

4. **Start services with Docker:**
```bash
docker-compose up -d postgres redis
```

5. **Run the application:**
```bash
python run_dev.py
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the application:**
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database Admin: http://localhost:8080 (Adminer)

## 🏗️ Project Structure

```
orca/
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── core/                     # Core configuration and utilities
│   │   ├── __init__.py
│   │   ├── config.py             # Application settings
│   │   ├── database.py           # Database connection
│   │   └── security.py           # Authentication utilities
│   ├── models/                   # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── base.py               # Base model class
│   │   ├── user.py               # User and authentication models
│   │   ├── project.py            # Project and membership models
│   │   ├── orca.py               # ORCA matrix models (Object, Relationship, CTA, Attribute)
│   │   └── collaboration.py      # Session and change tracking models
│   ├── api/                      # API route handlers
│   │   ├── __init__.py
│   │   ├── v1/                   # API version 1
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── projects.py       # Project management endpoints
│   │   │   ├── objects.py        # ORCA object operations
│   │   │   ├── relationships.py  # Relationship management
│   │   │   ├── ctas.py           # Call-to-action operations
│   │   │   ├── attributes.py     # Attribute management
│   │   │   └── exports.py        # Export operations
│   │   └── websocket.py          # WebSocket handlers
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py       # Authentication business logic
│   │   ├── project_service.py    # Project operations
│   │   ├── matrix_service.py     # ORCA matrix operations
│   │   ├── collaboration_service.py # Real-time collaboration
│   │   └── export_service.py     # Export generation
│   ├── schemas/                  # Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── user.py               # User schemas
│   │   ├── project.py            # Project schemas
│   │   ├── orca.py               # ORCA matrix schemas
│   │   └── common.py             # Shared schemas
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html             # Base template
│   │   ├── auth/                 # Authentication pages
│   │   ├── dashboard/            # Project dashboard
│   │   ├── matrix/               # Matrix workspace
│   │   └── components/           # Reusable components
│   └── static/                   # Static assets
│       ├── css/                  # Tailwind CSS
│       ├── js/                   # JavaScript and HTMX
│       └── images/               # Images and icons
├── alembic/                      # Database migrations
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── test_auth.py              # Authentication tests
│   ├── test_projects.py          # Project tests
│   ├── test_matrix.py            # ORCA matrix tests
│   └── test_collaboration.py     # Real-time collaboration tests
├── scripts/                      # Utility scripts
│   ├── seed_data.py              # Database seeding
│   └── export_sample.py          # Export testing
├── docs/                         # Project documentation
│   ├── prd/                      # Product requirements (sharded)
│   └── architecture/             # Architecture documentation (sharded)
├── docker-compose.yml            # Development services
├── Dockerfile                    # Production container
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore patterns
├── alembic.ini                   # Database migration config
└── pyproject.toml                # Project metadata and tools
```

## 🛠️ Development Workflow

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run tests in watch mode
pytest-watch
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Reset database (development only)
alembic downgrade base && alembic upgrade head
```

### Code Quality
```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint code
flake8 app/ tests/
mypy app/

# Security scan
bandit -r app/
```

## 🐳 Docker Development

### Full stack with Docker:
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Rebuild after changes
docker-compose up --build

# Stop services
docker-compose down
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ooux_orca
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/ooux_orca_test

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=True
ENVIRONMENT=development
```

## 📚 API Documentation

- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **WebSocket Tests**: Real-time collaboration testing
- **End-to-End Tests**: Full user workflow testing

## 🚀 Deployment

### Production Build
```bash
# Build production image
docker build -t ooux-orca:latest .

# Run production container
docker run -p 8000:8000 --env-file .env ooux-orca:latest
```

## 📖 Documentation

- [Product Requirements Document](docs/prd/)
- [Architecture Documentation](docs/architecture/)
- [API Reference](http://localhost:8000/docs)

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes following the coding standards
3. Add tests for new functionality
4. Run the full test suite
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
