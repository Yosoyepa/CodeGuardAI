# 🌐 Infraestructura y Datos: Análisis Profundo (`backend/src`)

Este documento disecciona los módulos que conectan la aplicación con el mundo exterior (`external`), definen la estructura de datos (`models`) y proveen utilidades críticas (`utils`).

---

## 1. External (`src/external/`)

Aquí reside el código que "habla" con APIs de terceros. Usamos el patrón **Adapter** para que nuestra aplicación no dependa directamente de las librerías externas.

### 📄 `clerk_client.py` (Autenticación)

Maneja la validación de tokens JWT de Clerk.

#### Análisis Línea por Línea

```python
class ClerkClient:
    _jwks_cache: Optional[Dict[str, Any]] = None
```
*   **Cache de Clase**: `_jwks_cache` es una variable estática (compartida por todas las instancias). Guardamos las claves públicas de Clerk aquí para no descargarlas en cada petición HTTP.

```python
    def __init__(self):
        self._jwks_url = settings.CLERK_JWKS_URL
        self._signing_key = settings.CLERK_JWT_SIGNING_KEY or settings.CLERK_SECRET_KEY
```
*   **Flexibilidad**: Soporta dos modos de operación.
    1.  **JWKS URL**: Para tokens RS256 (asimétricos, estándar de Clerk).
    2.  **Signing Key**: Para tokens HS256 (simétricos, custom templates).

```python
    def _get_token_algorithm(self, token: str) -> str:
        unverified_header = jwt.get_unverified_header(token)
        return unverified_header.get("alg")
```
*   **Detección Automática**: Antes de validar, leemos el header del token (que no está encriptado, solo codificado en Base64) para saber qué algoritmo usa (`alg`). Esto permite que el cliente se adapte dinámicamente.

### 📄 `gemini_client.py` (Inteligencia Artificial)

Cliente para Google Vertex AI.

#### Análisis Línea por Línea

```python
class VertexAIClient(AIClient):
    def __init__(self):
        self._model: Optional[GenerativeModel] = None
        self._initialized: bool = False
```
*   **Lazy Initialization**: En el constructor (`__init__`) **NO** conectamos a Google. Solo inicializamos variables en `None`.
    *   *¿Por qué?* Si las credenciales de Google fallan, no queremos que la aplicación entera se caiga al arrancar. Solo fallará cuando intentemos usar la IA.

```python
    def _initialize(self) -> None:
        if self._initialized: return
        
        vertexai.init(project=ai_settings.GCP_PROJECT_ID, location=ai_settings.GCP_LOCATION)
        self._model = GenerativeModel(ai_settings.model_name)
```
*   **Singleton Implícito**: Una vez inicializado (`_initialized = True`), reutilizamos la conexión y el modelo cargado para siempre.

---

## 2. Models (`src/models/`)

Definición de tablas de base de datos con SQLAlchemy.

### 📄 `user.py`

```python
class UserEntity(Base):
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)
```
*   **ID String**: Usamos `String` en lugar de `Integer` o `UUID` porque el ID viene de Clerk (ej. `user_2N...`). Es una clave foránea externa.

```python
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
```
*   **Enums en BD**: SQLAlchemy mapea el Enum de Python a un tipo ENUM nativo de PostgreSQL. Esto garantiza integridad de datos: la base de datos rechazará cualquier valor que no sea 'ADMIN' o 'DEVELOPER'.

```python
    def can_analyze(self, max_daily: int = 10) -> bool:
        if self.role == UserRole.ADMIN: return True
        
        today = date.today()
        if self.last_analysis_date != today: return True
        return self.daily_analysis_count < max_daily
```
*   **Rich Model (Modelo Rico)**: En lugar de tener esta lógica dispersa en un servicio ("si es admin, dejalo pasar..."), el propio objeto `User` sabe si puede analizar o no. Esto es Programación Orientada a Objetos pura.

### 📄 `finding.py`

```python
class AgentFindingEntity(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```
*   **UUIDs**: Usamos UUID v4 para los IDs de los hallazgos. Esto permite generar el ID en el código Python antes de guardar en la BD, lo cual es útil para sistemas distribuidos.

```python
    metrics = Column(JSONB, nullable=True)
    ai_explanation = Column(JSONB, nullable=True)
```
*   **JSONB (PostgreSQL)**: Usamos JSON Binario.
    *   *Ventaja*: Podemos guardar estructuras complejas (ej. métricas de Radon que varían) sin crear 20 columnas nuevas.
    *   *Performance*: A diferencia de `JSON` (texto), `JSONB` permite indexar campos internos y hacer búsquedas rápidas.

---

## 3. Utils (`src/utils/`)

### 📄 `encryption/aes_encryptor.py`

Implementa la seguridad de datos en reposo.

#### Análisis Línea por Línea

```python
from cryptography.fernet import Fernet

_KEY = os.getenv("ENCRYPTION_SECRET_KEY", Fernet.generate_key().decode())
_CIPHER = Fernet(_KEY.encode())
```
*   **Fernet**: Es una implementación de criptografía simétrica (AES-128 en modo CBC con firma HMAC-SHA256). Garantiza que el mensaje no solo está encriptado, sino que **no ha sido modificado** (integridad).
*   **Gestión de Claves**:
    *   Intenta leer `ENCRYPTION_SECRET_KEY` del `.env`.
    *   Si no existe, genera una clave aleatoria (`Fernet.generate_key()`).
    *   *Advertencia*: Si usas la clave generada, al reiniciar el servidor se perderá y no podrás desencriptar nada. ¡En producción es obligatorio configurar la variable de entorno!

```python
def encrypt_aes256(content: str) -> bytes:
    if not content: raise ValueError(...)
    return _CIPHER.encrypt(content.encode("utf-8"))
```
*   **Bytes vs String**: La encriptación trabaja con bytes. Por eso hacemos `.encode("utf-8")` antes de encriptar. El resultado son bytes que SQLAlchemy guardará en una columna `LargeBinary` o `Bytea`.

---

## 🔄 Resumen de Arquitectura de Datos

1.  **External**: Protege al núcleo de cambios en APIs externas (Clerk, Google). Si Google cambia su SDK, solo tocamos `gemini_client.py`.
2.  **Models**: Define la verdad de los datos. Usa tipos avanzados de PostgreSQL (`JSONB`, `ENUM`, `UUID`) para robustez y performance.
3.  **Utils**: Provee herramientas de bajo nivel (encriptación) que son usadas transversalmente por Repositorios y Servicios.
