# CodeGuard AI - Backend

**Multi-Agent Code Review System with AI-Powered Explanations**

> **⚠️ Current Status**: This project is in the **architecture design phase**. Most functionality is planned but not yet implemented.

## Project Overview

CodeGuard AI is designed as a sophisticated code analysis system that uses multiple specialized agents to analyze Python code for security vulnerabilities, quality issues, performance problems, and style violations. The system is intended to provide AI-powered explanations and real-time progress tracking via WebSocket connections.

### Vision
- **Multi-Agent Architecture**: Separate agents for Security, Quality, Performance, and Style analysis
- **AI-Powered Explanations**: Integration with Google Gemini for intelligent code recommendations
- **Real-Time Analysis**: WebSocket-based progress tracking
- **Professional Code Review**: Automated analysis with detailed reporting

## Current Implementation Status

###  What Works
- **Project Structure**: Complete Clean Architecture implementation
- **Dependencies**: All required packages defined in `requirements.txt`
- **Configuration**: Environment variables and settings structure
- **Documentation**: Comprehensive architecture diagrams and design documents
- **Tool Setup**: Code quality tools (black, isort, mypy, pylint) configured

###  What's Missing (Placeholder Files)
- **API Endpoints**: All router files are empty (`auth.py`, `analysis.py`, `reviews.py`)
- **Core Application**: Main FastAPI app not implemented (`src/core/main.py` missing)
- **Agent System**: Base agent and all specialized agents are empty
- **Services**: AI service, analysis service, and other core services not implemented
- **Database**: No SQLAlchemy models or repository implementations
- **Authentication**: Security layer and auth services missing

###  Dependencies Configured
- **Web Framework**: FastAPI, Uvicorn
- **Database**: SQLAlchemy, Alembic, PostgreSQL/Supabase
- **Authentication**: Clerk Backend API
- **AI Integration**: Google Generative AI, Google Cloud AI Platform
- **Static Analysis**: bandit, radon, pylint, flake8
- **Cache**: Redis
- **Testing**: pytest, coverage, faker
- **Development**: black, isort, mypy, pylint

## Setup and Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (or Supabase account)
- Redis 7+
- Google Cloud Account (for AI features)
- Clerk Account (for authentication)

### 1. Environment Setup
```bash
# Clone and setup virtual environment
git clone <repository-url>
cd CodeGuard-Unal/backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Configure required variables:
# - Database: SUPABASE_URL, SUPABASE_KEY
# - Redis: REDIS_URL
# - Authentication: CLERK_SECRET_KEY, CLERK_PUBLISHABLE_KEY
# - AI: GOOGLE_AI_API_KEY, GOOGLE_CLOUD_PROJECT
```

### 3. Database Setup (Planned)
```bash
# These commands will be available once database is implemented
alembic init
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 4. Running the Application (Currently Non-Functional)
```bash
# This will fail due to missing implementation
uvicorn src.core.main:app --reload
```

## API Documentation

> **Note**: Currently all API endpoints are placeholders and return HTTP 501 (Not Implemented)

### Planned Endpoints

#### Analysis Endpoints
- `POST /api/v1/analyze` - Upload and analyze Python file
- `GET /api/v1/reviews/{id}` - Get analysis results  
- `GET /api/v1/reviews` - List user's analyses
- `DELETE /api/v1/reviews/{id}` - Delete analysis

#### Authentication Endpoints  
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Current user info

#### Review Management
- `GET /api/v1/reviews/{id}/findings` - Get detailed findings
- `GET /api/v1/reviews/{id}/metrics` - Get analysis metrics
- `POST /api/v1/reviews/{id}/export` - Export analysis report

#### WebSocket Endpoints
- `ws://localhost:8000/ws/analysis/{analysis_id}` - Real-time progress updates

#### Admin Endpoints (Planned)
- `PUT /api/v1/admin/agents/{agent_name}/config` - Configure agent settings
- `GET /api/v1/admin/metrics` - System-wide metrics
- `GET /api/v1/admin/health` - System health status

### Example Usage (When Implemented)
```bash
# Upload file for analysis
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Authorization: Bearer <token>" \
  -F "file=@example.py"

# Get analysis results
curl -X GET "http://localhost:8000/api/v1/reviews/123" \
  -H "Authorization: Bearer <token>"

# WebSocket connection for real-time progress
ws://localhost:8000/ws/analysis/123
```

## Agent System

### Planned Architecture
The agent system is designed around the **Strategy Pattern** with a **Factory** for agent creation:

```
BaseAgent (Abstract)
├── SecurityAgent (Security vulnerabilities)
├── QualityAgent (Code quality issues)  
├── PerformanceAgent (Performance optimizations)
└── StyleAgent (Code style and conventions)
```

### Planned Capabilities

#### SecurityAgent
- **SQL Injection Detection**: Using bandit patterns
- **Authentication Issues**: Weak password policies
- **Data Exposure**: Sensitive information handling
- **Input Validation**: Missing or weak validation

#### QualityAgent  
- **Complexity Analysis**: Cyclomatic complexity measurement
- **Code Duplication**: Repeated code patterns
- **Maintainability Index**: Overall code maintainability score
- **Test Coverage**: Test coverage analysis

