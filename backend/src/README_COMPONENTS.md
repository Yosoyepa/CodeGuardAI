# 🧠 Componentes de Negocio: Análisis Profundo (`backend/src`)

Este documento ofrece una disección quirúrgica de los componentes que implementan la lógica de negocio de CodeGuard AI. Se explica el código línea por línea para garantizar una comprensión total del funcionamiento interno.

---

## 1. Servicios (`src/services/`)

La capa de servicios orquesta la lógica de negocio. No maneja HTTP (eso es para Routers) ni SQL (eso es para Repositories).

### 📄 `analysis_service.py`

Este es el cerebro de la operación. Coordina la recepción del archivo, la ejecución de agentes y el guardado de resultados.

#### Análisis Línea por Línea

```python
class AnalysisService:
    def __init__(self, repo: CodeReviewRepository):
        self.repo = repo
        self.event_bus = EventBus()
```
*   **Inyección de Dependencias**: Recibe `repo` en el constructor. Esto permite que, en los tests, le pasemos un `FakeRepository` que no toque la base de datos real.
*   **EventBus**: Instancia el bus de eventos para poder notificar "Empecé a analizar" sin bloquear el proceso.

```python
async def analyze_code(self, file: UploadFile, user_id: str) -> CodeReview:
    logger.info(f"Iniciando análisis para usuario {user_id}...")
    
    # 1. Validación (RN4)
    content, filename = await self._validate_file(file)
```
*   **`async def`**: Define una corrutina. Vital porque vamos a hacer operaciones de I/O (leer archivo, base de datos) y no queremos congelar el servidor mientras esperamos.
*   **`_validate_file`**: Método privado (encapsulamiento) que contiene la lógica "sucia" de verificar extensiones y tamaños.

```python
    # 2. Contexto
    analysis_id = uuid4()
    context = AnalysisContext(
        code_content=content,
        filename=filename,
        analysis_id=analysis_id,
        metadata={"user_id": user_id},
    )
```
*   **`AnalysisContext`**: Empaquetamos todo lo que los agentes necesitan saber en un solo objeto. Si mañana necesitamos pasar también el `project_id`, solo modificamos este objeto, no la firma de todos los métodos de los agentes.

```python
    self.event_bus.publish(AnalysisEventType.ANALYSIS_STARTED, {"id": str(analysis_id)})
```
*   **Desacoplamiento**: El servicio "grita" que empezó. No le importa si hay un WebSocket escuchando o un sistema de logs.

```python
    # 3. Ejecución de Agentes
    findings: List[Finding] = []
    try:
        security_agent = SecurityAgent()
        security_findings = security_agent.analyze(context)
        findings.extend(security_findings)
    except Exception as e:
        logger.error(...)
```
*   **Manejo de Fallos Parciales**: Cada agente está envuelto en un `try/except`. Si el `SecurityAgent` explota, el análisis **continúa** con los otros agentes. No queremos que un error en una regla de estilo aborte todo el proceso de seguridad.

---

### 📄 `mcp_context_enricher.py`

Este servicio implementa un patrón RAG (Retrieval-Augmented Generation) local.

#### Análisis Línea por Línea

```python
@dataclass
class EnrichedContext:
    finding: Finding
    security_context: Optional[SecurityContext]
    formatted_prompt_context: str
    has_security_context: bool
```
*   **`@dataclass`**: Crea una estructura de datos inmutable. Es más ligero que una clase normal y genera automáticamente `__init__` y `__repr__`.
*   **Propósito**: Guardar el resultado de "enriquecer" un hallazgo. No modificamos el objeto `Finding` original (principio de inmutabilidad), sino que creamos un envoltorio con la info extra.

```python
class MCPContextEnricher:
    def __init__(self, mcp_client: Optional[MCPClient] = None):
        self._mcp_client = mcp_client or get_mcp_client()
```
*   **Inyección Opcional**: Permite pasar un cliente mock para tests (`mcp_client=Mock()`). Si no se pasa nada, usa el real (`get_mcp_client()`).

