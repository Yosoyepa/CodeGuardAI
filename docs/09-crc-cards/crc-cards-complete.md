# CRC Cards - CodeGuard AI Complete System

> **CRC (Class-Responsibility-Collaborator)** cards help visualize object-oriented design by showing what each class does and which other classes it works with.

---

## 📦 **DOMAIN LAYER CLASSES**

### **BaseAgent** (Abstract)

| **Class Name** | BaseAgent |
|---|---|
| **Responsibilities** | • Define common interface for all analysis agents<br>• Implement abstract `analyze()` method<br>• Provide agent metadata (name, version, category)<br>• Handle error logging and metrics collection<br>• Emit events via EventBus (AGENT_STARTED, AGENT_COMPLETED) |
| **Collaborators** | • AnalysisContext (receives)<br>• Finding (produces)<br>• EventBus (publishes to)<br>• AgentConfig (configured by) |

---

### **SecurityAgent**

| **Class Name** | SecurityAgent |
|---|---|
| **Responsibilities** | • Parse Python code using AST module<br>• Detect dangerous functions (eval, exec, pickle)<br>• Detect SQL injection patterns (regex-based)<br>• Detect hardcoded credentials (entropy analysis)<br>• Detect weak cryptography (MD5, SHA1)<br>• Return list of security findings |
| **Collaborators** | • BaseAgent (extends)<br>• AnalysisContext (analyzes)<br>• Finding (creates)<br>• BanditAnalyzer (uses) |

---

### **SecurityAgentEnhanced** (Sprint 3)

| **Class Name** | SecurityAgentEnhanced |
|---|---|
| **Responsibilities** | • Extends SecurityAgent with AI capabilities<br>• Filter critical findings for AI explanation<br>• Request AI-generated explanations via AIExplainerService<br>• Attach AIExplanation objects to findings<br>• Implement graceful fallback if AI unavailable |
| **Collaborators** | • SecurityAgent (extends)<br>• AIExplainerService (requests from)<br>• MCPContextEnricher (enriches via)<br>• Finding (enriches with AI) |

---

### **QualityAgent**

| **Class Name** | QualityAgent |
|---|---|
| **Responsibilities** | • Calculate cyclomatic complexity (Radon library)<br>• Detect code duplication (threshold: 20%)<br>• Measure function length (threshold: 100 lines)<br>• Calculate maintainability index<br>• Return quality findings |
| **Collaborators** | • BaseAgent (extends)<br>• AnalysisContext (analyzes)<br>• Finding (creates)<br>• RadonAnalyzer (uses) |

---

### **PerformanceAgent**

| **Class Name** | PerformanceAgent |
|---|---|
| **Responsibilities** | • Detect nested loops (threshold: 3 levels)<br>• Identify inefficient algorithms (O(n²) patterns)<br>• Flag expensive operations inside loops (I/O, network)<br>• Visit AST nodes for performance analysis<br>• Return performance findings |
| **Collaborators** | • BaseAgent (extends)<br>• AnalysisContext (analyzes)<br>• Finding (creates)<br>• PerformanceASTVisitor (uses) |

---

### **StyleAgent**

| **Class Name** | StyleAgent |
|---|---|
| **Responsibilities** | • Check PEP 8 compliance (pylint + flake8)<br>• Validate docstrings presence and format<br>• Check naming conventions (snake_case, PascalCase)<br>• Detect unused imports and variables<br>• Return style findings |
| **Collaborators** | • BaseAgent (extends)<br>• AnalysisContext (analyzes)<br>• Finding (creates)<br>• PylintAnalyzer (uses)<br>• Flake8Analyzer (uses) |

---

### **OrchestratorAgent**

| **Class Name** | OrchestratorAgent |
|---|---|
| **Responsibilities** | • Coordinate parallel execution of all agents (ThreadPoolExecutor)<br>• Create agent instances via AgentFactory<br>• Aggregate findings from all agents<br>• Calculate quality score (0-100 formula)<br>• Handle agent failures and timeouts gracefully<br>• Emit progress events via EventBus<br>• Return CodeReview aggregate |
| **Collaborators** | • AgentFactory (creates agents)<br>• EventBus (publishes to)<br>• BaseAgent (orchestrates)<br>• AnalysisContext (receives)<br>• CodeReview (creates)<br>• Finding (aggregates) |

---

### **AgentFactory** (Singleton)