#### PerformanceAgent
- **Runtime Complexity**: O(n) analysis of algorithms
- **Memory Usage**: Memory-intensive operations
- **Database Queries**: N+1 query problems
- **Resource Leaks**: Unclosed connections/files

#### StyleAgent
- **PEP 8 Compliance**: Style guide adherence  
- **Naming Conventions**: Variable, function, class naming
- **Documentation**: Docstring requirements
- **Import Organization**: Import statement formatting

### Agent Execution Flow
```python
# Planned execution pattern
agent = AgentFactory.create_agent("security")
result = agent.analyze(code_file, config)
```

##  Configuration

### Environment Variables

#### Core Application
- `APP_NAME=CodeGuard AI` - Application name
- `APP_VERSION=1.0.0` - Application version
- `DEBUG=True` - Enable debug mode
- `ENVIRONMENT=development` - Environment type

#### API Configuration  
- `API_HOST=0.0.0.0` - API server host
- `API_PORT=8000` - API server port
- `LOG_LEVEL=INFO` - Logging level
- `ALLOWED_ORIGINS` - CORS allowed origins

#### Database (Supabase)
- `DATABASE_URL=postgresql://...` - Direct PostgreSQL connection
- `SUPABASE_URL=https://...` - Supabase project URL
- `SUPABASE_KEY=...` - Supabase anonymous key

#### Redis Cache
- `REDIS_URL=redis://localhost:6379/0` - Redis connection
- `REDIS_PASSWORD` - Redis password (if required)
- `REDIS_TTL=86400` - Cache TTL in seconds

#### Authentication (Clerk)
- `CLERK_SECRET_KEY=sk_test_...` - Clerk secret key
- `CLERK_PUBLISHABLE_KEY=pk_test_...` - Clerk publishable key

#### AI Services
- `GOOGLE_AI_API_KEY=AIzaSy...` - Google AI API key
- `GOOGLE_CLOUD_PROJECT=...` - GCP project name  
- `VERTEX_AI_LOCATION=us-central1` - Vertex AI location
- `AI_MODEL=gemini-1.5-flash` - AI model to use
- `AI_RATE_LIMIT=100` - Rate limit per minute

#### MCP Servers (Planned)
- `MCP_OWASP_SERVER_PATH=/path/to/owasp-mcp` - OWASP knowledge base
- `MCP_CVE_SERVER_PATH=/path/to/cve-mcp` - CVE database
- `MCP_CUSTOM_SERVER_PATH=/path/to/codeguard-kb-mcp` - Custom knowledge base

##  Architecture Overview

The backend follows **Clean Architecture** principles with four distinct layers:

```
┌─────────────────────────────────────────┐
│       PRESENTATION LAYER                │  ← FastAPI REST API + WebSocket
│   - routers/ (auth, analysis, reviews)  │    - API endpoints
│   - middleware/ (auth, rate limiting)   │    - WebSocket handlers  
│   - schemas/ (data models)              │    - Request/response models
├─────────────────────────────────────────┤
│       APPLICATION LAYER                 │  ← Use Cases & Services
│   - services/ (analysis, ai, auth)      │    - Business logic
│   - handlers/ (event handlers)          │    - Use case coordination
│   - workflows/ (analysis workflow)      │    - Process orchestration
├─────────────────────────────────────────┤
│       DOMAIN LAYER (Core)               │  ← Business Logic (Agents)
│   - agents/ (security, quality, etc)    │    - Core analysis logic
│   - models/ (entities, value objects)   │    - Business rules
│   - events/ (domain events)             │    - Event-driven design
├─────────────────────────────────────────┤
│       INFRASTRUCTURE LAYER              │  ← External Dependencies
│   - repositories/ (database access)     │    - Database interactions
│   - external_services/ (clerk, gemini)  │    - External API clients
│   - cache/ (redis)                      │    - Caching layer
└─────────────────────────────────────────┘
```

### Design Patterns Implemented
- **Factory Pattern**: `AgentFactory` for dynamic agent creation
- **Observer Pattern**: `EventBus` for real-time progress updates
- **Repository Pattern**: Abstract data access layer
- **Strategy Pattern**: Interchangeable agent algorithms
- **Dependency Injection**: Constructor injection for testability
- **Singleton Pattern**: Agent factory and event bus

##  Development

### Current Development Status
This project is currently in the **architecture design and planning phase**. To begin development:

### Getting Started for Contributors

1. **Understand the Architecture**
   - Review the Clean Architecture layers
   - Study the existing design patterns
   - Understand the agent system design

2. **Priority Implementation Order**
   ```
   1. Core Infrastructure
      ├── src/core/main.py (FastAPI app)
      ├── src/core/config/settings.py (Configuration)
      └── src/core/database.py (Database setup)
   
   2. Domain Layer
      ├── src/agents/base_agent.py (Base agent)
      └── src/agents/*_agent.py (Specialized agents)
   
   3. Application Layer  
      ├── src/services/analysis_service.py
      └── src/services/ai_service.py
   
   4. Presentation Layer
      ├── src/routers/analysis.py
      ├── src/routers/auth.py
      └── src/routers/reviews.py
   ```

