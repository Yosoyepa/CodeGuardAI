# CRC Cards - CodeGuard AI Domain Layer

> **Focus:** Core business logic classes (Agents, Entities, Value Objects, Enums)

---

## 🎯 **AGENTS (Core Analysis Logic)**

### **BaseAgent** (Abstract)

| **Class Name** | BaseAgent |
|---|---|
| **Responsibilities** | • Define common interface for all analysis agents<br>• Implement abstract `analyze(context: AnalysisContext)` method<br>• Provide agent metadata (name, version, category)<br>• Handle error logging and metrics collection<br>• Emit events via EventBus:<br>&nbsp;&nbsp;- AGENT_STARTED<br>&nbsp;&nbsp;- AGENT_COMPLETED<br>&nbsp;&nbsp;- AGENT_FAILED<br>• Parse AST from Python code |
| **Collaborators** | • **AnalysisContext** (receives as input)<br>• **Finding** (produces as output)<br>• **EventBus** (publishes events to)<br>• **AgentConfig** (configured by) |
| **Type** | Abstract Class |

---

### **SecurityAgent**

| **Class Name** | SecurityAgent |
|---|---|
| **Responsibilities** | • Parse Python code using AST module<br>• Detect dangerous functions:<br>&nbsp;&nbsp;- eval(), exec(), compile()<br>&nbsp;&nbsp;- pickle.loads(), __import__()<br>• Detect SQL injection patterns (regex)<br>• Detect hardcoded credentials (Shannon entropy analysis)<br>• Detect weak cryptography (MD5, SHA1, DES)<br>• Return list of security findings |
| **Collaborators** | • **BaseAgent** (extends)<br>• **AnalysisContext** (analyzes)<br>• **Finding** (creates)<br>• **BanditAnalyzer** (uses for static analysis) |
| **Type** | Concrete Class |

---

### **SecurityAgentEnhanced** (Sprint 3)

| **Class Name** | SecurityAgentEnhanced |
|---|---|
| **Responsibilities** | • Extends SecurityAgent with AI capabilities<br>• Filter critical findings (severity = CRITICAL)<br>• Request AI-generated explanations via AIExplainerService<br>• Attach AIExplanation objects to critical findings<br>• Implement graceful fallback if AI service unavailable<br>• Decide if finding should get AI explanation (configurable) |
| **Collaborators** | • **SecurityAgent** (extends)<br>• **AIExplainerService** (requests explanations from)<br>• **MCPContextEnricher** (enriches findings via)<br>• **Finding** (enriches with AIExplanation) |
| **Type** | Concrete Class (Decorator Pattern) |

---

### **QualityAgent**

| **Class Name** | QualityAgent |
|---|---|
| **Responsibilities** | • Calculate cyclomatic complexity using Radon library<br>• Detect code duplication (threshold: 20%)<br>• Measure function length (threshold: 100 lines)<br>• Calculate maintainability index (Radon MI)<br>• Flag functions exceeding complexity threshold (default: 10)<br>• Return quality findings |
| **Collaborators** | • **BaseAgent** (extends)<br>• **AnalysisContext** (analyzes)<br>• **Finding** (creates)<br>• **RadonAnalyzer** (uses for complexity calculation) |
| **Type** | Concrete Class |

---

### **PerformanceAgent**

| **Class Name** | PerformanceAgent |
|---|---|
| **Responsibilities** | • Detect nested loops (threshold: 3 levels)<br>• Identify inefficient algorithms (O(n²) patterns)<br>• Flag expensive operations inside loops:<br>&nbsp;&nbsp;- File I/O<br>&nbsp;&nbsp;- Network requests<br>&nbsp;&nbsp;- Database queries<br>• Visit AST nodes for performance analysis<br>• Return performance findings |
| **Collaborators** | • **BaseAgent** (extends)<br>• **AnalysisContext** (analyzes)<br>• **Finding** (creates)<br>• **PerformanceASTVisitor** (uses for AST traversal) |
| **Type** | Concrete Class |

---

### **StyleAgent**

| **Class Name** | StyleAgent |
|---|---|
| **Responsibilities** | • Check PEP 8 compliance using pylint + flake8<br>• Validate docstrings presence and format<br>• Check naming conventions:<br>&nbsp;&nbsp;- Functions: snake_case<br>&nbsp;&nbsp;- Classes: PascalCase<br>&nbsp;&nbsp;- Constants: UPPER_SNAKE_CASE<br>• Detect unused imports and variables<br>• Check line length (default: 88 characters)<br>• Return style findings |
| **Collaborators** | • **BaseAgent** (extends)<br>• **AnalysisContext** (analyzes)<br>• **Finding** (creates)<br>• **PylintAnalyzer** (uses)<br>• **Flake8Analyzer** (uses) |
| **Type** | Concrete Class |