| **Class Name** | AgentFactory |
|---|---|
| **Responsibilities** | • Provide singleton instance (thread-safe)<br>• Register agent classes dynamically<br>• Create agent instances with configuration<br>• Maintain registry of available agents<br>• Support dynamic agent loading |
| **Collaborators** | • BaseAgent (creates subclasses)<br>• AgentConfig (passes to agents)<br>• OrchestratorAgent (used by) |

---

### **EventBus** (Observer Pattern)

| **Class Name** | EventBus |
|---|---|
| **Responsibilities** | • Manage list of event observers<br>• Subscribe/unsubscribe observers<br>• Publish events to all subscribers<br>• Notify observers asynchronously (thread-safe)<br>• Support multiple event types |
| **Collaborators** | • EventObserver (notifies)<br>• Event (publishes)<br>• OrchestratorAgent (receives from)<br>• BaseAgent (receives from) |

---

### **Finding** (Entity)

| **Class Name** | Finding |
|---|---|
| **Responsibilities** | • Store individual vulnerability/issue details<br>• Associate with agent type, severity, line number<br>• Include code snippet and suggestion<br>• Optionally contain AIExplanation (Sprint 3)<br>• Calculate severity penalty for quality score<br>• Provide dictionary serialization |
| **Collaborators** | • Severity (has enum)<br>• AIExplanation (has 0..1)<br>• CodeReview (belongs to)<br>• BaseAgent (created by) |

---

### **AIExplanation** (Value Object - Sprint 3)

| **Class Name** | AIExplanation |
|---|---|
| **Responsibilities** | • Store AI-generated explanation text<br>• Include attack example and fix code<br>• Reference CWE ID and OWASP category<br>• Track model used (Gemini Flash/Pro)<br>• Record confidence score and generation time<br>• Provide dictionary serialization |
| **Collaborators** | • Finding (attached to)<br>• AIExplainerService (created by) |

---

### **CodeReview** (Aggregate Root)

| **Class Name** | CodeReview |
|---|---|
| **Responsibilities** | • Aggregate root for analysis session<br>• Contain list of Finding entities<br>• Track analysis status (PENDING → PROCESSING → COMPLETED/FAILED)<br>• Calculate and store quality score (0-100)<br>• Provide methods to filter findings by severity/agent<br>• Check if analysis has critical issues |
| **Collaborators** | • Finding (contains many)<br>• ReviewStatus (has enum)<br>• AnalysisContext (created from)<br>• User (belongs to)<br>• OrchestratorAgent (created by) |

---

### **AnalysisContext** (Value Object)

| **Class Name** | AnalysisContext |
|---|---|
| **Responsibilities** | • Encapsulate analysis input data<br>• Store filename, code content, user ID<br>• Provide parsed AST tree (lazy loading)<br>• Provide code lines as list<br>• Store analysis configuration<br>• Immutable after creation |
| **Collaborators** | • AgentConfig (has)<br>• BaseAgent (passed to)<br>• OrchestratorAgent (created by) |

---

## 🔧 **APPLICATION LAYER CLASSES**

### **AnalysisService**

| **Class Name** | AnalysisService |
|---|---|
| **Responsibilities** | • Orchestrate entire code analysis workflow<br>• Validate uploaded files (extension, size, encoding)<br>• Create AnalysisContext from file upload<br>• Invoke OrchestratorAgent for analysis<br>• Persist CodeReview and findings to database<br>• Emit ANALYSIS_COMPLETED event<br>• Return AnalysisDTO to caller |
| **Collaborators** | • OrchestratorAgent (invokes)<br>• CodeReviewRepository (persists via)<br>• AgentFindingRepository (persists via)<br>• AuthenticationService (validates via)<br>• EventBus (publishes to) |

---

### **AuthenticationService**

| **Class Name** | AuthenticationService |
|---|---|
| **Responsibilities** | • Validate JWT tokens via Clerk API<br>• Extract user claims from token<br>• Check user roles (DEVELOPER/ADMIN)<br>• Enforce rate limits (10 analyses/day)<br>• Get or create user from Clerk ID<br>• Track daily analysis quota |
| **Collaborators** | • ClerkClient (calls)<br>• UserRepository (queries)<br>• RedisCache (caches sessions)<br>• User (returns) |

---

### **AIExplainerService** (Sprint 3)

