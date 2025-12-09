# 📘 Documentación Técnica Profunda: Sistema de Agentes (`backend/src/agents`)

Este documento proporciona una explicación exhaustiva del módulo de agentes de CodeGuard AI. Está diseñado para desarrolladores que necesitan entender no solo *qué* hace el código, sino *cómo* lo hace, qué librerías utiliza, los patrones de diseño aplicados y los conceptos avanzados de Python implementados.

---

## 🧠 Conceptos Fundamentales

Antes de profundizar en cada archivo, es crucial entender las tecnologías base:

*   **AST (Abstract Syntax Tree):** La mayoría de los agentes no leen el código como texto plano, sino que lo convierten en una estructura de árbol que representa la sintaxis lógica del programa. Usamos la librería nativa `ast` de Python.
*   **Patrones de Diseño:** Soluciones arquitectónicas estándar para problemas comunes (Singleton, Factory, Observer, Visitor).
*   **Concurrencia:** Uso de hilos (`threading`) para ejecución paralela.

---

## 1. `base_agent.py` - El Cimiento Arquitectónico

Este archivo define la **Clase Base Abstracta** de la que heredan todos los agentes.

### 📚 Librerías Clave
- **`abc` (Abstract Base Classes):** Permite definir clases que no pueden ser instanciadas directamente y obliga a las clases hijas a implementar ciertos métodos.
- **`typing`:** Uso extensivo de Type Hints (`List`, `Optional`, `TYPE_CHECKING`) para un código robusto y autodocumentado.

### 🏗️ Patrones de Diseño
1.  **Template Method Pattern:** La clase base define la estructura y comportamiento común (logging, manejo de eventos, identidad), mientras que delega la lógica específica (`analyze`) a las subclases.
2.  **Observer Pattern:** Integración con `EventBus`. El agente actúa como un "sujeto" que notifica cambios de estado (`AGENT_STARTED`, `AGENT_COMPLETED`) a los observadores (ej. WebSockets).

### 🔑 Conceptos de Código
- **`@abstractmethod`:** Decorador que convierte un método en obligatorio para las subclases. Si una subclase no lo implementa, Python lanzará un error al intentar instanciarla.
- **Inyección de Dependencias:** El `EventBus` se pasa en el constructor, desacoplando el agente del sistema de mensajería.

---

## 2. `agent_factory.py` - Gestión de Instancias

Encargado de crear y administrar los agentes.

### 📚 Librerías Clave
- **`threading`:** Provee primitivas de sincronización.
- **`importlib` (implícito):** Realiza importaciones dinámicas dentro de métodos para evitar "Circular Imports".

### 🏗️ Patrones de Diseño
1.  **Singleton Pattern:** Garantiza que solo exista **una única instancia** de la fábrica en toda la aplicación.
    - *Implementación:* Usa una variable de clase `_instance` y un `_lock` para asegurar que, incluso en entornos multi-hilo, no se creen dos fábricas.
2.  **Factory Method Pattern:** Encapsula la lógica de creación de objetos. El cliente pide un agente por su nombre ("security") y la fábrica decide qué clase instanciar (`SecurityAgent`).
3.  **Registry Pattern:** Mantiene un diccionario interno `_registry` que mapea nombres de cadena a clases (`str -> class`).

### 🔑 Conceptos de Código
- **`threading.Lock()`:** Un semáforo binario. El bloque `with cls._lock:` asegura que solo un hilo a la vez pueda ejecutar el código de creación de la instancia, previniendo condiciones de carrera (Race Conditions).
- **Lazy Loading / Dynamic Imports:** Los `import` de los agentes están *dentro* del método `_register_default_agents`. Esto evita que `agent_factory.py` importe `security_agent.py` al inicio, lo cual podría causar ciclos si `security_agent.py` necesitara importar algo de la fábrica.

---

## 3. `orchestrator.py` - El Director de Orquesta

Coordina la ejecución de múltiples agentes simultáneamente.

### 📚 Librerías Clave
- **`concurrent.futures`:** Librería moderna de alto nivel para concurrencia.
  - **`ThreadPoolExecutor`:** Administra un pool de hilos de trabajo reutilizables.
  - **`as_completed`:** Iterador que devuelve los resultados de los hilos a medida que terminan, sin esperar a que todos finalicen.

### 🏗️ Patrones de Diseño
1.  **Facade Pattern:** Provee una interfaz simple (`orchestrate_analysis`) que oculta la complejidad de gestionar hilos, timeouts y agregación de resultados.
2.  **Coordinator Pattern:** Centraliza la lógica de flujo de trabajo.

### 🔑 Conceptos de Código
- **Futures:** Un objeto `Future` representa una operación asíncrona que puede o no haber terminado. Permite consultar el estado o bloquear esperando el resultado (`future.result()`).
- **Timeouts:** El uso de `timeout=self.timeout_seconds` es crítico para evitar que un agente colgado bloquee todo el sistema indefinidamente.

---

## 4. `security_agent.py` - El Guardián (Seguridad)

Analiza el código buscando vulnerabilidades.

### 📚 Librerías Clave
- **`ast`:** Parsea el código fuente en un árbol de nodos.
- **`re`:** Motor de Expresiones Regulares para búsqueda de patrones de texto.

