# 📘 Documentación Técnica Profunda: Módulo Core (`backend/src/core`)

Este documento es una guía exhaustiva para entender la infraestructura base de CodeGuard AI. Está diseñado para explicar no solo *qué* hace el código, sino *por qué* se eligieron ciertas librerías, qué significan los imports y cómo funcionan los patrones de diseño implementados.

---

## 🧠 Conceptos y Librerías Fundamentales

Antes de ver los archivos, entendamos las herramientas que construyen este módulo.

### 1. Pydantic y `pydantic-settings`
*   **¿Qué es?**: Una librería de validación de datos.
*   **¿Por qué la usamos en `config/`?**: En lugar de usar `os.getenv("DB_URL")` y obtener un string crudo (o `None`), Pydantic nos permite definir una clase `Settings`.
*   **Beneficio**: Si la variable de entorno falta o tiene el tipo incorrecto (ej. un string en lugar de un int para el puerto), la aplicación **falla al iniciar** con un error claro. Esto previene errores silenciosos en producción.
*   **Conceptos Clave**:
    *   `BaseSettings`: Clase madre que sabe leer `.env`.
    *   `Field`: Permite añadir metadatos (descripción, validaciones `ge=0` para números positivos).
    *   `computed_field`: Valores que se calculan automáticamente basados en otros.

### 2. SQLAlchemy (ORM)
*   **¿Qué es?**: Object Relational Mapper. Traduce clases de Python a tablas SQL.
*   **Conceptos Clave en `database.py`**:
    *   `Engine`: El gestor de conexiones (Connection Pool). Mantiene varias conexiones abiertas listas para usar.
    *   `Session`: El "espacio de trabajo" temporal. Aquí haces cambios (add, delete) y luego haces `commit` para guardarlos en la BD.
    *   `pool_pre_ping=True`: Una configuración vital. Antes de usar una conexión, verifica si la base de datos sigue ahí. Si se cayó y volvió, reconecta automáticamente.

### 3. FastAPI Dependency Injection (`Depends`)
*   **¿Qué es?**: Un sistema para "pedir" cosas que tu función necesita.
*   **¿Por qué lo usamos en `dependencies/`?**:
    *   En lugar de crear una conexión a la BD dentro de cada endpoint, le dices a FastAPI: "Necesito una sesión de BD (`db: Session = Depends(get_db)`)".
    *   FastAPI se encarga de crearla, pasártela y **cerrarla** cuando termines.

### 4. Patrón Observer (Eventos)
*   **¿Qué es?**: Un patrón de diseño donde un objeto (Sujeto) notifica a otros (Observadores) sobre cambios, sin saber quiénes son.
*   **Uso en `events/`**: Permite que el análisis de código avise "Terminé" y que el sistema de WebSockets escuche y le avise al usuario, sin que el código de análisis sepa nada de WebSockets.

---

## 📂 Análisis Archivo por Archivo

### 1. `config/settings.py` - El Cerebro de la Configuración

```python
from pydantic import Field
from pydantic_settings import BaseSettings
```

*   **Explicación**:
    *   Define la clase `Settings`.
    *   **Validación**: `API_PORT: int = Field(default=8000)` asegura que el puerto sea un número.
    *   **CORS**: `ALLOWED_ORIGINS` maneja qué dominios pueden llamar a tu API (vital para seguridad web).
    *   **Feature Flags**: `AI_ENABLED: bool` permite apagar la IA sin redeployar, solo cambiando una variable de entorno.

### 2. `config/mcp_config.py` - Base de Conocimiento Estática

```python
from dataclasses import dataclass
```

*   **`@dataclass`**: Un decorador de Python que genera automáticamente métodos como `__init__` y `__repr__`. Es como un `struct` en C o una clase POJO en Java. Se usa aquí para definir estructuras de datos inmutables (solo lectura).
*   **Contenido**: Define `OWASP_TOP_10`. No es código ejecutable, es **información**.
    *   *¿Por qué aquí?* Inyectamos este texto en el prompt de la IA. Así, cuando la IA detecta una "Inyección SQL", tiene a mano la definición exacta de OWASP para explicársela al usuario.

### 3. `events/event_bus.py` - El Bus de Mensajes (Singleton)

```python
class EventBus:
    _instance = None  # Variable de clase para guardar la única instancia

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

*   **`__new__` vs `__init__`**:
    *   `__init__` inicializa un objeto.
    *   `__new__` **crea** el objeto.
    *   Al interceptar `__new__`, controlamos la creación. Si ya existe una instancia (`_instance` no es None), devolvemos esa misma. Esto es el **Patrón Singleton**.
*   **Propósito**: Asegura que si importas `EventBus` en 10 archivos distintos, todos hablen por el mismo "canal".

### 4. `dependencies/auth.py` - El Portero (Seguridad)

```python
from fastapi.security import HTTPBearer
from src.external.clerk_client import ClerkClient
```

*   **`HTTPBearer`**: Le dice a Swagger UI (la documentación automática) que esta API usa un botón de "Authorize" con tokens Bearer.
*   **Lógica de Roles**:
    *   El código inspecciona `payload.get("public_metadata")`.
    *   Clerk (el proveedor de auth) guarda datos extra del usuario ahí. Nosotros guardamos el rol (`admin`, `developer`).
    *   Esto permite **RBAC (Role-Based Access Control)**: "Solo un admin puede borrar proyectos".

### 5. `database.py` - La Conexión a Datos

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

*   **`yield`**: Convierte la función en un **Generador**.
*   **Funcionamiento**:
    1.  FastAPI llama a `get_db()`.
    2.  Se ejecuta hasta el `yield db`. Se entrega la conexión.
    3.  FastAPI ejecuta tu endpoint (ej. guardar usuario).
    4.  Al terminar el endpoint, FastAPI vuelve a esta función y ejecuta lo que está después del `yield` (el bloque `finally`).
    5.  `db.close()` se ejecuta **siempre**, incluso si hubo error. Esto previene "fugas de conexiones" (Connection Leaks).

---

## 🏗️ Resumen de Patrones de Diseño

| Patrón | Archivo | Propósito |
| :--- | :--- | :--- |
| **Singleton** | `events/event_bus.py` | Garantizar un único canal de comunicación global. |
| **Observer** | `events/observers.py` | Desacoplar quien emite el evento de quien lo recibe. |
| **Dependency Injection** | `dependencies/` | Invertir el control: el framework provee los recursos, no la función. |
| **Repository (Implícito)** | `database.py` | Abstracción de la capa de datos (preparado para usarse). |
| **Configuration Object** | `config/settings.py` | Centralizar y validar configuración en un objeto tipado. |

---

## ⚠️ Notas para el Desarrollador

1.  **Archivos Vacíos**: `container.py` y `security.py` están vacíos. Esto es normal en fases tempranas, pero indica lugares reservados para lógica futura (ej. un contenedor DI más complejo o funciones de hashing propias).
2.  **Caché Pendiente**: La carpeta `cache/` existe pero está vacía. La infraestructura está lista para Redis (hay configuración en `settings.py`), pero falta el código que conecta y guarda datos.