| **Class Name** | AIExplainerService |
|---|---|
| **Responsibilities** | • Generate AI explanations for critical findings<br>• Build prompts with MCP-enriched context<br>• Call Gemini API (Flash in dev, Pro in prod)<br>• Parse JSON responses to AIExplanation objects<br>• Cache explanations in Redis (SHA256 key, TTL 24h)<br>• Implement retry logic with exponential backoff<br>• Fallback to static templates on failure<br>• Track AI usage metrics (tokens, cost, latency) |
| **Collaborators** | • MCPContextEnricher (enriches via)<br>• RedisCache (caches in)<br>• GeminiAPIClient (calls)<br>• RateLimiter (checks via)<br>• AIExplanation (creates)<br>• AIUsageMetrics (records) |

---

### **MCPContextEnricher** (Sprint 3)

| **Class Name** | MCPContextEnricher |
|---|---|
| **Responsibilities** | • Query OWASP MCP server for CWE definitions<br>• Query CVE MCP server for exploit examples<br>• Query Custom KB MCP for team conventions<br>• Execute all 3 queries in parallel (asyncio)<br>• Combine responses into single context string<br>• Handle MCP server failures gracefully<br>• Log MCP performance metrics |
| **Collaborators** | • MCPServerClient (queries via)<br>• MCPContextLog (logs to)<br>• AIExplainerService (used by)<br>• Finding (enriches) |

---

### **ExportService**

| **Class Name** | ExportService |
|---|---|
| **Responsibilities** | • Generate JSON exports of analysis results<br>• Generate PDF reports with AI explanations<br>• Format findings with syntax highlighting<br>• Upload exports to S3 or local storage<br>• Track export logs for compliance<br>• Generate team reports for date ranges |
| **Collaborators** | • CodeReviewRepository (fetches from)<br>• AgentFindingRepository (fetches from)<br>• PDFGenerator (generates with)<br>• StorageClient (uploads to)<br>• AnalysisExportLog (records) |

---

### **ConfigService** (Sprint 4)

| **Class Name** | ConfigService |
|---|---|
| **Responsibilities** | • Get/update agent configurations (thresholds, rules)<br>• Get/update AI configuration (model, rate limits)<br>• Validate configuration changes<br>• Cache configurations in Redis<br>• Invalidate cache on updates<br>• Emit CONFIG_UPDATED events<br>• Ensure only admins can modify configs |
| **Collaborators** | • ConfigRepository (persists to)<br>• RedisCache (caches in)<br>• EventBus (emits to)<br>• AgentConfig (returns)<br>• AIConfig (returns) |

---

## 🗄️ **INFRASTRUCTURE LAYER CLASSES**

### **CodeReviewRepository**

| **Class Name** | CodeReviewRepository |
|---|---|
| **Responsibilities** | • Implement ICodeReviewRepository interface<br>• Create, read, update, delete code reviews<br>• Encrypt code_content with AES-256<br>• Decrypt code_content when retrieving<br>• Map between domain CodeReview and ORM entity<br>• Handle database transactions |
| **Collaborators** | • CodeReview (domain model)<br>• CodeReviewEntity (ORM)<br>• AESEncryptor (encrypts with)<br>• SupabaseClient (queries via) |

---

### **AgentFindingRepository**

| **Class Name** | AgentFindingRepository |
|---|---|
| **Responsibilities** | • Implement IAgentFindingRepository interface<br>• Batch insert findings for performance<br>• Query findings by review ID, severity, agent<br>• Count findings by agent type<br>• Map between domain Finding and ORM entity |
| **Collaborators** | • Finding (domain model)<br>• AgentFindingEntity (ORM)<br>• SupabaseClient (queries via) |

---

### **UserRepository**

| **Class Name** | UserRepository |
|---|---|
| **Responsibilities** | • Implement IUserRepository interface<br>• Create, read, update users<br>• Update daily analysis quota<br>• Get daily usage count for rate limiting<br>• Map between domain User and ORM entity |
| **Collaborators** | • User (domain model)<br>• UserEntity (ORM)<br>• SupabaseClient (queries via) |

---

### **ConfigRepository**

| **Class Name** | ConfigRepository |
|---|---|
| **Responsibilities** | • Implement IConfigRepository interface<br>• Save/get agent configurations<br>• Save/get AI configuration (single row)<br>• Cache configurations in Redis<br>• Invalidate cache on updates<br>• Track who updated configs (audit trail) |
| **Collaborators** | • AgentConfig (domain model)<br>• AIConfig (domain model)<br>• AgentConfigEntity (ORM)<br>• AIConfigEntity (ORM)<br>• RedisCache (caches in)<br>• SupabaseClient (queries via) |