### ⚙️ Lógica Interna
Combina dos enfoques:
1.  **Análisis Sintáctico (AST):**
    - Usa `ast.walk(tree)` para recorrer todos los nodos del árbol.
    - Busca nodos tipo `ast.Call` (llamadas a funciones).
    - Verifica si el nombre de la función está en la lista negra (`eval`, `exec`).
    - *Ventaja:* No se confunde con comentarios o strings que contengan la palabra "eval".
2.  **Análisis Léxico (Regex):**
    - Busca patrones de texto crudo para cosas que el AST no ve fácilmente, como secretos hardcodeados (`password = "..."`).
    - *Ventaja:* Puede encontrar problemas en código sintácticamente inválido.

### 🔑 Conceptos de Código
- **Heurísticas:** Reglas prácticas para reducir falsos positivos. Ejemplo: Ignorar variables que contienen "YOUR_" o "EXAMPLE_" al buscar contraseñas.

---

## 5. `performance_agent.py` - El Optimizador (Rendimiento)

Detecta código lento o ineficiente.

### 📚 Librerías Clave
- **`ast`:** Específicamente la clase `ast.NodeVisitor`.

### 🏗️ Patrones de Diseño
1.  **Visitor Pattern:** Implementado a través de `ast.NodeVisitor`.
    - En lugar de un bucle `for` gigante (`ast.walk`), se definen métodos específicos para cada tipo de nodo: `visit_For`, `visit_Call`.
    - El visitante "camina" por el árbol y ejecuta el método correspondiente automáticamente.

### ⚙️ Lógica Interna (Stateful Analysis)
A diferencia de `SecurityAgent`, este agente **mantiene estado** mientras recorre el árbol:
- **`self.in_loop` (bool):** ¿Estoy actualmente dentro de un bucle `for` o `while`?
- **`self.loop_depth` (int):** ¿Qué tan profundo es el anidamiento?

**Ejemplo de detección O(n²):**
1. Entra a un `visit_For`. Incrementa `loop_depth` a 1.
2. Encuentra otro `visit_For` adentro. Incrementa `loop_depth` a 2.
3. Detecta que `loop_depth > 1` -> Reporta complejidad cuadrática.
4. Sale del bucle interno. Decrementa `loop_depth`.

---

## 6. `quality_agent.py` - El Inspector (Calidad)

Mide la salud del código con métricas cuantitativas.

### 📚 Librerías Clave
- **`radon`:** Librería externa estándar para métricas de código Python.
  - `cc_visit_ast`: Calcula Complejidad Ciclomática (caminos lógicos).
  - `mi_visit`: Calcula Índice de Mantenibilidad (fórmula matemática basada en Halstead metrics).

### ⚙️ Lógica Interna
- **Detección de Duplicación (Rolling Hash simplificado):**
  - Divide el código en bloques de N líneas (ventana deslizante).
  - Calcula el `hash()` del contenido de texto del bloque.
  - Guarda los hashes en un diccionario. Si un hash se repite, hay código duplicado.
  - *Nota:* Es una implementación ingenua O(N*M) que puede ser lenta en archivos gigantes.

---

## 7. `style_agent.py` - El Estilista (PEP 8)

Asegura que el código sea legible y siga convenciones.

### 📚 Librerías Clave
- **`subprocess`:** Permite ejecutar comandos del sistema operativo (usado en los analyzers para llamar a `pylint` o `flake8` como procesos externos).

### ⚙️ Lógica Interna
- **Análisis Híbrido:**
  - **Interno:** Verifica longitud de línea y nombres de variables usando AST y operaciones de string simples.
  - **Externo:** Delega el trabajo pesado a herramientas maduras (`pylint`) ejecutándolas en un entorno aislado y parseando su salida de texto.

---

## 🚀 Resumen de Tecnologías

| Tecnología | Uso Principal | Archivos |
| :--- | :--- | :--- |
| **AST (Abstract Syntax Tree)** | Entender la estructura lógica del código | `security`, `performance`, `style`, `quality` |
| **Regex (`re`)** | Buscar patrones de texto (SQLi, Secretos) | `security`, `style` |
| **Threading / Futures** | Ejecución paralela de agentes | `orchestrator`, `agent_factory` |
| **Visitor Pattern** | Recorrido eficiente y organizado del AST | `performance_agent` |
| **Singleton** | Gestión única de recursos | `agent_factory` |
| **Radon** | Cálculo matemático de métricas | `quality_agent` |

---

## ⚠️ Notas Críticas para Desarrolladores

1.  **Orquestador Desconectado:** Aunque `orchestrator.py` implementa una lógica paralela robusta, el servicio principal (`AnalysisService`) no lo está invocando. Actualmente, los agentes corren uno tras otro.
2.  **PerformanceAgent Apagado:** La línea que registra este agente en `agent_factory.py` está comentada. Las reglas de rendimiento no se están aplicando.
3.  **Inyección de EventBus:** Para que los WebSockets funcionen, es vital pasar la instancia de `EventBus` al crear los agentes. Actualmente, esto falta en varios puntos de instanciación.
