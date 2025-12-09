# 🗺️ Arquitectura y Flujo de Datos: CodeGuard AI

Este documento explica cómo se conectan todas las piezas del sistema (`backend/src`). Es la guía definitiva para entender el flujo de una petición desde que entra hasta que sale.

---

## 🔄 El Flujo de una Petición (Request Lifecycle)

Imagina que un usuario envía un archivo para analizar. Así viaja la información:

1.  **Entrada (Main & Middleware)**:
    *   La petición llega a `main.py`.
    *   Pasa por `middleware/cors.py` (¿Viene de un origen permitido?).
    *   Pasa por `middleware/rate_limit.py` (¿Ha hecho demasiadas peticiones?).
    *   Pasa por `middleware/auth.py` (¿Tiene un token válido?). Aquí se usa `external/clerk_client.py` para validar el JWT.

2.  **Enrutamiento (Routers)**:
    *   FastAPI dirige la petición a `routers/analysis.py`.
    *   El router valida los datos de entrada usando **Schemas** (`schemas/analysis_request.py`). Si el JSON está mal formado, rechaza la petición aquí.

3.  **Lógica de Negocio (Services)**:
    *   El router llama a `services/analysis_service.py`.
    *   El servicio orquesta el trabajo:
        *   Crea un registro en la BD usando **Repositories** (`repositories/analysis_repo.py`) y **Models** (`models/code_review.py`).
        *   Llama a los **Agents** (`agents/orchestrator.py`) para escanear el código.
        *   Si la IA está activada, llama a `external/gemini_client.py` para explicar los hallazgos.

4.  **Persistencia (Repositories & Models)**:
    *   Los resultados (hallazgos) se guardan. El `AnalysisRepository` toma los objetos de dominio y los convierte en filas de la base de datos usando `models/finding.py` y la sesión de `core/database.py`.

5.  **Notificación (Events & WebSockets)**:
    *   Mientras analiza, el servicio emite eventos al `core/events/event_bus.py`.
    *   El módulo `websocket/manager.py` escucha estos eventos y envía mensajes JSON en tiempo real al frontend del usuario ("Analizando seguridad...", "Encontrado error crítico...").

---

## 🧩 Mapa de Dependencias

*   **`core/`**: Es la base. **Todos** dependen de él (configuración, BD, logs). Él no depende de nadie.
*   **`models/`**: Define la estructura de datos. Usado por Repositories y Services.
*   **`schemas/`**: Define la estructura de la API (DTOs). Usado por Routers.
*   **`repositories/`**: Abstrae la base de datos. Usado por Services.
*   **`external/`**: Abstrae APIs externas. Usado por Services y Middleware.
*   **`agents/`**: Lógica pura de análisis. Usado por Services.
*   **`services/`**: El director de orquesta. Une Repositories, Agents y External.
*   **`routers/`**: La cara pública. Une Schemas y Services.

---

## 🏗️ Diagrama Conceptual de Capas

```mermaid
graph TD
    Client[Frontend / Cliente] -->|HTTP Request| Middleware
    Middleware --> Router
    
    subgraph Application Layer
        Router -->|Valida DTO| Schema
        Router -->|Llama| Service
    end
    
    subgraph Domain Layer
        Service -->|Ejecuta| Agent[Agents (Security, Quality)]
        Service -->|Consulta| Repository
        Service -->|Usa| External[External Clients (Gemini, Clerk)]
    end
    
    subgraph Infrastructure Layer
        Repository -->|ORM| Model
        Model -->|SQL| Database[(PostgreSQL)]
        External -->|API Call| Cloud[Nube (Google, Clerk)]
    end
    
    Service -.->|Event| EventBus
    EventBus -.->|Notify| WebSocket
    WebSocket -->|Push| Client
```

---

## 🔑 Claves para Entender el Código

1.  **Separación de Responsabilidades**:
    *   Un **Router** nunca debe hablar con la BD directamente. Debe llamar a un Service.
    *   Un **Model** nunca debe tener lógica de negocio compleja (como llamar a una API).
    *   Un **Agent** solo analiza código, no sabe de bases de datos ni de usuarios.

2.  **Inyección de Dependencias**:
    *   Casi todo se pasa como argumento. El `AnalysisService` recibe el `AnalysisRepository` en su constructor (o vía FastAPI Depends). Esto hace que sea fácil de probar (Mocking).

3.  **DTOs (Schemas) vs Entidades (Models)**:
    *   **Schema (`schemas/`)**: Lo que viaja por la red (JSON). Puede tener campos extra o menos campos.
    *   **Model (`models/`)**: Lo que se guarda en la BD (Tablas).
    *   *Regla*: Nunca devuelvas un Model directamente en la API. Conviértelo a Schema primero.