---

### **OrchestratorAgent**

| **Class Name** | OrchestratorAgent |
|---|---|
| **Responsibilities** | • Coordinate parallel execution of all 4 agents<br>• Use ThreadPoolExecutor (max_workers=4)<br>• Create agent instances via AgentFactory<br>• Aggregate findings from all agents<br>• Calculate quality score using formula:<br>&nbsp;&nbsp;`score = max(0, 100 - Σ(penalties))`<br>&nbsp;&nbsp;- CRITICAL: -10<br>&nbsp;&nbsp;- HIGH: -5<br>&nbsp;&nbsp;- MEDIUM: -2<br>&nbsp;&nbsp;- LOW: -1<br>• Handle agent failures and timeouts (30s per agent)<br>• Emit progress events via EventBus<br>• Create and return CodeReview aggregate root |
| **Collaborators** | • **AgentFactory** (creates agents via)<br>• **EventBus** (publishes events to)<br>• **BaseAgent** (orchestrates all subclasses)<br>• **AnalysisContext** (receives as input)<br>• **CodeReview** (creates and returns)<br>• **Finding** (aggregates from agents) |
| **Type** | Concrete Class |

---

## 🏭 **FACTORY & PATTERNS**

### **AgentFactory** (Singleton)

| **Class Name** | AgentFactory |
|---|---|
| **Responsibilities** | • Provide singleton instance (thread-safe initialization)<br>• Register agent classes dynamically:<br>&nbsp;&nbsp;`register_agent("SecurityAgent", SecurityAgent)`<br>• Create agent instances with configuration:<br>&nbsp;&nbsp;`create_agent("SecurityAgent", config)`<br>• Maintain registry of available agents<br>• Support dynamic agent loading (plugin architecture)<br>• Return list of registered agent names |
| **Collaborators** | • **BaseAgent** (creates subclasses of)<br>• **AgentConfig** (passes to created agents)<br>• **OrchestratorAgent** (used by for agent creation) |
| **Type** | Singleton Class |
| **Pattern** | Singleton + Factory |

---

### **EventBus** (Observer Pattern)

| **Class Name** | EventBus |
|---|---|
| **Responsibilities** | • Manage list of event observers (subscribers)<br>• Subscribe observers: `subscribe(observer)`<br>• Unsubscribe observers: `unsubscribe(observer)`<br>• Publish events to all subscribers: `publish(event)`<br>• Notify observers asynchronously (thread-safe with Lock)<br>• Support multiple event types:<br>&nbsp;&nbsp;- ANALYSIS_STARTED<br>&nbsp;&nbsp;- AGENT_STARTED<br>&nbsp;&nbsp;- AGENT_COMPLETED<br>&nbsp;&nbsp;- ANALYSIS_COMPLETED<br>&nbsp;&nbsp;- ANALYSIS_FAILED |
| **Collaborators** | • **EventObserver** (notifies interface implementers)<br>• **Event** (publishes instances of)<br>• **OrchestratorAgent** (receives events from)<br>• **BaseAgent** (receives events from) |
| **Type** | Concrete Class |
| **Pattern** | Observer (Publish-Subscribe) |

---

## 📦 **ENTITIES & VALUE OBJECTS**

### **Finding** (Entity)

| **Class Name** | Finding |
|---|---|
| **Responsibilities** | • Store individual vulnerability/issue details:<br>&nbsp;&nbsp;- id (UUID)<br>&nbsp;&nbsp;- agent_type (str)<br>&nbsp;&nbsp;- severity (Severity enum)<br>&nbsp;&nbsp;- issue_type (str, e.g., "eval_usage")<br>&nbsp;&nbsp;- line_number (int)<br>&nbsp;&nbsp;- code_snippet (str)<br>&nbsp;&nbsp;- message (str)<br>&nbsp;&nbsp;- suggestion (str)<br>• Optionally contain AIExplanation (Sprint 3)<br>• Calculate severity penalty for quality score<br>• Provide dictionary serialization: `to_dict()`<br>• Support equality comparison by id |
| **Collaborators** | • **Severity** (has enum value)<br>• **AIExplanation** (has 0..1 relationship)<br>• **CodeReview** (belongs to aggregate root)<br>• **BaseAgent** (created by) |
| **Type** | Entity (has identity) |

