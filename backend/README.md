# CodeGuard AI - Backend

Multi-Agent Code Review System with AI-Powered Explanations

## Architecture

This backend follows **Clean Architecture** principles:

```
┌─────────────────────────────────────────┐
│       PRESENTATION LAYER                │  ← FastAPI REST API + WebSocket
├─────────────────────────────────────────┤
│       APPLICATION LAYER                 │  ← Use Cases & Services
├─────────────────────────────────────────┤
│       DOMAIN LAYER (Core)               │  ← Business Logic (Agents)
├─────────────────────────────────────────┤
│       INFRASTRUCTURE LAYER              │  ← Database, Cache, External APIs
└─────────────────────────────────────────┘
```

## Project Structure

```
backend/
├── src/
│   ├── domain/              # Core business logic
│   │   ├── agents/          # SecurityAgent, QualityAgent, etc.
│   │   ├── models/          # Entities & Value Objects
│   │   ├── events/          # Event Bus (Observer Pattern)
│   │   └── factories/       # Agent Factory (Singleton)
│   ├── application/         # Use cases
│   │   ├── services/        # AnalysisService, AIExplainerService
│   │   ├── dtos/            # Data Transfer Objects
│   │   └── interfaces/      # Repository contracts
│   ├── infrastructure/      # External dependencies
│   │   ├── repositories/    # Database access
│   │   ├── orm/             # SQLAlchemy entities
│   │   ├── external_services/ # Clerk, Gemini, MCP
│   │   └── cache/           # Redis
│   ├── presentation/        # API layer
│   │   ├── api/             # FastAPI controllers
│   │   ├── websocket/       # Real-time progress
│   │   └── middleware/      # Auth, rate limiting
│   └── config/              # Configuration
├── tests/                   # Organized by layer
├── docs/                    # Design diagrams
└── main.py                  # Entry point
```

## Design Patterns

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| **Factory** | `AgentFactory` | Create agents dynamically |
| **Singleton** | `AgentFactory`, `EventBus` | Single instance |
| **Observer** | `EventBus` + Observers | Real-time progress |
| **Repository** | All repositories | Data access abstraction |
| **Strategy** | `BaseAgent` | Interchangeable algorithms |
| **Dependency Injection** | Constructor injection | Testability |

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run with Docker

```bash
docker-compose up -d
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start Development Server

```bash
uvicorn src.core.main:app --reload
```

API docs available at: http://localhost:8000/docs

## Testing

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/domain/test_security_agent.py

# Run with verbose output
pytest -v
```

## Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
pylint src/
flake8 src/

# Type checking
mypy src/
```

## API Endpoints

### Analysis
- `POST /api/v1/analyze` - Upload and analyze Python file
- `GET /api/v1/reviews/{id}` - Get analysis results
- `GET /api/v1/reviews` - List user's analyses

### WebSocket
- `ws://localhost:8000/ws/analysis/{analysis_id}` - Real-time progress

### Admin (Sprint 4)
- `PUT /api/v1/admin/agents/{agent_name}/config` - Configure agent
- `GET /api/v1/admin/metrics` - System metrics

## Sprints Roadmap

- **Sprint 1 (MVP)**: SecurityAgent, API REST, Persistence
- **Sprint 2**: Quality/Performance/Style Agents, Parallel execution, WebSocket
- **Sprint 3**: AI Explanations (Gemini), MCP Integration, Frontend
- **Sprint 4**: Auto-fix, Custom MCP server, Admin dashboard

## Tech Stack

- **Framework**: FastAPI 0.104
- **Database**: PostgreSQL 15 (Supabase)
- **Cache**: Redis 7
- **AI**: Google Gemini 1.5 Flash/Pro
- **Auth**: Clerk OAuth
- **Static Analysis**: bandit, radon, pylint, flake8
- **Testing**: pytest, coverage

## Contributing

1. Create feature branch
2. Write tests (minimum 75% coverage)
3. Follow PEP 8 style guide
4. Run linters before commit
5. Update documentation

## License

Academic project - Universidad Nacional de Colombia
