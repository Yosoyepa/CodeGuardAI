# 🔧 Documentación Técnica del Pipeline CI/CD - CodeGuard AI

Esta documentación detalla la configuración completa del pipeline de **Integración Continua / Despliegue Continuo (CI/CD)** implementado con **GitHub Actions** para CodeGuard AI.

---

## 📋 Tabla de Contenidos

- [Visión General](#-visión-general-del-pipeline)
- [Workflows Implementados](#-workflows-implementados)
- [Estructura de Directorios](#-estructura-de-archivos)
- [Protección de Ramas](#-protección-de-ramas)
- [Secretos y Variables](#-secretos-y-variables-de-entorno)
- [Configuración Detallada](#-configuración-detallada-de-workflows)
- [Badges de Estado](#-badges-de-estado)
- [Monitoreo](#-monitoreo-y-logging)
- [Troubleshooting](#-troubleshooting)
- [Mejores Prácticas](#-mejores-prácticas)

---

## 🎯 Visión General del Pipeline

El pipeline CI/CD de CodeGuard AI automatiza la **validación, testing y construcción** del código para garantizar que todos los cambios que llegan a las ramas `main` y `develop` cumplen con los estándares de calidad establecidos.

### Objetivos del Pipeline

1. ✅ **Validación Automática**: Linting, tests, build
2. ✅ **Garantía de Calidad**: Cobertura ≥75%, pylint ≥8.5/10
3. ✅ **Prevención de Regresiones**: Tests obligatorios
4. ✅ **Feedback Inmediato**: En PRs y commits
5. ✅ **Deployment Seguro**: Build validado

### Arquitectura del Pipeline

```
┌───────────────────────────────────────────────────────────┐
│             GITHUB ACTIONS WORKFLOW ORCHESTRATION         │
└───────────────────────────────────────────────────────────┘
                              ↓
         Trigger: push a rama / pull request
                              ↓
    ┌────────────────────────┬────────────────────┬──────────────┐
    ↓                        ↓                    ↓              ↓
┌──────────────┐    ┌───────────────────┐  ┌─────────────┐  ┌──────────┐
│  Lint Check  │    │  Test & Coverage  │  │ Docker Build│  │ Security │
│  (lint.yml)  │    │   (test.yml)      │  │ (docker.yml)│  │  Scan    │
└──────────────┘    └───────────────────┘  └─────────────┘  └──────────┘
    ✅/❌              ✅/❌                   ✅/❌            ✅/❌
        └────────────────────┬────────────────────┘
                              ↓
                   ┌──────────────────────┐
                   │ Branch Protection    │
                   │ Status Checks        │
                   └──────────────────────┘
                              ↓
                    Merge Allowed? ✅
```

---

## 🔄 Workflows Implementados

### 1️⃣ Workflow: Lint Check (`lint.yml`)

**Ubicación**: `.github/workflows/lint.yml`

**Propósito**: Validar que el código cumple con estándares de estilo y calidad.

**Triggers**:
- Push a ramas: `main`, `develop`, `feature/**`, `bugfix/**`, `hotfix/**`
- Pull requests hacia: `main`, `develop`

**Herramientas**:
- **Black**: Formateo de código
- **isort**: Ordenamiento de imports
- **Flake8**: Análisis de PEP 8 y errores básicos
- **Pylint**: Análisis comprehensive de código

**Configuración**:

```yaml
name: Lint Code

on:
  push:
    branches: [main, develop, "feature/**", "bugfix/**", "hotfix/**"]
    paths:
      - "backend/src/**/*.py"
      - "backend/tests/**/*.py"
      - ".github/workflows/lint.yml"
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    name: Code Quality Check
    runs-on: ubuntu-latest
    
    steps:
      # 1. Checkout código
      - uses: actions/checkout@v4
      
      # 2. Setup Python 3.11
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      
      # 3. Instalar dependencias
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install black isort flake8 pylint
          pip install -r requirements.txt
      
      # 4. Ejecutar Black (formatter)
      - name: Run Black
        run: |
          cd backend
          black src/ tests/ --line-length=100 --check
      
      # 5. Ejecutar isort
      - name: Run isort
        run: |
          cd backend
          isort src/ tests/ --profile=black --check-only
      
      # 6. Ejecutar Flake8
      - name: Run Flake8
        run: |
          cd backend
          flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
      
      # 7. Ejecutar Pylint
      - name: Run Pylint
        run: |
          cd backend
          pylint src/ --rcfile=.pylintrc --fail-under=8.5 || exit 1
          echo "✅ Pylint passed with score ≥8.5/10"
      
      # 8. Summary
      - name: Summary
        if: success()
        run: echo "✅ All lint checks passed!"
```

**Criterios de Éxito**:
- ✅ Black: Sin cambios requeridos (--check)
- ✅ isort: Imports correctamente ordenados
- ✅ Flake8: Sin errores de estilo
- ✅ Pylint: Puntuación ≥ 8.5/10

---

### 2️⃣ Workflow: Testing & Coverage (`test.yml`)

**Ubicación**: `.github/workflows/test.yml`

**Propósito**: Ejecutar tests y validar cobertura de código.

**Triggers**:
- Push a ramas: `main`, `develop`, `feature/**`, `bugfix/**`, `hotfix/**`
- Pull requests hacia: `main`, `develop`

**Servicios**:
- PostgreSQL 15 (para tests de integración)
- Redis (cache layer)

**Configuración**:

```yaml
name: Tests & Coverage

on:
  push:
    branches: [main, develop, "feature/**", "bugfix/**", "hotfix/**"]
    paths:
      - "backend/src/**/*.py"
      - "backend/tests/**/*.py"
      - "backend/requirements.txt"
      - ".github/workflows/test.yml"
  pull_request:
    branches: [main, develop]

jobs:
  test:
    name: Run Tests & Coverage
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]  # Test en múltiples versiones
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: codeguard_test
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: codeguard_test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      # 1. Checkout código
      - uses: actions/checkout@v4
      
      # 2. Setup Python
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"
      
      # 3. Instalar dependencias
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install pytest pytest-cov pytest-asyncio httpx
          pip install -r requirements.txt
      
      # 4. Ejecutar tests
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://codeguard_test:test_password@localhost:5432/codeguard_test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/ \
            --cov=src \
            --cov-report=term-missing \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=75 \
            -v
      
      # 5. Subir cobertura a Codecov
      - name: Upload to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          flags: unittests
          name: codecov-${{ matrix.python-version }}
          fail_ci_if_error: false
      
      # 6. Guardar reporte HTML
      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report-py${{ matrix.python-version }}
          path: backend/htmlcov/
          retention-days: 30
      
      # 7. Summary
      - name: Summary
        if: success()
        run: |
          echo "✅ Tests passed!"
          echo "📊 Coverage: ≥75%"
```

**Criterios de Éxito**:
- ✅ Todos los tests pasan
- ✅ Cobertura ≥ 75%
- ✅ Tests en Python 3.11 y 3.12

---

### 3️⃣ Workflow: Docker Build (`docker.yml`)

**Ubicación**: `.github/workflows/docker.yml`

**Propósito**: Validar que la imagen Docker se construye correctamente.

**Triggers**:
- Push a: `main`, `develop`
- Pull requests hacia: `main`, `develop`

**Configuración**:

```yaml
name: Docker Build

on:
  push:
    branches: [main, develop]
    paths:
      - "backend/Dockerfile"
      - "backend/docker-compose.yml"
      - "backend/requirements.txt"
      - "backend/src/**/*.py"
      - ".github/workflows/docker.yml"
  pull_request:
    branches: [main, develop]

jobs:
  build:
    name: Build & Validate Docker Image
    runs-on: ubuntu-latest
    
    steps:
      # 1. Checkout
      - uses: actions/checkout@v4
      
      # 2. Setup Docker Buildx (mejor caché)
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      # 3. Build imagen
      - name: Build Docker image
        uses: docker/build-push-action@v5
        with:
          context: backend/
          push: false
          tags: codeguard-backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      # 4. Validar docker-compose
      - name: Validate docker-compose
        run: |
          cd backend
          docker-compose config > /dev/null
          echo "✅ docker-compose.yml is valid"
      
      # 5. Test imagen (verificar que se puede ejecutar)
      - name: Test Docker image
        run: |
          docker run --rm codeguard-backend:${{ github.sha }} python --version
          docker run --rm codeguard-backend:${{ github.sha }} pip list | grep fastapi
          echo "✅ Docker image validated"
      
      # 6. Scan vulnerabilidades (Trivy)
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: codeguard-backend:${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          exit-code: 0  # No bloquea si hay advertencias
      
      # 7. Upload Trivy results
      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif
      
      # 8. Summary
      - name: Summary
        if: success()
        run: |
          echo "✅ Docker build successful"
          echo "Image: codeguard-backend:${{ github.sha }}"
```

**Criterios de Éxito**:
- ✅ Imagen Docker se construye sin errores
- ✅ Contiene Python y FastAPI
- ✅ Sin vulnerabilidades críticas

---

## 📁 Estructura de Archivos

```
.github/
├── workflows/
│   ├── lint.yml                    # Linting workflow
│   ├── test.yml                    # Testing workflow
│   ├── docker.yml                  # Docker build workflow
│   └── deploy.yml                  # (Futuro) Deployment
│
└── PULL_REQUEST_TEMPLATE.md        # Template para PRs
```

### Archivo: `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## 📝 Descripción
Descripción clara de los cambios realizados.

## 🎯 Historia de Usuario Relacionada
Closes #XX (CGAI-XX)

## 🧪 Testing
- [x] Tests unitarios agregados
- [x] Tests de integración
- [x] Coverage ≥75%

## ✅ Checklist
- [x] He seguido las convenciones de commits
- [x] He agregado tests
- [x] Todos los tests pasan
- [x] He actualizado documentación
- [x] Mi código sigue las convenciones

## 🔗 Related Issues
Closes #XX, #YY
```

---

## 🛡️ Protección de Ramas

### Rama `main` (Producción)

**Ubicación**: Settings → Branches → Add rule

**Configuración**:

| Regla | Estado |
|-------|--------|
| **Require pull request reviews** | ✅ Sí (1 aprobación) |
| **Dismiss stale PR approvals** | ✅ Sí |
| **Require status checks** | ✅ Sí: lint, test, docker |
| **Require branches up to date** | ✅ Sí |
| **Resolve conversations** | ✅ Sí |
| **Require signed commits** | ❌ No (opcional) |
| **Linear history** | ❌ No |
| **Allow force pushes** | ❌ No |
| **Allow deletions** | ❌ No |

### Rama `develop` (Integración)

**Configuración Similar a `main` pero**:
- Aprobaciones requeridas: 1 (no 2)
- Sin restricción de "quien puede pushear"

---

## 🔐 Secretos y Variables de Entorno

### Secretos Requeridos (GitHub Settings → Secrets)

| Secreto | Descripción | Requerido | Usado en |
|---------|-------------|-----------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ Tests | test.yml |
| `REDIS_URL` | Redis connection string | ✅ Tests | test.yml |
| `SUPABASE_URL` | Supabase project URL | ✅ Producción | Aplicación |
| `SUPABASE_KEY` | Supabase API key | ✅ Producción | Aplicación |

### Variables de Entorno (Públicas)

```yaml
env:
  PYTHON_VERSION: "3.11"
  REGISTRY: ghcr.io
  IMAGE_NAME: codeguard-backend
```

### Configurar Secretos

```bash
# 1. Ir a GitHub Settings → Secrets and variables → Actions
# 2. Click "New repository secret"
# 3. Name: DATABASE_URL
# 4. Value: postgresql://user:pass@localhost:5432/codeguard_db
# 5. Click "Add secret"
```

---

## ⚙️ Configuración Detallada de Workflows

### Caching de Dependencias

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
    cache: "pip"  # Cache automático de pip
```

**Ventajas**:
- ✅ Reduce tiempo de instalación de dependencias
- ✅ Acelera workflow ~2-3 minutos

### Matrix Testing (Múltiples Versiones)

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
    os: [ubuntu-latest, macos-latest]  # (Futuro)
```

**Ventajas**:
- ✅ Prueba en múltiples versiones
- ✅ Garantiza compatibilidad

### Condicionales en Steps

```yaml
- name: Deploy to production
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: echo "Deploying..."

- name: Upload artifacts
  if: always()  # Siempre, incluso si fallaron pasos anteriores
  uses: actions/upload-artifact@v4
```

---

## 📊 Badges de Estado

### Agregar Badges al README

En `README.md` (raíz del proyecto):

```markdown
[![Lint](https://github.com/YOUR_ORG/CodeGuard-Unal/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/YOUR_ORG/CodeGuard-Unal/actions/workflows/lint.yml)
[![Tests](https://github.com/YOUR_ORG/CodeGuard-Unal/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/YOUR_ORG/CodeGuard-Unal/actions/workflows/test.yml)
[![Docker](https://github.com/YOUR_ORG/CodeGuard-Unal/actions/workflows/docker.yml/badge.svg?branch=main)](https://github.com/YOUR_ORG/CodeGuard-Unal/actions/workflows/docker.yml)
```

### Generar Automáticamente

```bash
# En GitHub:
# 1. Actions → Seleccionar workflow (ej: Lint Code)
# 2. Click "..." → "Create status badge"
# 3. Seleccionar rama (main)
# 4. Copy markdown
# 5. Pegar en README.md
```

---

## 📈 Monitoreo y Logging

### Ver Logs de Workflows

```bash
# En GitHub:
# 1. Actions → Seleccionar workflow run
# 2. Jobs → Seleccionar job
# 3. Step → Expandir para ver logs detallados
```

### Debugging de Workflows

```yaml
- name: Debug info
  run: |
    echo "GitHub context:"
    echo "  ref: ${{ github.ref }}"
    echo "  sha: ${{ github.sha }}"
    echo "  event: ${{ github.event_name }}"
```

---

## 🔧 Troubleshooting

### ❌ Problema: "lint.yml" falla por formato

**Síntoma**:
```
black: error: cannot format backend/src/file.py
```

**Solución**:
```bash
cd backend
black src/ --line-length=100
git add .
git commit -m "style: format code with black"
```

### ❌ Problema: Tests fallan solo en CI

**Causas comunes**:
1. Falta variable de entorno
2. Diferencia de BD (CI usa BD limpia)
3. Race conditions en tests async

**Soluciones**:
```bash
# Verificar env vars en workflow
# Añadir fixtures para resetear BD
# Usar pytest-asyncio correctamente
pytest tests/ -v --tb=short
```

### ❌ Problema: Docker build timeout

**Solución**: Usar caché:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### ❌ Problema: Coverage no alcanza 75%

**Pasos**:
1. Generar reporte: `pytest --cov=src --cov-report=html`
2. Abrir `htmlcov/index.html`
3. Identificar archivos sin cobertura
4. Escribir tests adicionales

---

## 🎯 Mejores Prácticas

### 1. Commits Pequeños y Frecuentes

```bash
# ✅ Bien
git commit -m "feat(agents): add eval detection"
git commit -m "test(agents): add eval tests"
git commit -m "docs(readme): update examples"

# ❌ Evitar
git commit -m "Add features, fix bugs, update docs"
```

### 2. Ejecutar Tests Localmente Antes de Push

```bash
cd backend
pytest tests/ --cov=src --cov-fail-under=75
pylint src/ --rcfile=.pylintrc --fail-under=8.5
```

### 3. Mantener Workflows Rápidos

| Métrica | Objetivo |
|---------|----------|
| Lint | < 1 min |
| Tests | < 5 min |
| Docker Build | < 3 min |
| Total | < 10 min |

**Optimizaciones**:
- ✅ Cache de pip
- ✅ Cache de Docker layers
- ✅ Paralelización de tests

### 4. Revisar Logs Detallados

Ante un fallo:
1. Expandir todos los steps
2. Buscar el primer error (🔴 rojo)
3. Copiar comando y ejecutar localmente

### 5. Documentar Cambios en CI

```bash
git commit -m "ci(github): add Docker Trivy scanning

- Scan for CRITICAL and HIGH vulnerabilities
- Upload results to GitHub Security
- Non-blocking (warnings allowed)

Relates to security hardening"
```

---

## 📚 Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

<div align="center">
  <p>Documentación del Pipeline CI/CD - CodeGuard AI</p>
  <p>Universidad Nacional de Colombia - 2025</p>
  <p>Última actualización: <strong>6 de Noviembre de 2025</strong></p>
</div>