---

### **AIExplanation** (Value Object - Sprint 3)

| **Class Name** | AIExplanation |
|---|---|
| **Responsibilities** | • Store AI-generated explanation fields:<br>&nbsp;&nbsp;- explanation (str, pedagogical text)<br>&nbsp;&nbsp;- attack_example (Optional[str], exploit demo)<br>&nbsp;&nbsp;- fix_code (Optional[str], corrected code)<br>&nbsp;&nbsp;- cwe_reference (str, e.g., "CWE-95")<br>&nbsp;&nbsp;- owasp_category (str, e.g., "A03:2021")<br>&nbsp;&nbsp;- confidence_score (float, 0.0-1.0)<br>&nbsp;&nbsp;- model_used (str, "gemini-1.5-flash")<br>&nbsp;&nbsp;- generated_at (datetime)<br>• Check if high confidence: `is_high_confidence()`<br>• Provide dictionary serialization: `to_dict()`<br>• Immutable after creation |
| **Collaborators** | • **Finding** (attached to)<br>• **AIExplainerService** (created by) |
| **Type** | Value Object (no identity, value equality) |

---

### **CodeReview** (Aggregate Root)

| **Class Name** | CodeReview |
|---|---|
| **Responsibilities** | • Serve as aggregate root for analysis session<br>• Contain list of Finding entities (composition)<br>• Track analysis status lifecycle:<br>&nbsp;&nbsp;- PENDING → PROCESSING → COMPLETED/FAILED<br>• Calculate and store quality score (0-100)<br>• Provide methods to manage findings:<br>&nbsp;&nbsp;- `add_finding(finding)`<br>&nbsp;&nbsp;- `get_findings_by_severity(severity)`<br>&nbsp;&nbsp;- `get_findings_by_agent(agent_type)`<br>&nbsp;&nbsp;- `get_critical_findings()`<br>• Check analysis state:<br>&nbsp;&nbsp;- `is_completed()`<br>&nbsp;&nbsp;- `is_failed()`<br>&nbsp;&nbsp;- `has_critical_issues()`<br>• Store metadata:<br>&nbsp;&nbsp;- filename, user_id, created_at, completed_at |
| **Collaborators** | • **Finding** (contains many, 1:N)<br>• **ReviewStatus** (has enum value)<br>• **AnalysisContext** (created from)<br>• **User** (belongs to)<br>• **OrchestratorAgent** (created by) |
| **Type** | Aggregate Root Entity |

---

### **AnalysisContext** (Value Object)

| **Class Name** | AnalysisContext |
|---|---|
| **Responsibilities** | • Encapsulate all analysis input data:<br>&nbsp;&nbsp;- analysis_id (UUID)<br>&nbsp;&nbsp;- user_id (str)<br>&nbsp;&nbsp;- filename (str)<br>&nbsp;&nbsp;- code_content (str, Python source code)<br>&nbsp;&nbsp;- uploaded_at (datetime)<br>• Provide parsed AST tree (lazy loading): `get_ast()`<br>• Provide code as list of lines: `get_lines()`<br>• Get specific line: `get_line(line_number)`<br>• Store analysis configuration: `config (AnalysisConfig)`<br>• Immutable after creation<br>• Provide dictionary serialization: `to_dict()` |
| **Collaborators** | • **AgentConfig** (has configuration)<br>• **BaseAgent** (passed to all agents)<br>• **OrchestratorAgent** (created by) |
| **Type** | Value Object |

---

### **AgentConfig** (Value Object)

| **Class Name** | AgentConfig |
|---|---|
| **Responsibilities** | • Store agent-specific configuration:<br>&nbsp;&nbsp;- enabled (bool, agent on/off)<br>&nbsp;&nbsp;- timeout_seconds (int, default: 30)<br>&nbsp;&nbsp;- custom_rules (Dict[str, Any])<br>&nbsp;&nbsp;- thresholds (Dict[str, float])<br>• Check if specific rule enabled: `is_rule_enabled(rule_name)`<br>• Get threshold with default: `get_threshold(key, default)`<br>• Provide dictionary serialization: `to_dict()`<br>• Create from dictionary: `from_dict(data)` |
| **Collaborators** | • **BaseAgent** (configures)<br>• **AnalysisContext** (contained in) |
| **Type** | Value Object |