---

### **ClerkClient**

| **Class Name** | ClerkClient |
|---|---|
| **Responsibilities** | • Verify JWT tokens via Clerk API<br>• Get user profile from Clerk<br>• List users with filters<br>• Make authenticated HTTP requests to Clerk<br>• Handle API errors and retries |
| **Collaborators** | • AuthenticationService (used by)<br>• User (returns data for) |

---

### **GeminiAPIClient** (Sprint 3)

| **Class Name** | GeminiAPIClient |
|---|---|
| **Responsibilities** | • Generate content via Gemini API (Flash/Pro)<br>• Select endpoint based on environment (dev/prod)<br>• Count tokens in prompts<br>• Handle rate limits (429 errors)<br>• Implement exponential backoff retries<br>• Track API usage metrics |
| **Collaborators** | • AIExplainerService (used by)<br>• AIUsageMetrics (records to) |

---

### **MCPServerClient** (Sprint 3)

| **Class Name** | MCPServerClient |
|---|---|
| **Responsibilities** | • Query MCP servers via stdio protocol<br>• Call tools with parameters (lookup_cwe, search_cve)<br>• List available tools on server<br>• Manage connection lifecycle (connect/disconnect)<br>• Handle timeouts and errors<br>• Log query performance |
| **Collaborators** | • MCPContextEnricher (used by)<br>• MCPContextLog (logs to) |

---

### **RedisCache**

| **Class Name** | RedisCache |
|---|---|
| **Responsibilities** | • Get/set key-value pairs in Redis<br>• Set TTL (time-to-live) for keys<br>• Delete keys (cache invalidation)<br>• Check key existence<br>• Generate cache keys (SHA256 hashing)<br>• Calculate cache hit rate<br>• Serialize/deserialize values (JSON) |
| **Collaborators** | • AIExplainerService (used by)<br>• ConfigService (used by)<br>• AuthenticationService (used by) |

---

### **AESEncryptor**

| **Class Name** | AESEncryptor |
|---|---|
| **Responsibilities** | • Encrypt plaintext with AES-256-GCM<br>• Decrypt ciphertext to plaintext<br>• Generate initialization vectors (IV)<br>• Load encryption key from environment<br>• Ensure secure key management |
| **Collaborators** | • CodeReviewRepository (used by) |

---

## 🎨 **HELPERS & UTILITIES**

### **BanditAnalyzer**

| **Class Name** | BanditAnalyzer |
|---|---|
| **Responsibilities** | • Run Bandit static analysis tool<br>• Parse Bandit JSON output<br>• Map Bandit issues to Finding objects<br>• Get severity from Bandit confidence/severity |
| **Collaborators** | • SecurityAgent (used by) |

---

### **RadonAnalyzer**

| **Class Name** | RadonAnalyzer |
|---|---|
| **Responsibilities** | • Analyze cyclomatic complexity with Radon<br>• Calculate maintainability index<br>• Parse Radon output to metrics dictionary |
| **Collaborators** | • QualityAgent (used by) |

---

### **PylintAnalyzer**

| **Class Name** | PylintAnalyzer |
|---|---|
| **Responsibilities** | • Run pylint on Python code<br>• Parse pylint messages<br>• Filter by category (convention, warning, error)<br>• Load custom pylint config file |
| **Collaborators** | • StyleAgent (used by) |

---

### **Flake8Analyzer**

| **Class Name** | Flake8Analyzer |
|---|---|
| **Responsibilities** | • Run flake8 on Python code<br>• Parse flake8 violations<br>• Map violations to Finding objects |
| **Collaborators** | • StyleAgent (used by) |

---

### **PerformanceASTVisitor**

| **Class Name** | PerformanceASTVisitor |
|---|---|
| **Responsibilities** | • Visit AST nodes (for/while loops)<br>• Track loop nesting depth<br>• Identify expensive operations in loops (I/O, network)<br>• Get list of nested loops with line numbers |
| **Collaborators** | • PerformanceAgent (used by) |

---

### **RateLimiter**

| **Class Name** | RateLimiter |
|---|---|
| **Responsibilities** | • Check rate limits via Redis counters<br>• Increment counter on usage<br>• Get remaining requests count<br>• Reset counters (e.g., daily reset)<br>• Support sliding window rate limiting |
| **Collaborators** | • AIExplainerService (used by)<br>• AuthenticationService (used by)<br>• RedisCache (uses) |

---

### **PDFGenerator**

