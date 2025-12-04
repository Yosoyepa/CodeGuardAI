# 🚀 CodeGuard AI - Multi-Agent Code Review System

[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-brightgreen.svg)](https://github.com/Yosoyepa/CodeGuardAI/releases/tag/v1.0.0)
[![Lint](https://github.com/Yosoyepa/CodeGuardAI/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/Yosoyepa/CodeGuardAI/actions/workflows/lint.yml)
[![Tests](https://github.com/Yosoyepa/CodeGuardAI/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Yosoyepa/CodeGuardAI/actions/workflows/test.yml)
[![Coverage 94%](https://img.shields.io/badge/coverage-94.34%25-brightgreen.svg)](https://github.com/Yosoyepa/CodeGuardAI)
[![Docker Build](https://github.com/Yosoyepa/CodeGuardAI/actions/workflows/docker.yml/badge.svg?branch=main)](https://github.com/Yosoyepa/CodeGuardAI/actions/workflows/docker.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791.svg)](https://www.postgresql.org/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com/)
[![License MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**CodeGuard AI** es una plataforma inteligente de revisión de código Python que utiliza una **arquitectura híbrida multi-agente** para realizar análisis estáticos especializados en seguridad, calidad, rendimiento y estilo. Integra comunicación en tiempo real con WebSockets y explicaciones mejoradas por IA mediante Google Gemini y servidores Model Context Protocol (MCP).

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Arquitectura](#-arquitectura-clean-architecture)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Inicio Rápido](#-inicio-rápido)
- [Instalación Local](#-instalación-local)
- [Uso](#-uso)
- [Contribución](#-contribución)
- [Sprint Roadmap](#-sprint-roadmap)
- [Equipo](#-equipo)

---

## ✨ Características Principales

### Sprint 1 (22 Oct - 6 Nov) - MVP - ✅ COMPLETADO

#### 🛡️ SecurityAgent (v1.0.0)
- Detección de funciones peligrosas (`eval`, `exec`, `pickle`, `__import__`)
- Análisis de inyección SQL (concatenación de cadenas, f-strings)
- Detección de credenciales hardcodeadas (password, API keys, tokens)
- Identificación de algoritmos criptográficos débiles (MD5, SHA1, DES)
- **Método**: AST (Abstract Syntax Tree) parsing + Regex patterns

#### 🏗️ Arquitectura Clean Architecture
- **Capa de Dominio**: Agentes base, modelos de datos, lógica de negocio
- **Capa de Aplicación**: Servicios, casos de uso, routers REST/WebSocket
- **Capa de Infraestructura**: BD, cache, eventos, configuración
- **Capa de Presentación**: API REST, WebSocket, Swagger/OpenAPI

#### 🔄 CI/CD Pipeline Completo (GitHub Actions)
- ✅ **lint.yml**: Validación de código (Black, isort, Flake8)
- ✅ **test.yml**: Tests unitarios + cobertura ≥75%
- ✅ **docker.yml**: Build y validación de imágenes Docker
- ✅ **Branch Protection**: Reglas en `main` y `develop`
- ✅ **Secrets**: Configuración de variables de entorno

#### 💾 Persistencia Completa
- PostgreSQL con Alembic (migraciones versionadas)
- Redis para caché y sesiones
- Almacenamiento de análisis, hallazgos, reseñas de código
- Cifrado AES-256 para código fuente en BD

#### 📡 Comunicación en Tiempo Real
- WebSockets para progreso de análisis en vivo
- Event Bus con patrón Observer
- Notificaciones de estado de agentes

### Sprint 2 (4-17 Nov) - Agentes Especializados - 🔄 EN PROGRESO

- [x] **Supabase Integration**: PostgreSQL cloud database con SQLAlchemy ORM y Alembic migrations ✅
  - Schema: `users`, `code_reviews`, `agent_findings`
  - Tipos PostgreSQL: UUID, JSONB, ARRAY, ENUMs
  - Relaciones con cascade delete y índices optimizados
- [ ] **BaseAgent**: Clase abstracta con logging y métricas
- [ ] **QualityAgent**: Complejidad ciclomática, duplicación de código
- [ ] **PerformanceAgent**: Bucles anidados, algoritmos ineficientes
- [ ] **StyleAgent**: PEP 8, docstrings, convenciones de nombres
- [ ] **OrchestratorAgent**: Ejecución paralela con ThreadPoolExecutor
- [ ] Autenticación con Clerk OAuth 2.0
- [ ] Dashboard interactivo con métricas

### Sprint 3 (18 Nov - 1 Dic) - IA Generativa - 📅 PLANIFICADO

- [ ] Integración Google Gemini 1.5 Flash (desarrollo)
- [ ] Integración Google Vertex AI Gemini Pro (producción)
- [ ] Servidores MCP: OWASP Top 10, CVE Database, KB personalizado
- [ ] Explicaciones pedagógicas generadas por IA
- [ ] Sugerencias de remediación automáticas
- [ ] Frontend React con visualizaciones

### Sprint 4 (2-15 Dic) - Deployment & Polish - 📅 PLANIFICADO

- [ ] Auto-corrección con generación de parches
- [ ] Servidor MCP personalizado para convenciones de equipo
- [ ] Panel de administración (configuración IA, reglas)
- [ ] Dashboard de métricas históricas
- [ ] Deployment en Railway/Render

---

## 🏛️ Arquitectura Clean Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER                                  │
│  REST API (FastAPI) │ WebSocket │ Swagger/OpenAPI Docs         │
│  POST /api/v1/analysis │ GET /api/v1/reviews/:id               │
│  WS /ws/analysis/:analysis_id                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              APPLICATION LAYER                                   │
│  AnalysisService │ MetricsService │ ExportService              │
│  AuthService │ ConfigService │ AIService                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              DOMAIN LAYER                                        │
│  OrchestratorAgent → BaseAgent → SecurityAgent                 │
│  QualityAgent │ PerformanceAgent │ StyleAgent                  │
│  AgentFactory (Singleton) │ EventBus (Observer)                │
│  Models: Finding, Analysis, CodeReview                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              INFRASTRUCTURE LAYER                                │
│  PostgreSQL │ Redis │ Alembic Migrations                       │
│  AnalysisRepository │ FindingRepository                         │
│  EmailService │ FileHandler │ PDFGenerator                     │
│  RateLimiter │ Logger │ CacheManager                           │
└─────────────────────────────────────────────────────────────────┘
```

**Patrones de Diseño Implementados**:
- Factory Pattern (AgentFactory, ServiceFactory)
- Singleton Pattern (Container, EventBus)
- Observer Pattern (Event system)
- Repository Pattern (Data access)
- Strategy Pattern (Agent implementations)
- Dependency Injection (Core container)

---

## 📁 Estructura del Proyecto

```
CodeGuard-Unal/
│
├── README.md                          # Este archivo (raíz)
├── CONTRIBUTING.md                    # Guía de contribución
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore patterns
│
├── .github/
│   ├── workflows/
│   │   ├── lint.yml                   # ✅ Linting CI workflow
│   │   ├── test.yml                   # ✅ Testing CI workflow
│   │   └── docker.yml                 # ✅ Docker build workflow
│   └── PULL_REQUEST_TEMPLATE.md       # PR template
│
├── backend/                           # Aplicación FastAPI
│   ├── .env.example                   # Template de variables de entorno
│   ├── .dockerignore
│   ├── .gitignore
│   ├── Dockerfile                     # ✅ Docker image definition
│   ├── docker-compose.yml             # ✅ Multi-container setup (PostgreSQL, Redis)
│   ├── pyproject.toml                 # Configuración Python
│   ├── pytest.ini                     # Configuración de tests
│   ├── requirements.txt               # Dependencias producción
│   ├── requirements-dev.txt           # Dependencias desarrollo
│   ├── alembic.ini                    # Database migrations config
│   ├── README.md                      # Backend-specific docs
│   │
│   ├── alembic/
│   │   ├── env.py                     # Migration environment
│   │   ├── script.py.mako             # Migration template
│   │   └── versions/                  # Migration scripts
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                    # ✅ FastAPI app entry point
│   │   │
│   │   ├── agents/                    # 🤖 DOMAIN LAYER - Agentes
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Abstract base class
│   │   │   ├── orchestrator.py        # Coordinator de agentes
│   │   │   ├── agent_factory.py       # Factory pattern
│   │   │   ├── security_agent.py      # ✅ Seguridad
│   │   │   ├── quality_agent.py       # Calidad de código
│   │   │   ├── performance_agent.py   # Rendimiento
│   │   │   ├── style_agent.py         # Estilo/PEP8
│   │   │   └── analyzers/             # Herramientas estáticas
│   │   │       ├── ast_visitor.py
│   │   │       ├── bandit_analyzer.py
│   │   │       ├── flake8_analyzer.py
│   │   │       ├── pylint_analyzer.py
│   │   │       └── radon_analyzer.py
│   │   │
│   │   ├── core/                      # 🏗️ INFRASTRUCTURE LAYER
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # SQLAlchemy session
│   │   │   ├── security.py            # JWT, password hashing
│   │   │   ├── container.py           # DI container
│   │   │   ├── cache/                 # Redis layer
│   │   │   │   ├── redis_cache.py
│   │   │   │   └── cache_keys.py
│   │   │   ├── config/                # Configuración centralizada
│   │   │   │   ├── settings.py        # Pydantic settings
│   │   │   │   ├── database.py
│   │   │   │   ├── redis_config.py
│   │   │   │   ├── logging_config.py
│   │   │   │   ├── ai_config.py
│   │   │   │   └── mcp_config.py
│   │   │   ├── dependencies/          # DI providers
│   │   │   │   ├── get_db.py
│   │   │   │   ├── get_current_user.py
│   │   │   │   ├── auth.py
│   │   │   │   └── get_services.py
│   │   │   └── events/                # Event system
│   │   │       ├── base_event.py
│   │   │       ├── event_bus.py
│   │   │       ├── analysis_events.py
│   │   │       ├── agent_events.py
│   │   │       └── observers.py
│   │   │
│   │   ├── routers/                   # 📡 PRESENTATION LAYER
│   │   │   ├── __init__.py
│   │   │   ├── health.py              # GET /health
│   │   │   ├── analysis.py            # ✅ POST /api/v1/analyze
│   │   │   ├── reviews.py             # GET /api/v1/reviews/:id
│   │   │   ├── auth.py                # POST /auth/login
│   │   │   ├── admin.py               # Admin endpoints
│   │   │   └── export.py              # PDF/JSON export
│   │   │
│   │   ├── schemas/                   # 📊 Data models (Pydantic)
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py            # ✅ AnalysisContext
│   │   │   ├── finding.py             # ✅ Finding, Severity
│   │   │   ├── agent_config.py
│   │   │   ├── metrics.py
│   │   │   ├── review.py
│   │   │   ├── user.py
│   │   │   ├── export.py
│   │   │   ├── ai_explanation.py
│   │   │   ├── websocket.py
│   │   │   └── common.py
│   │   │
│   │   ├── services/                  # 🔧 APPLICATION LAYER
│   │   │   ├── __init__.py
│   │   │   ├── analysis_service.py    # Orquestación de análisis
│   │   │   ├── ai_service.py          # Integración con Gemini
│   │   │   ├── auth_service.py        # Autenticación
│   │   │   ├── config_service.py      # Configuración
│   │   │   ├── export_service.py      # Generación de reportes
│   │   │   ├── metrics_service.py     # Cálculo de métricas
│   │   │   └── mcp_context_enricher.py # MCP integration
│   │   │
│   │   ├── websocket/                 # 🔌 WebSocket handlers
│   │   │   ├── __init__.py
│   │   │   ├── connection_manager.py
│   │   │   ├── analysis_ws.py
│   │   │   └── events.py
│   │   │
│   │   ├── utils/                     # 🛠️ Utilities
│   │   │   ├── __init__.py
│   │   │   ├── logger.py              # Logging setup
│   │   │   ├── code_parser.py         # AST parsing
│   │   │   ├── validators.py          # Data validation
│   │   │   ├── file_handler.py        # File operations
│   │   │   ├── metrics_calculator.py  # Metrics algorithms
│   │   │   ├── rate_limiter.py        # Rate limiting
│   │   │   └── pdf_generator.py       # PDF reports
│   │   │
│   │   └── models/                    # ORM Models (SQLAlchemy)
│   │       ├── __init__.py
│   │       ├── base.py                # Base model
│   │       ├── analysis.py            # Analysis records
│   │       ├── finding.py             # Finding records
│   │       ├── review.py              # Code review records
│   │       ├── user.py                # User records
│   │       └── metrics.py             # Metrics records
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Pytest fixtures
│       ├── pytest.ini
│       ├── requirements.txt
│       │
│       ├── unit/                      # 🧪 Unit tests
│       │   ├── test_base_agent.py     # ✅ CGAI-12
│       │   ├── test_analysis_schemas.py # ✅ CGAI-12
│       │   ├── test_security_agent.py # ✅ CGAI-19
│       │   ├── test_quality_agent.py
│       │   ├── test_performance_agent.py
│       │   ├── test_style_agent.py
│       │   └── ...
│       │
│       ├── integration/               # 🔗 Integration tests
│       │   ├── test_security_agent_integration.py # ✅ CGAI-19
│       │   ├── test_analysis_service.py
│       │   └── test_api_endpoints.py
│       │
│       ├── e2e/                       # 🌐 End-to-end tests
│       │   ├── test_complete_analysis.py
│       │   ├── test_full_analysis_workflow.py
│       │   └── test_user_journey.py
│       │
│       └── fixtures/
│           ├── mock_data.py
│           ├── sample_code.py
│           └── test_data.py
│
└── docs/
    ├── README.md                      # Índice de documentación
    ├── ci-cd-setup.md                 # 📋 CI/CD configuration
    ├── CodeGuardUnalDesignBeta.pdf   # Diseño del sistema
    ├── 04-activity-diagrams/          # Diagramas de actividad
    ├── 05-state-diagrams/             # Diagramas de estado
    ├── 06-database/                   # Esquema de BD
    ├── 07-component-diagrams/         # Diagramas de componentes
    ├── 08-mockups/                    # UI/UX designs
    ├── 09-crc-cards/                  # CRC cards
    └── exports/
        ├── png/                       # Diagramas exportados (PNG)
        └── svg/                       # Diagramas exportados (SVG)
```

---

## 🚀 Inicio Rápido

### Requisitos Previos

- **Docker** & **Docker Compose**
- **Python 3.11+** (para desarrollo local)
- **Git**

### Opción 1: Con Docker Compose (Recomendado)

```bash
# 1. Clonar repositorio
git clone https://github.com/Yosoyepa/CodeGuardAI.git
cd CodeGuardAI

# 2. Configurar variables de entorno
cd backend
cp .env.example .env
# Editar .env con credenciales de Supabase, etc.

# 3. Levantar todos los servicios
docker-compose up -d

# 4. Verificar que esté funcionando
curl http://localhost:8000/health

# 5. Acceder a la documentación interactiva
# API: http://localhost:8000/docs
# Redoc: http://localhost:8000/redoc
```

### Opción 2: Instalación Local (Desarrollo)

```bash
# 1. Clonar y navegar
git clone https://github.com/Yosoyepa/CodeGuardAI.git
cd CodeGuardAI/backend

# 2. Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo

# 4. Configurar base de datos
cp .env.example .env
# Editar .env

# 5. Ejecutar migraciones
alembic upgrade head

# 6. Levantar servidor
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 💻 Instalación Local

### Paso 1: Preparar Entorno

```bash
cd CodeGuard-Unal/backend

# Crear virtualenv
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Paso 2: Configurar Base de Datos

```bash
# Copiar template de variables de entorno
cp .env.example .env

# Editar .env y completar:
# - DATABASE_URL=postgresql://user:password@localhost:5432/codeguard_db
# - REDIS_URL=redis://localhost:6379/0
# - SUPABASE_URL=https://xxxxx.supabase.co
# - SUPABASE_KEY=xxxxxxxx

# Ejecutar migraciones Alembic
alembic upgrade head
```

### Paso 3: Ejecutar Servidor

```bash
# Modo desarrollo (con reload automático)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Modo producción
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Paso 4: Acceder a la Aplicación

- **API REST**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📖 Uso

### Análisis de Código via API

#### 1. Realizar Análisis

```bash
# Crear archivo de prueba con código vulnerable
echo 'password = "admin123"
result = eval(user_input)
query = "SELECT * FROM users WHERE id = " + user_id' > test_vuln.py

# Enviar análisis (en modo desarrollo, auth es opcional)
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@test_vuln.py"

# Respuesta:
# {
#   "review_id": "550e8400-e29b-41d4-a716-446655440000",
#   "filename": "test_vuln.py",
#   "status": "COMPLETED",
#   "quality_score": 70,
#   "total_findings": 3,
#   "findings": [
#     {
#       "severity": "critical",
#       "issue_type": "hardcoded_credentials",
#       "message": "Possible hardcoded password detected",
#       "line_number": 1
#     },
#     ...
#   ]
# }
```

#### 2. Obtener Resultados

```bash
curl -X GET "http://localhost:8000/api/v1/reviews/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Respuesta:
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "filename": "app.py",
#   "status": "completed",
#   "quality_score": 45,
#   "findings": [
#     {
#       "severity": "critical",
#       "issue_type": "dangerous_function",
#       "message": "Use of eval() detected",
#       "line_number": 2,
#       "code_snippet": "result = eval(user_input)",
#       "suggestion": "Use ast.literal_eval() instead",
#       "agent_name": "SecurityAgent"
#     }
#   ]
# }
```

#### 3. Monitorear en Tiempo Real (WebSocket)

```javascript
// Cliente JavaScript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/550e8400-e29b-41d4-a716-446655440000');

ws.onopen = () => {
  console.log('Conectado');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Progreso:', message);
  // {
  //   "type": "agent_progress",
  //   "agent_name": "SecurityAgent",
  //   "status": "analyzing",
  //   "findings_count": 2
  // }
};

ws.onerror = (error) => {
  console.error('Error:', error);
};
```

### Documentación Interactiva (Swagger UI)

Visita **http://localhost:8000/docs** para acceder a:
- 📋 Todos los endpoints disponibles
- 🧪 Pruebas interactivas
- 📚 Ejemplos de requests/responses
- 🔐 Autenticación integrada

---

## 🤝 Contribución

Antes de contribuir, **lee** [CONTRIBUTING.md](CONTRIBUTING.md) para conocer:

- 🔀 Flujo de trabajo **GitFlow** (ramas `main`, `develop`, `feature/*`)
- 📝 Convenciones de **Conventional Commits**
- ✅ Estándares de calidad (cobertura ≥75%, pylint ≥8.5/10)
- 🧪 Proceso de testing y revisión de código

### Proceso Rápido de Contribución

```bash
# 1. Crear rama feature desde develop
git checkout develop
git pull origin develop
git checkout -b feature/CGAI-XX-descripcion-corta

# 2. Hacer cambios y tests
# ... hacer cambios ...
pytest tests/ --cov=src --cov-fail-under=75

# 3. Commit con formato convencional
git add .
git commit -m "feat(agents): add new security check

- Detect hardcoded credentials
- Add unit tests (90% coverage)
- Update documentation

Related: CGAI-19"

# 4. Push y crear Pull Request
git push -u origin feature/CGAI-XX-descripcion-corta
# Crear PR en GitHub
```

**Nota**: Todos los PRs deben pasar los 3 status checks:
- ✅ Lint (Black, isort, Flake8)
- ✅ Tests (pytest, coverage ≥75%)
- ✅ Docker Build (imagen se construye sin errores)

---

## 🗺️ Sprint Roadmap

### Sprint 1 (22 Oct - 6 Nov) ✅ COMPLETADO

- ✅ Estructura Clean Architecture
- ✅ SecurityAgent v1 (eval/exec, SQL injection, hardcoded credentials)
- ✅ API REST con FastAPI
- ✅ Persistencia en PostgreSQL + Redis
- ✅ Pipeline CI/CD (lint, test, docker)
- ✅ WebSocket para progreso en tiempo real
- ✅ Documentación completa

**Criterios de éxito**: ✅ Cumplidos
- ✅ 3 workflows CI/CD funcionando
- ✅ Coverage >75%
- ✅ Branch protection en main y develop
- ✅ README con badges
- ✅ CONTRIBUTING.md completo

### Sprint 2 (4-17 Nov) 🔄 EN PROGRESO

**Historias Completadas (Sprint 1)**:
- ✅ CGAI-12: BaseAgent y AnalysisContext (5 pts) ✅
- ✅ CGAI-19: SecurityAgent v1 (5 pts) ✅
- ✅ CGAI-20: FastAPI endpoint POST /api/v1/analyze (5 pts) ✅
  - 116 tests passing (94.34% coverage)
  - ✅ OAuth2 para Swagger UI
  - ✅ Cifrado AES-256 para código fuente
  - PostgreSQL con Alembic migrations

**Historias Completadas (Sprint 2)**:
- [x] Supabase Integration: Cloud PostgreSQL database ✅
  - Modelos SQLAlchemy: `UserEntity`, `CodeReviewEntity`, `AgentFindingEntity`
  - Migración Alembic `ba48c1bb8e18` aplicada
  - Persistencia de análisis verificada: `1754e5ab-b6a1-4dce-997a-e3e6f485f43c`

**Próximas Historias**:
- [ ] Actualizar

**Objetivos**: Despliegue

### Sprint 3 (18 Nov - 1 Dic) 📅 PLANIFICADO

- ✅ Integración Gemini 1.5 Flash (desarrollo)
- ✅ Servidores MCP: OWASP, CVE, KB
- ✅ Frontend React con visualizaciones
- ✅ Explicaciones IA para hallazgos

### Sprint 4 (2-15 Dic) 📅 PLANIFICADO

- ✅ Auto-corrección con parches
- ✅ Dashboard de métricas históricas
- [ ] Deployment en Railway/Render

---

## 👥 Equipo

**Proyecto Académico - Universidad Nacional de Colombia**
**Curso**: Ingeniería de Software II 2025-II

### Integrantes

| Nombre | GitHub | Rol |
|--------|--------|-----|
| Jorge Andrés Mora León | [@aiizedev](https://github.com/aiizedev) | DevOps / Backend |
| John Alejandro Pastor Sandoval | [@jpastor1649](https://github.com/jpastor1649) | Backend |
| David Fernando Benjumea Mora | [@DavidFBM](https://github.com/DavidFBM) | Backend |
| Juan Sebastián Muñoz Lemus | [@jumunozle](https://github.com/jumunozle) | Frontend |
| Juan Carlos Andrade Unigarro | [@Yosoyepa](https://github.com/Yosoyepa) | DevOps |

### Profesores

- **Ing. Liliana Marcela Olarte, M.Sc.**

---

## 📚 Documentación Adicional

- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Guía completa de contribución
- **[backend/README.md](backend/README.md)**: Documentación específica del backend
- **[docs/ci-cd-setup.md](docs/ci-cd-setup.md)**: Configuración detallada de CI/CD
- **[docs/CodeGuardUnalDesignBeta.pdf](docs/CodeGuardUnalDesignBeta.pdf)**: Diseño del sistema
- **[API Docs](http://localhost:8000/docs)**: Documentación interactiva (Swagger UI)

---

## 🔗 Enlaces Útiles

- **Repository**: [GitHub](https://github.com/Yosoyepa/CodeGuardAI)
- **Issues**: [GitHub Issues](https://github.com/Yosoyepa/CodeGuardAI/issues)
- **Projects**: [GitHub Projects](https://github.com/Yosoyepa/CodeGuardAI/projects)
- **Releases**: [v1.0.0](https://github.com/Yosoyepa/CodeGuardAI/releases/tag/v1.0.0)
- **Slack**: #codeguard-dev
- **Email**: codeguard-ai@unal.edu.co

---

## 📊 Badges de Estado

| Métrica | Estado |
|---------|--------|
| **CI/CD Pipeline** | ![Status](https://img.shields.io/badge/status-passing-brightgreen) |
| **Code Coverage** | ![Coverage](https://img.shields.io/badge/coverage-75%25-yellowgreen) |
| **Code Quality** | ![Pylint](https://img.shields.io/badge/pylint-8.5%2B-green) |
| **Python Version** | ![Python](https://img.shields.io/badge/python-3.11%2B-blue) |
| **License** | ![License](https://img.shields.io/badge/license-MIT-blue) |

---

## 📜 Licencia

Este proyecto está licenciado bajo la **Licencia MIT**. Ver [LICENSE](LICENSE) para detalles completos.

---

<div align="center">
  <p>Construido con ❤️ por el equipo de CodeGuard AI</p>
  <p>Universidad Nacional de Colombia - Ingeniería de Software II 2025-II</p>
  <p>Última actualización: <strong>6 de Noviembre de 2025</strong></p>
</div>


