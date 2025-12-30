
Natural-Language Specification: SpecFirst System Builder (Fastify + FastAPI)
-----------------------------------------------------------------------------

### 1\. Overall Goal

I want to build a **Spec‑First System Builder**: a platform that takes natural-language descriptions of software systems, converts them into strict machine-readable specs (CTO), plans the architecture, generates deterministic code, orchestrates builds/tests, and learns over time from metrics and causal analysis.

The system will be:

*   **Schema-first**: CTO JSON is the primary source of truth.
*   **LLM-assisted but deterministic**: LLMs are used only as translators/planners; all code generation is via deterministic scripts + templates.
*   **Split-stack**:
    *   **Node/TypeScript + Fastify**: local web client and API gateway/proxy.
    *   **Python + FastAPI**: backend API handling specs, architecture planning, code generation, orchestration, and causal analysis.
*   **Workflow-driven**: Prefect for DAG orchestration and parallelization.
*   **Causally self-improving**: DoWhy for causal inference over architecture and build metrics.
*   **Template-based**: Jinja2 for code generation templates.
*   **Graph-aware**: NetworkX (and optionally Neo4j) for representing and analyzing specs and architecture graphs.
*   **LLM calls managed via OpenRouter/OpenAI SDK**, with usage metrics recorded.
*   **CLI wrappers** for key python generator steps so they can be run from the terminal or CI without the web UI
* * *

### 2\. Architecture and Technology Stack

#### 2.1 Technology Stack

*   **Client / Gateway (Node/TS)**
    
    *   Language: TypeScript
    *   Runtime: Node.js
    *   Framework: Fastify
    *   Responsibilities:
        *   Serve a simple web UI for specs, diagrams, plans, runs, metrics.
        *   Expose a local HTTP API for automation/integration.
        *   Proxy relevant requests to Python/FastAPI backend.
    *   Testing: Vitest and Supertest or similar.
*   **Backend (Python)**
	*	Note: Fastify gateway and FastAPI backend should interact locally (same server)
    *   Language: Python 3.x
    *   Framework: FastAPI
    *   Responsibilities:
        *   Spec ingestion and CTO generation.
        *   Diagram (Mermaid) generation.
        *   ArchitecturePlan creation & refinement.
        *   Deterministic generator management (Python + Jinja2).
        *   Orchestrating builds/tests via Prefect.
        *   Metrics harvesting and storage.
        *   Causal analysis via DoWhy.
    *   Libraries:
        *   Prefect for workflow orchestration and DAGs.
        *   Jinja2 for code generation templates.
        *   NetworkX for graph representations and analysis.
        *   DoWhy for causal modeling and effect estimation.
        *   Pydantic / jsonschema for CTO validation.
*   **LLM Integration**
    
    *   All LLM interactions are via:
        *   OpenRouter and/or OpenAI SDK.
    *   Responsibilities:
        *   Natural language → CTO JSON.
        *   CTO → Mermaid diagrams.
        *   CTO + diagrams → ArchitecturePlan.
        *   CTO + Plan (+ Lessons Learned) → generator scripts.
        *   Optional: assist in auto-fix loops.
    *   Requirements:
        *   Log model name, tokens, latency, and step for every call.
        *   No LLM calls inside generator scripts; only in planning/translation phases.
*   **Persistence and Infrastructure**
    
    *   Database: PostgreSQL (for specs, artifacts, metrics).
    *   Filesystem or object store:
        *   Store CTO JSON, Mermaid diagrams, ArchitecturePlans, generator scripts, generated code snapshots.
    *   Containerization: Docker for sandboxing generation and tests.
    *   Orchestration: local Prefect server/agent (initially).

* * *

### 3\. Core Phases and Behavior

#### Phase 1 – Intent → CTO + Diagrams

*   User provides a natural-language description of a target application or feature change via:
    
    *   Web UI (Fastify frontend).
    *   Or CLI wrapper (e.g., sfsb-spec new --input description.txt).
*   Backend (FastAPI) calls LLM (via OpenRouter/OpenAI SDK) to:
    
    *   Produce a **CTO JSON** with:
        *   project, technology\_stack, data\_models, api\_resources, services, datastores, external\_systems, workflows, architecture\_policies.
        *   technology\_stack must reflect:
            *   Node/TypeScript + Fastify for client gateway.
            *   Python + FastAPI + Prefect + Jinja2 + DoWhy + NetworkX on backend.
    *   Produce **Mermaid diagrams**:
        *   System diagram (flowchart) for services, datastores, externals, client gateway.
        *   Workflow diagrams (stateDiagram-v2) for key business processes.
*   The system:
    
    *   Validates CTO against JSON Schema.
    *   Runs basic consistency checks (e.g., references match existing models).
    *   Validates Mermaid syntax.
    *   Exposes CTO + diagrams for **human review/approval** via the web UI.
    *   On approval, CTO and diagrams are frozen and versioned.
*   CLI wrappers:
    
    *   sfsb-cto generate --spec-id <id> → run NL-to-CTO + diagrams for a given spec input file.
    *   Options to override or pin LLM model used.

* * *

#### Phase 1.5 – Architecture Planning (Modularity)

*   Input: frozen CTO + diagrams + architecture policies + historical Lessons Learned.
    
*   Backend (FastAPI + LLM via OpenRouter/OpenAI):
    
    *   Generates one or more **ArchitecturePlan** candidates (JSON).
    *   Each plan specifies:
        *   Layers (e.g., domain, infra, api).
        *   Modules (id, layer, file, responsibilities, exports, imports\_from).