---

## 📊 **ENUMERATIONS**

### **Severity** (Enum)

| **Enum Name** | Severity |
|---|---|
| **Values** | • **CRITICAL** (penalty: -10 points)<br>• **HIGH** (penalty: -5 points)<br>• **MEDIUM** (penalty: -2 points)<br>• **LOW** (penalty: -1 point) |
| **Methods** | • `get_penalty()` → int<br>• `get_color()` → str (for UI)<br>• `get_order()` → int (for sorting) |
| **Type** | Enum with Behavior |

---

### **ReviewStatus** (Enum)

| **Enum Name** | ReviewStatus |
|---|---|
| **Values** | • **PENDING** (initial state)<br>• **PROCESSING** (agents executing)<br>• **COMPLETED** (success, terminal)<br>• **FAILED** (error, terminal) |
| **Methods** | • `is_terminal()` → bool<br>• `can_transition_to(status)` → bool |
| **Type** | Enum with Behavior |

---

### **AgentCategory** (Enum)

| **Enum Name** | AgentCategory |
|---|---|
| **Values** | • **SECURITY**<br>• **QUALITY**<br>• **PERFORMANCE**<br>• **STYLE** |
| **Methods** | • `get_color()` → str (for UI icons)<br>• `get_icon()` → str (emoji or CSS class) |
| **Type** | Enum |

---

## 🎭 **DOMAIN EVENTS**

### **Event** (Base Domain Event)

| **Class Name** | Event |
|---|---|
| **Responsibilities** | • Represent state changes in the system<br>• Store event metadata:<br>&nbsp;&nbsp;- event_id (UUID)<br>&nbsp;&nbsp;- event_type (str)<br>&nbsp;&nbsp;- aggregate_id (UUID, e.g., review_id)<br>&nbsp;&nbsp;- aggregate_type (str, e.g., "CodeReview")<br>&nbsp;&nbsp;- data (Dict[str, Any], additional info)<br>&nbsp;&nbsp;- timestamp (datetime)<br>• Provide dictionary serialization: `to_dict()`<br>• Immutable after creation |
| **Collaborators** | • **EventBus** (published via) |
| **Type** | Base Domain Event |

---

### **AnalysisStartedEvent**

| **Event** | AnalysisStartedEvent (extends Event) |
|---|---|
| **Data** | • review_id (UUID)<br>• user_id (str)<br>• filename (str)<br>• timestamp (datetime) |
| **When** | Emitted when OrchestratorAgent begins analysis |

---

### **AgentCompletedEvent**

| **Event** | AgentCompletedEvent (extends Event) |
|---|---|
| **Data** | • review_id (UUID)<br>• agent_name (str)<br>• findings_count (int)<br>• execution_time_ms (int) |
| **When** | Emitted when any agent finishes analysis |

---

### **AnalysisCompletedEvent**

| **Event** | AnalysisCompletedEvent (extends Event) |
|---|---|
| **Data** | • review_id (UUID)<br>• quality_score (int)<br>• total_findings (int)<br>• has_critical (bool) |
| **When** | Emitted when all agents complete successfully |

---

### **AnalysisFailedEvent**

| **Event** | AnalysisFailedEvent (extends Event) |
|---|---|
| **Data** | • review_id (UUID)<br>• error_message (str)<br>• error_type (str, e.g., "SyntaxError") |
| **When** | Emitted when analysis fails fatally |

---

## 🔄 **DESIGN PATTERNS IN DOMAIN LAYER**

| Pattern | Classes | Purpose |
|---------|---------|---------|
| **Template Method** | BaseAgent | Define skeleton of analyze() algorithm |
| **Factory** | AgentFactory | Centralized agent creation |
| **Singleton** | AgentFactory | Single instance shared globally |
| **Observer** | EventBus + EventObserver | Decouple event producers from consumers |
| **Strategy** | BaseAgent subclasses | Interchangeable analysis algorithms |
| **Decorator** | SecurityAgentEnhanced | Add AI layer to SecurityAgent |
| **Aggregate Root** | CodeReview | Consistency boundary for findings |
| **Value Object** | AIExplanation, AnalysisContext, AgentConfig | Immutable, value-based equality |
| **Domain Event** | Event hierarchy | Track state changes |

---

**Total Domain Classes:** 24  
**Last Updated:** November 2, 2025