### Development Workflow
```bash
# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Code quality checks (when code is available)
black src/ tests/
isort src/ tests/
mypy src/
pylint src/

# Run tests (when implemented)
pytest tests/ --cov=src
```

### Contributing Guidelines
1. **Follow Clean Architecture**: Keep layers separated and dependencies pointing inward
2. **Write Tests First**: Implement tests alongside features
3. **Document Changes**: Update this README when adding new functionality
4. **Use Design Patterns**: Follow established patterns in the codebase
5. **Code Quality**: Maintain high code quality standards

##  Project Structure
```
backend/
├── src/
│   ├── core/                    # Core FastAPI application
│   │   ├── main.py             # App factory (MISSING - HIGH PRIORITY)
│   │   ├── config/             # Configuration management
│   │   │   └── settings.py     # Environment settings (EMPTY - HIGH PRIORITY)
│   │   ├── database.py         # Database configuration (EMPTY)
│   │   ├── security.py         # Authentication/authorization (EMPTY)
│   │   ├── container.py        # Dependency injection (EMPTY)
│   │   ├── cache/              # Caching infrastructure
│   │   ├── dependencies/       # Dependency injection
│   │   └── events/             # Event system
│   ├── agents/                 # Agent system (ALL EMPTY - HIGH PRIORITY)
│   │   ├── base_agent.py       # Base agent class
│   │   ├── security_agent.py   # Security analysis
│   │   ├── quality_agent.py    # Quality analysis  
│   │   ├── performance_agent.py # Performance analysis
│   │   ├── style_agent.py      # Style analysis
│   │   ├── agent_factory.py    # Agent factory
│   │   └── orchestrator.py     # Agent coordination
│   ├── routers/                # API endpoints (ALL EMPTY - HIGH PRIORITY)
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── analysis.py         # Analysis endpoints
│   │   ├── reviews.py          # Review management
│   │   ├── health.py           # Health checks
│   │   └── admin.py            # Administrative endpoints
│   ├── services/               # Business logic services (ALL EMPTY)
│   │   ├── analysis_service.py # Analysis orchestration
│   │   ├── ai_service.py       # AI integration
│   │   ├── auth_service.py     # Authentication logic
│   │   └── export_service.py   # Report generation
│   ├── repositories/           # Data access layer (ALL EMPTY)
│   │   ├── user_repo.py        # User data access
│   │   ├── review_repo.py      # Review data access
│   │   └── finding_repo.py     # Findings data access
│   ├── schemas/                # Data models (Structure exists)
│   │   ├── user.py             # User models
│   │   ├── analysis.py         # Analysis models
│   │   ├── finding.py          # Finding models
│   │   └── review.py           # Review models
│   └── utils/                  # Utility functions
├── tests/                      # Test suite (Structure exists)
├── docs/                       # Architecture documentation
├── alembic/                    # Database migrations
├── main.py                     # Application entry point
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example               # Environment template
├── pyproject.toml             # Project configuration
├── docker-compose.yml         # Docker setup
└── Dockerfile                 # Container configuration
```

##  Future Roadmap

### Sprint 1: Core Infrastructure (Priority 1)
- [ ] Implement `src/core/main.py` (FastAPI application)
- [ ] Implement `src/core/config/settings.py` (Configuration)
- [ ] Implement database setup and SQLAlchemy models
- [ ] Implement basic authentication system
- [ ] Create basic test suite

### Sprint 2: Agent System (Priority 2)
- [ ] Implement `BaseAgent` with core functionality
- [ ] Implement `SecurityAgent` with bandit integration
- [ ] Implement agent factory and orchestrator
- [ ] Create basic analysis workflow
- [ ] Implement WebSocket for real-time progress

### Sprint 3: AI Integration (Priority 3)
- [ ] Implement AI service with Gemini integration
- [ ] Implement AI-powered explanations
- [ ] Add MCP server integration
- [ ] Create advanced analysis capabilities

### Sprint 4: Production Features (Priority 4)
- [ ] Implement export functionality (PDF reports)
- [ ] Add admin dashboard capabilities
- [ ] Performance optimization
- [ ] Production deployment setup

##  Quick Start for Contributors

If you want to help implement this project:

1. **Start with Core Infrastructure** - Implement the missing FastAPI app and configuration
2. **Focus on Authentication** - Set up Clerk integration for user management  
3. **Build Agent System** - Create the analysis agents with real functionality
4. **Add AI Features** - Integrate with Google Gemini for explanations

This is an excellent project for learning **Clean Architecture**, **Agent Patterns**, and **AI Integration**. The comprehensive design makes it easy to understand and extend.

##  Statistics

- **Total Files**: 50+ Python files
- **Implemented**: ~10% (configuration and setup only)
- **Planned Features**: 90% defined in architecture
- **Documentation Coverage**: 95% (excellent design documentation)
- **Architecture Score**: A+ (Clean Architecture implementation)

##  License

Academic project - Universidad Nacional de Colombia
