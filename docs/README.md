# 📐 CodeGuard AI - Workshop 2 Complete Documentation

## 📑 Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Architecture & Design](#architecture--design)
- [Diagrams Reference](#diagrams-reference)
- [How to Export Diagrams](#how-to-export-diagrams)
- [Technologies Used](#technologies-used)
- [Design Patterns](#design-patterns-used)

---

## Overview

This documentation contains all design artifacts, diagrams, and specifications for the **CodeGuard AI Multi-Agent Code Review System** - a Python-based automated code analysis platform with AI-powered explanations using Google Gemini and Model Context Protocol (MCP) servers.

**Key Features:**
- Multi-agent architecture (Security, Quality, Performance, Style)
- AI-powered explanations via Google Gemini (Sprint 3)
- Context enrichment via MCP servers (OWASP, CVE, Custom KB)
- Parallel agent execution (4 agents in ~4 seconds)
- Real-time WebSocket progress updates
- Clean Architecture + C4 Model design

---

## Directory Structure

```
docs/
├── 01-architecture/                 # System architecture (C4 Model)
│   ├── c4-level1-system-context.puml
│   ├── c4-level2-container-diagram.puml
│   ├── c4-level3-component-backend.puml
│   ├── c4-level3-component-frontend.puml
│   ├── c4-level4-code-domain-layer.puml
│   ├── c4-deployment-architecture.puml
│   └── clean-architecture-layers.puml
│
├── 02-class-diagrams/               # UML Class Diagrams
│   ├── uml-domain-layer-complete.puml
│   ├── uml-application-layer-services.puml
│   ├── uml-infrastructure-layer-repositories.puml
│   ├── uml-domain-agents-hierarchy.puml
│   └── uml-domain-models-relationships.puml
│
├── 03-sequence-diagrams/            # UML Sequence Diagrams
│   ├── uml-seq-code-analysis-workflow.puml
│   ├── uml-seq-ai-explanation-generation.puml
│   ├── uml-seq-parallel-agent-execution.puml
│   ├── uml-seq-admin-configuration.puml
│   └── uml-seq-websocket-real-time-progress.puml
│
├── 04-activity-diagrams/            # UML Activity Diagrams (BPMN-style)
│   ├── uml-act-analysis-workflow-complete.puml
│   ├── uml-act-parallel-agent-execution.puml
│   ├── uml-act-ai-explanation-subprocess.puml
│   ├── uml-act-mcp-context-enrichment.puml
│   └── uml-act-admin-config-workflow.puml
│
├── 05-state-diagrams/               # UML State Diagrams
│   ├── uml-state-codereview-lifecycle.puml
│   ├── uml-state-codereview-lifecycle.mmd
│   ├── uml-state-analysis-status.puml
│   └── uml-state-agent-execution.puml
│
├── 06-database/                     # Database Models
│   ├── er-diagram-complete.dbml     # For dbdiagram.io
│   ├── er-diagram-complete.puml     # PlantUML version
│   ├── database-schema.sql
│   └── sample-queries.sql
│
├── 07-component-diagrams/           # UML Component Diagrams
│   ├── uml-comp-ai-mcp-integration.puml
│   ├── uml-comp-backend-services.puml
│   ├── uml-comp-frontend-modules.puml
│   └── uml-comp-infrastructure-services.puml
│
├── 08-mockups/                      # UI Wireframes & Mockups
│   ├── mockup-01-upload-page.png
│   ├── mockup-02-analysis-progress.png
│   ├── mockup-03-results-dashboard.png
│   ├── mockup-04-finding-detail-modal.png
│   ├── mockup-05-admin-dashboard.png
│   └── mockup-06-trends-dashboard.png
│
├── 09-crc-cards/                    # CRC Cards (Class-Responsibility-Collaborator)
│   ├── crc-cards-complete.md
│   └── crc-cards-domain-layer.md
│
├── exports/                         # Exported diagrams (PNG, SVG, PDF)
│   ├── png/                         # Raster format (300 DPI)
│   ├── svg/                         # Vector format (scalable)
│   ├── pdf/                         # PDF format (documents)
│   └── index.html                   # HTML gallery of all diagrams
│
├── scripts/                         # Utility scripts
│   ├── export-all-diagrams.sh       # Bash script to export all diagrams
│   ├── validate-diagrams.sh         # Validate PlantUML syntax
│   └── generate-index.py            # Generate HTML index
│
└── README.md                        # This file
```

---

## Architecture & Design

### C4 Model (4 Levels of Architecture)

The system follows the C4 Model for architecture visualization:

| Level | Focus | File |
|-------|-------|------|
| **1** | System Context | c4-level1-system-context.puml |
| **2** | Containers (Apps, DBs) | c4-level2-container-diagram.puml |
| **3** | Components (Internal) | c4-level3-component-backend.puml |
| **4** | Code (Classes, Interfaces) | c4-level4-code-domain-layer.puml |

### Clean Architecture (Onion Model)

```
┌─────────────────────────────────────────┐
│       PRESENTATION LAYER                │  ← FastAPI, WebSocket
│  (REST API, Controllers)                │
├─────────────────────────────────────────┤
│       APPLICATION LAYER                 │  ← Services
│  (Use Cases, DTOs)                      │
├─────────────────────────────────────────┤
│       DOMAIN LAYER (Core)               │  ← Business Logic
│  (Entities, Agents, Value Objects)      │     No dependencies!
├─────────────────────────────────────────┤
│       INFRASTRUCTURE LAYER              │  ← DB, APIs, Cache
│  (Repositories, External Services)      │
└─────────────────────────────────────────┘
```

**Key Principle:** All dependencies point INWARD toward the core domain.

---

## Diagrams Reference

### 1. Architecture Diagrams

- **clean-architecture-layers.puml** - Layered architecture showing Presentation, Application, Domain, and Infrastructure layers with dependency inversion

### 2. Class Diagrams

- **uml-domain-layer-complete.puml** - Complete domain layer with agents, EventBus, factory pattern
- **uml-application-layer-services.puml** - Application layer services (AnalysisService, AuthService, AIExplainer)
- **uml-infrastructure-layer-repositories.puml** - Repositories, ORM entities, external services
- **uml-domain-agents-hierarchy.puml** - Agent hierarchy and collaboration patterns
- **uml-domain-models-relationships.puml** - Domain models, entities, value objects, enums

### 3. Sequence Diagrams

- **uml-seq-code-analysis-workflow.puml** - Complete flow from file upload to results
- **uml-seq-parallel-agent-execution.puml** - Parallel execution of 4 agents (ThreadPoolExecutor)
- **uml-seq-ai-explanation-generation.puml** - AI explanation generation with MCP context enrichment
- **uml-seq-admin-configuration.puml** - Admin configuration workflow (Sprint 4)
- **uml-seq-websocket-real-time-progress.puml** - WebSocket real-time progress updates

### 4. Activity Diagrams (BPMN-style)

- **uml-act-analysis-workflow-complete.puml** - High-level analysis workflow
- **uml-act-parallel-agent-execution.puml** - Parallel agent execution detail
- **uml-act-ai-explanation-subprocess.puml** - AI explanation subprocess (Sprint 3)
- **uml-act-mcp-context-enrichment.puml** - MCP servers context enrichment
- **uml-act-admin-config-workflow.puml** - Admin configuration workflow (Sprint 4)

### 5. State Diagrams

- **uml-state-codereview-lifecycle.puml** - CodeReview entity lifecycle (PENDING → PROCESSING → COMPLETED/FAILED)
- **uml-state-analysis-status.puml** - Analysis status from user perspective
- **uml-state-agent-execution.puml** - Individual agent execution lifecycle
- **uml-state-codereview-lifecycle.mmd** - Mermaid version of CodeReview lifecycle

### 6. Component Diagrams

- **uml-comp-ai-mcp-integration.puml** - AI and MCP integration architecture
- **uml-comp-backend-services.puml** - Backend service components
- **uml-comp-frontend-modules.puml** - React frontend module structure
- **uml-comp-infrastructure-services.puml** - Infrastructure layer components

### 7. Database Model

- **er-diagram-complete.dbml** - ER diagram for dbdiagram.io
  - 9 tables: users, code_reviews, agent_findings, agent_configs, ai_config, ai_usage_metrics, mcp_context_logs, event_logs, analysis_export_logs
  - Relationships with cascade delete
  - Indexes and constraints optimized
- **database-schema.sql** - Complete DDL SQL script (PostgreSQL 15)
- **sample-queries.sql** - Common query patterns for analysis

### 8. CRC Cards

- **crc-cards-complete.md** - All 60+ classes with responsibilities and collaborators
- **crc-cards-domain-layer.md** - Domain layer classes only (focused view)

---

## How to Export Diagrams

### Option 1: Automated Export (Recommended)

```bash
# Make script executable
chmod +x scripts/export-all-diagrams.sh

# Run export script
./scripts/export-all-diagrams.sh

# Generates PNG, SVG, PDF in exports/
# Output: 30 PNG + 30 SVG + 30 PDF = 90 files
```

### Option 2: Manual Export via VS Code

1. **Install PlantUML Extension:**
   ```bash
   code --install-extension jebbs.plantuml
   ```

2. **Open any .puml file** in VS Code

3. **Preview:** Press Alt+D (Windows/Linux) or Cmd+D (Mac)

4. **Export:** Right-click → "Export Current Diagram" → PNG/SVG/PDF

### Option 3: Online Editor

- Go to https://www.plantuml.com/plantuml/uml/
- Paste PlantUML code
- Export from browser

### Option 4: dbdiagram.io (For ER Diagrams)

- Go to https://dbdiagram.io/
- Import or paste er-diagram-complete.dbml
- View and export ER diagram

---

## Technologies Used

### Diagram Tools

- **PlantUML** - UML, C4 Model, BPMN diagrams (code-based)
- **Mermaid** - Flowcharts, state diagrams (simpler syntax)
- **dbdiagram.io** - ER diagrams (browser-based)
- **Draw.io** - Visual editing (browser-based)

### Export Formats

- **PNG** - Raster, 300 DPI for PDF documents
- **SVG** - Vector, scalable without quality loss
- **PDF** - Direct PDF export

### Supported Browsers

- Chrome 100+
- Firefox 100+
- Safari 15+
- Edge 100+

---

## Design Patterns Used

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Factory** | AgentFactory | Centralized agent instantiation |
| **Singleton** | AgentFactory, EventBus | Single system instances |
| **Observer** | EventBus + Observers | Event-driven progress |
| **Repository** | All repositories | Data access abstraction |
| **Strategy** | BaseAgent (abstract) | Algorithm families |
| **Template Method** | BaseAgent.analyze() | Common algorithm skeleton |
| **Dependency Injection** | All services | Testability, loose coupling |
| **Builder** | AnalysisContext | Complex object construction |
| **Adapter** | Repositories | Domain ↔ ORM mapping |
| **Decorator** | SecurityAgentEnhanced | Adds AI layer to base agent |
| **Aggregate Root** | CodeReview | Consistency boundary |

---

## Database Schema Overview

### Core Tables

- **users** - Central user management (Clerk OAuth)
- **code_reviews** - Main analysis sessions (encrypted code)
- **agent_findings** - Individual vulnerability findings
- **agent_configs** - Agent configuration (Sprint 4)
- **ai_config** - Global AI settings (Sprint 3)

### Integration Tables

- **ai_usage_metrics** - AI API usage tracking
- **mcp_context_logs** - MCP server query logs
- **event_logs** - Analysis event timeline
- **analysis_export_logs** - Export audit trail

---

## Next Steps

1. **View Diagrams:** Open exports/index.html in browser
2. **Edit Diagrams:** Use VS Code + PlantUML extension
3. **Generate PNG:** Run ./scripts/export-all-diagrams.sh
4. **Include in PDF:** Reference PNG exports in LaTeX \includegraphics
5. **Share with Team:** All diagrams are in exports/svg/ for presentations

---

## Document Information

- **Project:** CodeGuard AI Multi-Agent Code Review System
- **Course:** Software Engineering II (2025-II)
- **Institution:** Universidad Nacional de Colombia
- **Created:** November 2, 2025
- **Format:** PlantUML (.puml), Mermaid (.mmd), dbml (.dbml), SQL (.sql)
- **Status:** Workshop 2 Design Phase Complete
- **Total Diagrams:** 30 diagrams + 1 ER diagram
- **Total Exports:** 90 files (PNG, SVG, PDF)

---

**For questions or updates, refer to the main project documentation or contact the development team.**