| **Class Name** | PDFGenerator |
|---|---|
| **Responsibilities** | • Render HTML template with analysis data<br>• Convert HTML to PDF (weasyprint or reportlab)<br>• Include syntax-highlighted code snippets<br>• Format AI explanations in PDF<br>• Add logo and branding |
| **Collaborators** | • ExportService (used by) |

---

## 📊 **DTOs (Data Transfer Objects)**

### **AnalysisDTO**

| **Class Name** | AnalysisDTO |
|---|---|
| **Responsibilities** | • Transfer analysis summary to frontend<br>• Include analysis_id, quality_score, status<br>• Include findings count by severity<br>• Provide dictionary serialization<br>• Map from CodeReview domain model |
| **Collaborators** | • CodeReview (maps from) |

---

### **CodeReviewDTO**

| **Class Name** | CodeReviewDTO |
|---|---|
| **Responsibilities** | • Transfer complete code review to frontend<br>• Include findings list (as FindingDTOs)<br>• Include timestamps, quality score, status<br>• Provide dictionary serialization<br>• Map from CodeReview + Finding domain models |
| **Collaborators** | • CodeReview (maps from)<br>• FindingDTO (contains list) |

---

### **FindingDTO**

| **Class Name** | FindingDTO |
|---|---|
| **Responsibilities** | • Transfer individual finding to frontend<br>• Include all finding details (severity, message, line)<br>• Optionally include AIExplanationDTO<br>• Provide dictionary serialization<br>• Map from Finding domain model |
| **Collaborators** | • Finding (maps from)<br>• AIExplanationDTO (contains 0..1) |

---

### **AIExplanationDTO**

| **Class Name** | AIExplanationDTO |
|---|---|
| **Responsibilities** | • Transfer AI explanation to frontend<br>• Include explanation text, attack example, fix code<br>• Include CWE/OWASP references<br>• Provide dictionary serialization<br>• Map from AIExplanation value object |
| **Collaborators** | • AIExplanation (maps from) |

---

## 🔄 **OBSERVERS (Event Handling)**

### **WebSocketObserver**

| **Class Name** | WebSocketObserver |
|---|---|
| **Responsibilities** | • Implement EventObserver interface<br>• Listen to EventBus events<br>• Format events as JSON messages<br>• Send events to WebSocket clients<br>• Handle connection errors gracefully |
| **Collaborators** | • EventBus (subscribes to)<br>• Event (receives)<br>• WebSocket connection (sends to) |

---

### **DatabaseObserver**

| **Class Name** | DatabaseObserver |
|---|---|
| **Responsibilities** | • Implement EventObserver interface<br>• Listen to EventBus events<br>• Persist events to event_logs table<br>• Create audit trail for analysis |
| **Collaborators** | • EventBus (subscribes to)<br>• Event (receives)<br>• EventLogRepository (persists via) |

---

### **LoggingObserver**

| **Class Name** | LoggingObserver |
|---|---|
| **Responsibilities** | • Implement EventObserver interface<br>• Listen to EventBus events<br>• Format events as structured logs<br>• Write logs to stdout/file (structlog)<br>• Filter events by log level |
| **Collaborators** | • EventBus (subscribes to)<br>• Event (receives)<br>• Logger (logs to) |

---

## 📋 **LEGEND**

| Symbol | Meaning |
|--------|---------|
| **•** | Individual responsibility or action |
| **→** | Direction of dependency |
| **(extends)** | Inheritance relationship |
| **(uses)** | Composition/aggregation |
| **(creates)** | Factory/creation pattern |
| **(calls)** | Direct method invocation |
| **(Sprint 3)** | Feature added in Sprint 3 |
| **(Sprint 4)** | Feature added in Sprint 4 |

---

## 📊 **DESIGN PATTERNS SUMMARY**

| Pattern | Classes |
|---------|---------|
| **Template Method** | BaseAgent (abstract analyze) |
| **Factory** | AgentFactory (creates agents) |
| **Singleton** | AgentFactory, EventBus |
| **Observer** | EventBus + Observers |
| **Repository** | All repositories (data access abstraction) |
| **Strategy** | BaseAgent (algorithm families) |
| **Dependency Injection** | All services (constructor injection) |
| **Builder** | AnalysisContext |
| **Adapter** | Repositories (domain ↔ ORM) |
| **Decorator** | SecurityAgentEnhanced (adds AI layer) |

---

**Total Classes:** 60+  
**Last Updated:** November 2, 2025