*   Python backend uses NetworkX to:
    
    *   Build a module dependency graph.
    *   Detect cycles, layer violations.
    *   Compute metrics (fan‑in/out, depth, etc.).
*   Optional refinement loop via Prefect:
    
    *   Task: generate candidates with LLM.
    *   Task: evaluate and score candidates (possibly with weights from DoWhy).
    *   Iterate until:
        *   No improvement above threshold.
        *   Hard constraints satisfied.
        *   Max iterations reached.
*   Human review:
    
    *   Visualize module graph (optionally rendered to Mermaid).
    *   Approve a final ArchitecturePlan version.
*   CLI wrappers:
    
    *   sfsb-arch plan --cto <path> → generate and evaluate ArchitecturePlan(s).
    *   sfsb-arch evaluate --plan <path> → run metrics and checks on a given plan.

* * *

#### Phase 2 – Generator Script Creation (Python + Jinja2)

*   Input: CTO + ArchitecturePlan + diagrams (all frozen versions).
    
*   Backend uses LLM (via OpenRouter/OpenAI) to generate **deterministic Python CLI generators**, such as:
    
    *   gen\_ts\_schema.py: from data\_models → TS interfaces and Zod schemas.
    *   gen\_db\_schema.py: from data\_models → Postgres DDL or SQLAlchemy/Alembic models.
    *   gen\_workflow\_machine.py: from workflow Mermaid → TS or Python state machines.
    *   gen\_middleware.py: from api\_resources + Plan → FastAPI routers (Python) and optionally Fastify routes (TS) for the client gateway.
    *   gen\_tests.py: from APIs + invariants → Jest/Vitest tests for TS side and pytest tests for Python side.
*   Constraints:
    
    *   Generators are plain Python CLIs:
        *   Use Jinja2 templates.
        *   No network/time/random/env dependencies.
    *   System enforces allowed imports and validates generator scripts.
*   Generator scripts and templates are stored in the repo and versioned.
    
*   CLI wrappers:
    
    *   sfsb-gen create --type ts-schema|db-schema|workflow|middleware|tests --cto <path> --plan <path>
    *   These wrappers call the LLM only when (re)generating the generator script itself; codegen runs use the stored scripts.

* * *

#### Phase 3 – Deterministic Build & Orchestration (Prefect + Docker)

*   Prefect flows (triggered via:
    
    *   Web UI,
    *   CLI sfsb-build run --cto <path> --plan <path>,
    *   or FastAPI endpoint) perform the build:
    
    1.  Setup sandbox Docker environments (Python + Node).
    2.  Run Python generators (inside container) to emit:
        *   Backend FastAPI code (routers, models, state machines).
        *   Front/gateway Fastify code (if generated).
        *   DB schema/migrations.
        *   Tests (TS and Python).
    3.  Install dependencies and compile code:
        *   npm install && npm test for Node/TS.
        *   pip install -r requirements.txt && pytest for Python.
    4.  Run all tests and static checks.
    5.  Capture all logs and metrics from Prefect tasks.
*   Parallel execution:
    
    *   Prefect maps tasks over resources (e.g., generate per-resource routes/tests).
    *   Concurrency limits are configurable and can be tuned by causal feedback.

* * *

#### Phase 4 – Validation, Lessons, and Causal Feedback (DoWhy)

*   Validation:
    
    *   Test suites (TS and Python) run in CI-like fashion inside containers.
    *   Static analysis (TS compile, linters, mypy/ruff if applicable).
    *   Consistency checks vs CTO and ArchitecturePlan (e.g., every module in plan exists in code).
*   Lessons Learned:
    
    *   On test failures or human fixes:
        *   Record:
            *   Snippets of CTO and Plan.
            *   Generator templates or scripts involved.
            *   Error messages and diffs of fixes.
        *   Store in a vector DB (and optionally graph DB).
*   Metrics & Causal Analysis:
    
    *   For each run, record:
        *   Architecture metrics (cycles, fan‑in/out, modules, refinement iterations).
        *   Prefect metrics (task runtimes, parallelism, success/failure).
        *   LLM metrics (model, tokens, latency, retries; via OpenRouter/OpenAI usage).
        *   Git/CI metrics (bugfix commits, red-green cycles, incidents).
    *   Periodic Prefect flow runs DoWhy:
        *   Builds causal graphs.
        *   Estimates effects of architecture choices, refinement depth, and parallelism on outcomes.
        *   Writes causal\_weights.json to guide scoring and policies in future planning.
*   CLI wrappers:
    
    *   sfsb-metrics collect --build-id <id>
    *   sfsb-causal refresh → recompute causal weights from history.

* * *

### 4\. Human-in-the-Loop and Bootstrapping

*   All key artifacts (CTO, diagrams, ArchitecturePlan, generator scripts, code) live in Git and are reviewed via PRs.
    
*   Human approvals at:
    
    *   New CTO/diagrams.
    *   New or significantly changed ArchitecturePlan.
    *   New generator scripts or major edits.
    *   Production release points.
*   Bootstrapping:
    
    *   The Spec-First System Builder itself is defined by:
        *   A CTO describing its own models, APIs, services, workflows, and tech stack (Fastify + FastAPI + Prefect + DoWhy + Jinja2 + NetworkX).
        *   An ArchitecturePlan describing its own modules.
    *   v0 is implemented semi-manually:
        *   Initial Fastify/FastAPI services.
        *   Initial Prefect flows and simple generators.
    *   From v1 onward:
        *   Use the system to refine its own CTO/Plan.
        *   Generate updated generators and code for itself.
        *   Apply the same metric and causal feedback loops to its own evolution.

* * *
