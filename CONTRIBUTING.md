# 🤝 Guía de Contribución - CodeGuard AI

¡Gracias por tu interés en contribuir a **CodeGuard AI**! Este documento te guía a través del flujo de trabajo para colaborar efectivamente en el proyecto.

---

## 📋 Tabla de Contenidos

- [Código de Conducta](#-código-de-conducta)
- [Cómo Contribuir](#-cómo-contribuir)
- [Flujo de Trabajo GitFlow](#-flujo-de-trabajo-gitflow)
- [Convenciones de Commits](#-convenciones-de-commits)
- [Estándares de Calidad](#-estándares-de-calidad)
- [Proceso de Pull Request](#-proceso-de-pull-request)
- [Configuración del Entorno](#-configuración-del-entorno)
- [Testing](#-testing)
- [Reportar Bugs](#-reportar-bugs)
- [Sugerir Mejoras](#-sugerir-mejoras)

---

## 📜 Código de Conducta

Este proyecto y todos los participantes están regidos por nuestro **Código de Conducta**. Por favor:

- ✅ Sé respetuoso y empático con otros contribuidores
- ✅ Acepta críticas constructivas con gracia
- ✅ Enfócate en lo que es mejor para la comunidad
- ✅ Muestra cortesía hacia diferentes puntos de vista

**Para reportar comportamientos inaceptables**, contáctanos en:
📧 `codeguard-ai@unal.edu.co`

---

## 🚀 Cómo Contribuir

### Tipos de Contribuciones

1. **🐛 Reportar Bugs**: Identifica y documenta errores
2. **✨ Implementar Features**: Desarrolla nuevas funcionalidades
3. **📝 Mejorar Documentación**: Actualiza o crea documentación
4. **🧪 Escribir Tests**: Aumenta la cobertura de pruebas
5. **🎨 Refactorizar Código**: Mejora la estructura sin cambiar funcionalidad
6. **⚡ Optimizar Rendimiento**: Mejora velocidad o uso de recursos

### Antes de Empezar

1. ✅ **Revisa el backlog**: Ve a [GitHub Issues](https://github.com/YOUR_ORG/CodeGuard-Unal/issues)
2. ✅ **Busca issue abierto**: Verifica que no esté duplicado
3. ✅ **Asigna el issue**: Comenta que deseas trabajar en él
4. ✅ **Lee la documentación**: Familiarízate con la arquitectura

---

## 🔀 Flujo de Trabajo GitFlow

CodeGuard AI utiliza **GitFlow** como estrategia de branching. Este modelo define ramas para diferentes propósitos.

### Estructura de Ramas

```
main (producción)
  └─ Etiquetas: v1.0.0, v1.1.0
       ↑ (merges desde release/* y hotfix/*)
       
develop (integración)
  └─ Rama principal de desarrollo
       ↑ (merges desde feature/*, bugfix/*, hotfix/*)
       
feature/* (features nuevas)
  ├─ feature/CGAI-12-base-agent
  ├─ feature/CGAI-19-security-agent
  └─ feature/CGAI-20-fastapi-endpoint
  
bugfix/* (bugs en develop)
  └─ bugfix/CGAI-99-fix-orchestrator-timeout
  
hotfix/* (bugs críticos en main)
  └─ hotfix/CGAI-98-security-patch
  
release/* (preparación de releases - Sprint 2+)
  └─ release/v1.1.0
```

### Crear Feature Branch

```bash
# 1. Asegúrate que develop esté actualizado
git checkout develop
git pull origin develop

# 2. Crear feature branch (formato: feature/CGAI-XX-descripcion-corta)
git checkout -b feature/CGAI-19-security-agent

# 3. Hacer cambios y commits
# ... trabajar en el código ...

# 4. Mantener actualizado con develop
git fetch origin
git rebase origin/develop

# 5. Push
git push -u origin feature/CGAI-19-security-agent

# 6. Crear PR en GitHub
```

### Crear Bugfix Branch (bugs en develop)

```bash
git checkout develop
git pull origin develop
git checkout -b bugfix/CGAI-99-fix-description
# ... hacer cambios ...
git push -u origin bugfix/CGAI-99-fix-description
```

### Crear Hotfix Branch (bugs críticos en main)

```bash
# Los hotfix se ramifican desde main
git checkout main
git pull origin main
git checkout -b hotfix/CGAI-98-critical-fix

# Hacer fix y commit
git commit -m "fix(agents): patch critical vulnerability

[descripción del fix]"

# Merge a main
git checkout main
git merge --no-ff hotfix/CGAI-98-critical-fix
git push origin main

# Merge también a develop
git checkout develop
git merge --no-ff hotfix/CGAI-98-critical-fix
git push origin develop
```

### Release Branch (Sprint 2+)

```bash
# Para preparar una versión
git checkout develop
git checkout -b release/v1.1.0

# En release solo se corrigen bugs, no se agregan features
git commit -m "bump version to 1.1.0"

# Merge a main con tag
git checkout main
git merge --no-ff release/v1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags
```

---

## 📝 Convenciones de Commits

CodeGuard AI sigue **Conventional Commits** para mantener un historial limpio y automatizable.

### Formato

```
<tipo>(<scope>): <descripción>

[cuerpo opcional]

[footer(s) opcional(es)]
```

### Tipos de Commits

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(security): add hardcoded credentials detection` |
| `fix` | Corrección de bug | `fix(api): handle null pointer in analyze endpoint` |
| `docs` | Cambios en documentación | `docs(readme): update installation steps` |
| `style` | Formato (sin cambio lógico) | `style(code): format with black` |
| `refactor` | Refactorización sin cambiar funcionalidad | `refactor(agents): extract logging method` |
| `test` | Agregar o modificar tests | `test(security): add unit tests for eval detection` |
| `chore` | Mantenimiento, dependencias | `chore(deps): update pytest to 8.0` |
| `perf` | Mejora de rendimiento | `perf(analysis): optimize AST parsing` |
| `ci` | Cambios en CI/CD | `ci(github): add coverage reporting` |

### Scopes Comunes

```
agents, security, quality, performance, style, orchestrator
api, schemas, routers, services, core, database
auth, cache, events, config, dependencies
docker, ci, tests, docs
```

### Ejemplos Correctos

```bash
# Feature simple
git commit -m "feat(security): add SQL injection detection"

# Bug fix
git commit -m "fix(api): return 422 for invalid filename"

# Con cuerpo
git commit -m "feat(agents): implement quality metrics calculation

- Add cyclomatic complexity calculation
- Add code duplication detection
- Add test coverage computation
- Related to CGAI-20"

# Breaking change
git commit -m "feat(api)!: change analyze response format

BREAKING CHANGE: response now uses 'analysis_id' instead of 'id'"

# Multiple scopes
git commit -m "refactor(core,services): improve dependency injection

- Simplify container initialization
- Add lazy loading for services
- Update documentation"
```

### ❌ Ejemplos Incorrectos

```bash
# Falta tipo
git commit -m "add new feature"

# Tipo incorrecto
git commit -m "Feature: add new agent"

# Descripción muy vaga
git commit -m "fix: fixes bug"

# Mayúscula al inicio
git commit -m "feat: Add new endpoint"

# Punto al final
git commit -m "feat(security): add detection."

# Demasiado largo (>72 caracteres)
git commit -m "feat(api): implement a very comprehensive analysis system for detecting all types of vulnerabilities"
```

### Reglas de Formato

| Regla | Detalle |
|-------|---------|
| **Primera línea** | Máximo 72 caracteres |
| **Cuerpo** | Máximo 100 caracteres por línea |
| **Tipo** | En minúscula |
| **Scope** | En minúscula (opcional) |
| **Descripción** | Comienza en minúscula, modo imperativo |
| **Punto final** | Sin punto en la primera línea |

---

## ✅ Estándares de Calidad

### 1. Linting (Pylint ≥ 8.5/10)

```bash
cd backend

# Ejecutar pylint
pylint src/ --rcfile=.pylintrc

# Verificar score
pylint src/ --rcfile=.pylintrc | grep -E "rated at"
```

**Configuración** (`.pylintrc`):
```ini
[MASTER]
max-line-length=100
disable=C0111,C0103,R0903

[MESSAGES CONTROL]
disable=missing-docstring,too-few-public-methods
```

### 2. Testing (Coverage ≥ 75%)

```bash
cd backend

# Ejecutar tests con cobertura
pytest tests/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=75 \
  -v
```

### 3. Formateo (Black + isort)

```bash
cd backend

# Formatear código
black src/ tests/ --line-length=100
isort src/ tests/ --profile=black

# Verificar sin modificar
black --check src/ tests/
isort --check-only src/ tests/
```

### 4. Type Hints (Obligatorio para métodos públicos)

```python
# ✅ Correcto
def analyze(self, context: AnalysisContext) -> List[Finding]:
    """Analyze code and return findings."""
    pass

# ❌ Incorrecto
def analyze(self, context):
    return []
```

### 5. Docstrings (Obligatorio para clases y métodos públicos)

```python
# ✅ Correcto
class SecurityAgent(BaseAgent):
    """
    Agent for detecting security vulnerabilities.
    
    Analyzes Python code for:
    - Dangerous functions (eval, exec)
    - SQL injection patterns
    - Hardcoded credentials
    """
    
    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """
        Analyze code for security issues.
        
        Args:
            context: Analysis context with code and metadata
            
        Returns:
            List of security findings
        """
        pass

# ❌ Incorrecto
class SecurityAgent(BaseAgent):
    def analyze(self, context):
        pass
```

---

## 🔄 Proceso de Pull Request

### Antes de Crear el PR

```bash
cd backend

# 1. Verificar linting
pylint src/ --rcfile=.pylintrc

# 2. Ejecutar tests localmente
pytest tests/ --cov=src --cov-fail-under=75

# 3. Formatear código
black src/ tests/ --line-length=100
isort src/ tests/ --profile=black

# 4. Verificar commits
git log --oneline -5
# Todos deben tener formato: tipo(scope): descripcion

# 5. Rebase con develop (si es necesario)
git fetch origin
git rebase origin/develop
```

### Crear Pull Request

1. **Push de la rama**:
```bash
git push -u origin feature/CGAI-19-security-agent
```

2. **Crear PR en GitHub**:
   - Base: `develop` (o `main` para hotfixes)
   - Compare: tu rama

3. **Completar la plantilla del PR**:

```markdown
## 📝 Descripción
Implementa detección de credenciales hardcodeadas en SecurityAgent para identificar contraseñas, API keys y tokens en código Python.

## 🎯 Historia de Usuario Relacionada
Closes #19 (CGAI-19: SecurityAgent v1)

## 🧪 Cómo se Probó
- [x] Tests unitarios agregados (15 nuevos tests)
- [x] Tests de integración con AnalysisService
- [x] Probado manualmente con código malicioso
- [x] Cobertura: 88% (cumple umbral 75%)

## ✅ Checklist Previo al Merge
- [x] Mi código sigue las convenciones del proyecto
- [x] He agregado tests que prueban mis cambios
- [x] Todos los tests pasan localmente (`pytest`)
- [x] He actualizado la documentación relevante
- [x] Mis commits siguen Conventional Commits
- [x] He hecho rebase con develop
- [x] He ejecutado linting localmente
- [x] He verificado coverage >75%

## 📸 Screenshots (si aplica)
N/A

## 📚 Notas Adicionales
- Implementa detección con regex patterns
- Detecta placeholders (YOUR_, REPLACE_) para evitar falsos positivos
- Integrado con EventBus para notificaciones en tiempo real
- Compatible con Python 3.11+
```

### Revisión de Código

**Requisitos para merge**:
1. ✅ **CI Passing**: Los 3 workflows en verde
   - `lint.yml`: Pylint ≥ 8.5/10
   - `test.yml`: Tests passing + coverage ≥ 75%
   - `docker.yml`: Build exitoso

2. ✅ **1+ Aprobación**: Al menos un reviewer

3. ✅ **Conflicts Resolved**: Sin conflictos con base

**Proceso**:
- Revisor deja comentarios en líneas específicas
- Autor responde y hace cambios
- Push de commits adicionales (NO force push)
- Revisor aprueba cuando cambios son satisfactorios

### Merge del PR

```bash
# Merge strategy: Squash (por defecto para features)
# Esto combina todos los commits en uno solo

# Mensaje de merge sugerido:
feat(security): detect hardcoded credentials (#19)

- Implement regex-based credential detection
- Add placeholders to avoid false positives
- Integrate with event system
- Add comprehensive unit tests (88% coverage)

Closes CGAI-19
```

**Después del merge**:
```bash
# Branch se elimina automáticamente en GitHub
# O manualmente:
git branch -d feature/CGAI-19-security-agent
git push origin --delete feature/CGAI-19-security-agent
```

---

## 🛠️ Configuración del Entorno

### Requisitos Previos

- Python 3.11+
- Git
- Docker (opcional)
- VSCode o PyCharm

### Instalación

```bash
# 1. Fork y clonar
git clone https://github.com/YOUR_USERNAME/CodeGuard-Unal.git
cd CodeGuard-Unal/backend

# 2. Agregar remote upstream
git remote add upstream https://github.com/YOUR_ORG/CodeGuard-Unal.git

# 3. Entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 4. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Pre-commit hooks
pip install pre-commit
pre-commit install

# 6. Copiar .env
cp .env.example .env
```

### Pre-commit Hooks (Validación Automática)

Los pre-commit hooks ejecutan validaciones automáticamente antes de cada commit.

**Archivo**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/PyCQA/pylint
    rev: v3.0.0
    hooks:
      - id: pylint
        args: [--rcfile=.pylintrc, --fail-under=8.5]
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
cd backend

# Todos los tests
pytest tests/ -v

# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integración
pytest tests/integration/ -v

# Con cobertura detallada
pytest tests/ --cov=src --cov-report=term-missing

# HTML report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Estructura de Tests

```
backend/tests/
├── unit/                      # Tests de componentes aislados
│   ├── test_base_agent.py
│   ├── test_security_agent.py
│   └── ...
├── integration/               # Tests de interacción entre componentes
│   ├── test_analysis_service.py
│   └── test_security_agent_integration.py
├── e2e/                       # Tests end-to-end
│   └── test_complete_analysis.py
├── fixtures/                  # Mock data
│   ├── mock_data.py
│   └── sample_code.py
└── conftest.py               # Pytest fixtures
```

### Escribir Tests

```python
import pytest
from src.agents.security_agent import SecurityAgent
from src.schemas.analysis import AnalysisContext

class TestSecurityAgent:
    """Test suite for SecurityAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance"""
        return SecurityAgent()
    
    def test_detect_eval(self, agent):
        """Test detection of eval() function"""
        code = "result = eval(user_input)"
        context = AnalysisContext(
            code_content=code,
            filename="test.py"
        )
        
        findings = agent.analyze(context)
        
        assert len(findings) >= 1
        assert any(f.issue_type == "dangerous_function" for f in findings)
```

---

## 🐛 Reportar Bugs

### Antes de Reportar

1. Busca issues existentes duplicados
2. Reproduce el bug consistentemente
3. Recopila información: OS, Python version, logs

### Template de Issue para Bugs

```markdown
## 🐛 Descripción del Bug
Descripción clara y concisa del problema.

## 🔄 Pasos para Reproducir
1. Cargar archivo con 'eval'
2. Llamar POST /api/v1/analyze
3. Observar que no se detecta eval

## ✅ Comportamiento Esperado
El SecurityAgent debería detectar eval con severity=critical

## ❌ Comportamiento Actual
El análisis retorna 0 findings

## 📋 Contexto
- OS: Ubuntu 22.04
- Python: 3.11.5
- Branch: develop

## 📝 Logs
\`\`\`
[ERROR] AST parsing failed for test.py
Traceback...
\`\`\`
```

---

## ✨ Sugerir Mejoras

### Template de Feature Request

```markdown
## ✨ Descripción
Agregar soporte para detección de SSRF (Server-Side Request Forgery)

## 🎯 Problema que Resuelve
SSRF está en OWASP Top 10 y no está detectado actualmente

## 💡 Solución Propuesta
- Detectar urllib/requests sin validación
- Identificar patrones como requests.get(user_input)
- Sugerir listas blancas de dominios

## 🔄 Alternativas Consideradas
- Integrar Bandit con regla B310
- Custom regex patterns
```

---

## 💬 Preguntas?

- **Slack**: [#codeguard-dev](https://codeguard-unal.slack.com)
- **Email**: codeguard-ai@unal.edu.co
- **Office Hours**: Martes y Jueves 2-4 PM (COT)
- **Issues**: [GitHub Issues](https://github.com/YOUR_ORG/CodeGuard-Unal/issues)

---

<div align="center">
  <p>Gracias por contribuir a CodeGuard AI ❤️</p>
  <p>Juntos hacemos mejores desarrolladores y código más seguro</p>
</div>