```python
    async def enrich(self, finding: Finding) -> EnrichedContext:
        security_context = await self._mcp_client.get_security_context(finding)
```
*   **Búsqueda Semántica (Simulada)**: El cliente MCP busca en el diccionario OWASP si el `issue_type` del hallazgo (ej. "sql_injection") tiene una definición oficial.

---

## 2. Repositorios (`src/repositories/`)

Encargados de hablar con la Base de Datos. Transforman Objetos de Dominio (Pydantic) a Entidades (SQLAlchemy).

### 📄 `code_review_repository.py`

#### Análisis Línea por Línea

```python
def create(self, review: CodeReview) -> CodeReview:
    try:
        # RN16: Encriptación
        encrypted_content = encrypt_aes256(review.code_content)
```
*   **Seguridad por Diseño**: Antes de siquiera crear el objeto entidad, encriptamos el código. `encrypt_aes256` devuelve `bytes`, no `str`.
*   **Cumplimiento**: Esto satisface requisitos de privacidad (GDPR/CCPA) donde los datos sensibles no deben ser legibles en la BD.

```python
        entity = CodeReviewEntity(
            id=review.id,
            code_content=encrypted_content,  # Guardamos bytes encriptados
            ...
        )
        self.session.add(entity)
```
*   **Unit of Work**: `session.add` solo marca el objeto para ser guardado. No se envía el SQL todavía.

```python
        for finding in review.findings:
            severity_enum = SeverityEnum[finding.severity.name]
            finding_entity = AgentFindingEntity(...)
            self.session.add(finding_entity)
            
        self.session.commit()
```
*   **Transacción Atómica**: Agregamos la revisión Y sus hallazgos. Luego hacemos `commit()`. Si falla el guardado de un hallazgo, el `rollback()` (en el bloque `except`) deshace TODO. Nunca tendremos una revisión guardada a medias.

---

## 3. Routers (`src/routers/`)

La puerta de entrada HTTP.

### 📄 `analysis.py`

```python
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_code(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
```
*   **`UploadFile`**: FastAPI usa `spooled` files. Si el archivo es pequeño, está en memoria. Si es grande, se guarda en disco temporalmente. Esto evita que una subida de 1GB consuma 1GB de RAM.
*   **`Depends(get_current_user)`**: Middleware de autenticación. Si el token es inválido, esta función ni siquiera se ejecuta.
*   **`Depends(get_db)`**: Inyección de sesión de BD.

```python
    repo = CodeReviewRepository(db)
    service = AnalysisService(repo)
    result = await service.analyze_code(file, current_user.id)
```
*   **Composición**: Aquí ensamblamos las piezas. Router -> Service -> Repository -> DB.
*   **`await`**: Esperamos a que el servicio termine. Mientras tanto, FastAPI puede atender otras peticiones.

---

## 4. Schemas (`src/schemas/`)

Definiciones de datos y validación.

### 📄 `analysis.py` (AnalysisContext)

```python
class AnalysisContext(BaseModel):
    code_content: str = Field(..., min_length=1)
    
    _ast_cache: Optional[python_ast.Module] = PrivateAttr(default=None)
```
*   **`PrivateAttr`**: Este campo NO se valida ni se serializa a JSON. Es para uso interno de la clase.
*   **Patrón Memoization**: Usamos esto para guardar el AST.

```python
    @model_validator(mode="after")
    def _normalize_code_content(self) -> "AnalysisContext":
        self.code_content = dedent(self.code_content)
        return self
```
*   **Limpieza Automática**: `dedent` elimina la sangría común a la izquierda.
    *   *Problema*: Si copias código de una función indentada, Python lanzará `IndentationError` al parsearlo.
    *   *Solución*: `dedent` lo mueve a la izquierda, haciéndolo código válido de nivel superior.

---

## 🎓 Conclusión del Módulo

Este conjunto de componentes demuestra una arquitectura **Clean (Limpia)**:
1.  **Routers** validan HTTP.
2.  **Services** ejecutan lógica.
3.  **Repositories** persisten datos.
4.  **Schemas** aseguran la integridad de los datos entre capas.

Cada línea tiene un propósito defensivo (validaciones, try/except, transacciones) o arquitectónico (inyección de dependencias, desacoplamiento).
