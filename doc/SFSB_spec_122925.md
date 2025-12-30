
Spec‑First System Builder – v0 Specification
============================================

0\. Purpose and Principles
--------------------------

The **Spec‑First System Builder** is a platform that:

*   Takes **natural-language descriptions** of software systems.
*   Refines them into a **formal natural-language spec** (NLSpec).
*   Translates NLSpec into a **Central Truth Object** (CTO) JSON.
*   Plans and validates architecture down to **module and function-level specification grains**.
*   Uses deterministic **generator scripts + templates** to emit code.
*   Orchestrates builds/tests deterministically (Prefect + Docker).
*   Learns over time via **metrics** and **causal inference** (DoWhy).

Key principles:

*   **Schema-first**: CTO, ArchitecturePlan, ModuleSpecs, and FunctionSpecs are structured artifacts validated against external JSON Schemas and Pydantic models.
*   **LLM-assisted, deterministic core**:
    *   LLMs are used only for translation and planning (no runtime dependence).
    *   Code generation is via deterministic Python CLIs + Jinja2 templates.
*   **Human-in-the-loop** at critical approvals (NLSpec, CTO+diagrams, architecture/spec grains, generators).
*   **Git‑aligned & reproducible**:
    *   All important artifacts and prompts are versioned in Git.
    *   Each build is associated with a specific commit (“one build, one snapshot”).

* * *

1\. Architecture and Technology Stack
-------------------------------------

### 1.1 Client / Gateway (Node/TS + Fastify)

*   Language: TypeScript
*   Runtime: Node.js
*   Framework: Fastify
*   Responsibilities:
    *   Serve a web UI for:
        *   Phase 1 NLSpec chat and review.
        *   Viewing/approving CTO, diagrams, ArchitecturePlan, ModuleSpecs, FunctionSpecs.
        *   Inspecting builds, graphs, and metrics.
    *   Provide a local HTTP API for automation and integration.
    *   Proxy relevant requests to Python/FastAPI backend.
*   Testing: Vitest, Supertest or similar.

### 1.2 Backend (Python + FastAPI)

*   Language: Python 3.x
*   Framework: FastAPI
*   Responsibilities:
    *   Phase 1 – NLSpec:
        *   Conversational refinement.
        *   Validation and approval.
    *   Phase 2 – CTO & diagrams:
        *   CTO generation from NLSpec.
        *   Validation and diagram synthesis.
    *   Phase 3 – Architecture Planning & Spec Grains:
        *   ArchitecturePlan (layers & modules).
        *   ModuleSpecSet and FunctionSpecSet.
        *   Graph/DAG construction and validation.
    *   Phase 4 – Generator Scripts:
        *   LLM-assisted design/refinement of deterministic Python generator CLIs and Jinja2 templates.
    *   Phase 5 – Deterministic Builds:
        *   Prefect + Docker flows for generation, compile, tests.
        *   Git/commit consistency enforcement.
    *   Phase 6 – Validation & Causal Feedback:
        *   Spec↔code alignment checks.
        *   Lessons Learned collection.
        *   DoWhy-based causal analysis.
*   Libraries:
    *   FastAPI, Pydantic
    *   Prefect
    *   Jinja2
    *   NetworkX
    *   DoWhy
    *   PostgreSQL drivers/ORM as needed

### 1.3 LLM Integration

*   LLM access via **OpenRouter** (and optionally OpenAI SDK).
*   LLMs are used for:
    *   Phase 1: Conversational NLSpec refinement.
    *   Phase 2: NLSpec → CTO; CTO → diagrams (if LLM-assisted).
    *   Phase 3: CTO → ArchitecturePlan → ModuleSpecs → FunctionSpecs.
    *   Phase 4: Designing/refining generator scripts/templates.
*   Every LLM call logs:
    *   Phase/step ID.
    *   Model name.
    *   Token counts (prompt, completion, total).
    *   Latency and retry count.
    *   Prompt file paths and content hashes used.
*   No LLM calls are made:
    *   In generator scripts during builds.
    *   During runtime of generated applications.

### 1.4 Persistence and Infrastructure

*   Database: PostgreSQL
    *   For projects, artifacts, builds, metrics, Lessons Learned, causal analysis results.
*   Filesystem or object store:
    *   For:
        *   spec/ artifacts (NLSpec, CTO, plans, specs, diagrams).
        *   .sfsb/ configuration, prompts, artifacts, logs.
        *   Generator scripts and templates.
*   Containerization: Docker
    *   Separate containers for Python and Node/TS builds/tests.
*   Orchestration: Prefect
    *   Local agent/server initially.
    *   Flows for Phase 3 planning and Phase 5 builds.

### 1.5 Repository Layout (Project Level)

On project initialization:

    spec/
      nl_spec_v1.md
      # later:
      cto_v1.json
      architecture_plan_v1.json
      module_specs_v1.json
      function_specs_v1.json
      diagrams/
        # mermaid files
    
    .sfsb/
      prompts/
        phase1_nl_spec/
          system.md
          questions.md
        phase2_cto/
          system.md
        phase2_diagrams/
          system.md
        phase3_arch_plan/
          system.md
        phase3_module_specs/
          system.md
        phase3_function_specs/
          system.md
        phase4_generators/
          system.md
          # generator-specific prompts later
      logs/
        phase1_conversations/
          # per-session chat logs
        llm_calls/
          # optional aggregate logs
      artifacts/
        nl_spec_v1.json
        cto_v1_draft.json
        cto_v1_validation_report.json
        # additional validation/assumption files
    
    generators/
      # LLM-designed Python CLIs for codegen
    
    templates/
      # Jinja2 templates (TS, Python, DB, tests)

Schemas and Pydantic models live in the backend repo (not in the project repo).

* * *

2\. Cross-cutting Rules
-----------------------

### 2.1 Prompt and Context Management

*   All system prompts and context for LLM calls are .md files in .sfsb/prompts/<phase>/.
    *   E.g. .sfsb/prompts/phase2\_cto/system.md.
*   Backend composes prompts only from:
    *   These files,
    *   Current project artifacts (NLSpec, CTO, etc.).
*   Designers can:
    *   Edit existing prompts.
    *   Add extra context files (e.g. domain notes) in the same folder.
*   Versioning:
    *   Via Git commits.
    *   For each LLM call, log:
        *   prompt\_files: list of paths used.
        *   prompt\_hashes: content hashes (e.g. SHA-256).

No hidden prompts live exclusively in code.

### 2.2 JSON Schemas and Pydantic Models

*   Each structured artifact (NLSpec, CTO, ArchitecturePlan, ModuleSpecSet, FunctionSpecSet) is validated against:
    *   A JSON Schema file, e.g.:
        *   nlspec.schema.json
        *   cto.schema.json
        *   architecture\_plan.schema.json
        *   module\_specs.schema.json
        *   function\_specs.schema.json
    *   And a Pydantic model with the same conceptual structure.
*   These schemas/models are:
    *   Maintained in the backend repository (e.g. backend/schemas/, backend/models/).
    *   Versioned with the tool.
*   Artifacts include a \_meta.schema entry indicating schema ID/version so the backend knows which schema to use.

### 2.3 Assumptions and Missing Information

For each LLM-produced planning artifact (CTO, ArchitecturePlan, ModuleSpecs, FunctionSpecs):

*   Output must include:
    *   assumptions: list of assumptions made where the source spec was ambiguous.
    *   missing\_information: list of information that appears necessary but isn’t present upstream.
*   These are stored as sidecar JSON files in .sfsb/artifacts/ (or under \_meta).
*   Validators:
    *   Treat structural and referential errors as hard failures.
    *   Treat most assumptions/missing\_info as warnings in v0, but surface them prominently.
*   The system may recommend:
    *   Revisiting NLSpec or CTO when major missing info is discovered.
*   The “hard” architecture DAG includes only validated, non-assumed elements.

### 2.4 Git and Build Consistency

*   The repo must be a Git repository.
*   Before running a build:
    *   System checks for uncommitted changes in:
        *   spec/
        *   .sfsb/prompts/
        *   .sfsb/artifacts/
        *   Generator and template directories.
    *   In strict mode:
        *   If dirty, build is rejected with an instruction to commit or stash changes.
*   Each build records:
    *   repo\_commit\_hash
    *   branch\_name
    *   dirty\_state (should be false in strict mode)
    *   Versions/hashes of NLSpec, CTO, ArchitecturePlan, ModuleSpecs, FunctionSpecs, generator scripts, templates, and prompts used.
*   “One build, one snapshot”:
    *   Each build is bound to a specific commit and set of artifacts.
    *   Avoids silent drift between specs, prompts, templates, and generated code.

* * *

3\. Phase 1 – Conversational NL Specification (NLSpec)
------------------------------------------------------

### 3.1 Objective

Produce a **formal NLSpec** that:

*   Captures:
    *   Project name and short description.
    *   Target platforms and stack (languages, runtimes, frameworks).
    *   Core functionality and use cases.
    *   Optional constraints and risks.
*   Is human-editable (Markdown) and machine-validated (JSON/Pydantic).
*   Serves as the sole input to CTO generation.

### 3.2 NLSpec Structure (Conceptual)

Fields (conceptual; validated via nlspec.schema.json + NLSpec model):

*   project:
    *   name (string, required)
    *   short\_description (string, required)
    *   version\_hint (string, optional)
*   platforms\_and\_stack:
    *   targets (array, required, non-empty):
        *   Each:
            *   kind (string/enum; e.g. "client\_gateway", "backend", "cli")
            *   language (string, required)
            *   runtime (string, optional)
            *   framework (string, optional)
            *   notes (string, optional)
    *   persistence\_preferences (string/list, optional)
    *   llm\_usage\_policy (string, optional)
*   core\_functionality:
    *   primary\_users\_or\_actors (string/list, required)
    *   main\_capabilities (string/list, required)
    *   example\_workflows (string, optional)
*   constraints\_and\_policies (optional):
    *   must\_haves (string/list)
    *   nice\_to\_haves (string/list)
    *   known\_non\_goals (string/list)
*   open\_questions\_and\_risks (optional):
    *   open\_questions (string/list)
    *   risks (string/list)

### 3.3 Representation and Storage

*   Human file: spec/nl\_spec\_vN.md (Markdown with predefined headings).
*   Structured form: .sfsb/artifacts/nl\_spec\_vN.json.
*   On approval, canonical file: spec/nl\_spec\_vN\_approved.md.

### 3.4 Chat‑first Workflow

*   User starts Phase 1 via UI or CLI.
*   Backend uses LLM (with prompts in .sfsb/prompts/phase1\_nl\_spec/) to:
    *   Ask questions to populate NLSpec sections.
    *   Suggest wording.
    *   Flag obvious inconsistencies as advice.
*   Output:
    *   Draft nl\_spec\_vN.md + structured JSON.

### 3.5 Validation and Approval

*   Deterministic validator checks:
    *   All required fields present/non-empty.
    *   Types match schema.
*   If invalid:
    *   Report missing/invalid fields.
    *   Open new chat session for refinement.
*   If valid:
    *   User runs approval:
        *   CLI: sfsb-spec approve-nl
        *   Or UI: “Approve NL Spec”.
    *   Approved NLSpec is frozen and referenced in subsequent artifacts (nl\_spec\_ref in CTO).

### 3.6 Logging

*   Each chat session:
    *   Logged as Markdown/YAML under .sfsb/logs/phase1\_conversations/.
    *   Contains:
        *   Session metadata (timestamps, model).
        *   Full conversation turns.
        *   Tokens/latency per assistant response.

* * *

4\. Phase 2 – CTO Generation & Diagram Synthesis
------------------------------------------------

### 4.1 Objective

From an **approved NLSpec**:

*   Generate a **CTO JSON** with all required sections.
*   Validate CTO structurally and by references.
*   Generate and validate system + workflow diagrams (Mermaid).
*   Get human approval before architecture planning.

### 4.2 CTO Structure and Storage

CTO (validated via cto.schema.json + CTO Pydantic model) must include:

*   project
*   nl\_spec\_ref:
    *   id, path, hash, approved\_at
*   technology\_stack
*   data\_models
*   api\_resources
*   services
*   datastores
*   external\_systems
*   workflows
*   architecture\_policies

CTO is stored as:

*   spec/cto\_vN.json.

No manual editing; always regenerated from NLSpec.

### 4.3 CTO Generation

*   Input: structured NLSpec.
*   Single LLM call for v0 (prompt in .sfsb/prompts/phase2\_cto/).
*   Output draft: .sfsb/artifacts/cto\_vN\_draft.json.
*   Also output assumptions and missing\_information about NLSpec gaps.

### 4.4 CTO Validation

*   Schema/Pydantic validation:
    *   All required sections present.
    *   Internal fields match expected types/structures.
*   Referential integrity:
    *   API models referenced exist in data\_models.
    *   Services’ handles\_models and depends\_on reference valid entities.
    *   Datastore references valid.
*   Consistency with NLSpec (advisory):
    *   Warn if platform/stack or capabilities diverge significantly from NLSpec.

If validation fails:

*   Report error list.
*   User can:
    *   Regenerate CTO (possibly after prompt edits).
    *   Or refine NLSpec in Phase 1.

### 4.5 Diagrams

From validated CTO:

*   Generate Mermaid diagrams using LLM or deterministic patterns (prompts in .sfsb/prompts/phase2\_diagrams/ if LLM):
    *   spec/diagrams/cto\_vN\_system.mmd – system-level flowchart.
    *   spec/diagrams/cto\_vN\_workflow\_<workflow\_id>.mmd – workflow stateDiagram‑v2 per workflow.

Validation:

*   Syntax: via Mermaid CLI/parser.
*   Semantics:
    *   Nodes correspond to CTO services/datastores/external\_systems/workflows.
    *   Workflow states and transitions match workflows in CTO.

Diagram failures block progression; regenerate or update CTO/NLSpec as needed.

### 4.6 Human Approval

*   Review CTO and diagrams.
*   Approve via CLI/UI:
    *   sfsb-cto approve --version vN.
*   Only approved CTO+diagrams can be used in Phase 3.

* * *

5\. Phase 3 – Architecture Planning & Specification Grains
----------------------------------------------------------

### 5.1 Objective

From approved CTO:

*   Design a modular **ArchitecturePlan** (layers, modules).
*   Define **ModuleSpecSet** (module-level grains).
*   Define **FunctionSpecSet** (function-level grains).
*   Build and validate architecture DAGs:
    *   Module dependency graph.
    *   Per-module function graphs.
    *   Inter-module function interface edges.
*   Prepare all information needed for code generation.

All LLM-assisted steps are orchestrated by Prefect; validation is deterministic.

### 5.2 ArchitecturePlan

*   Artifact: spec/architecture\_plan\_vN.json.
*   Validated via architecture\_plan.schema.json + model.
*   Content:
    *   layers: e.g. \["domain", "infra", "api"\].
    *   modules: array of module definitions:
        *   id (e.g. mod.project\_service)
        *   name
        *   layer
        *   description
        *   file\_path (relative path/pattern)
        *   imports\_from: list of module IDs.
    *   \_meta: schema info, metrics, assumptions/missing\_info.

#### 5.2.1 Generation

*   Task: generate\_architecture\_plan\_candidates.
*   Input: CTO + architecture\_policies.
*   LLM with prompts in .sfsb/prompts/phase3\_arch\_plan/.
*   Output: one or more ArchitecturePlan candidates.

#### 5.2.2 Evaluation

*   Task: evaluate\_architecture\_plans (NetworkX).
*   Build module graphs:
    *   Nodes: modules.
    *   Edges: imports\_from dependencies.
*   Enforce:
    *   No illegal cycles.
    *   Layer rules.
    *   Fan-in/out thresholds per policy.
*   Select best candidate based on deterministic heuristics.

#### 5.2.3 Human Approval

*   Review chosen ArchitecturePlan and metrics.
*   Approve via CLI/UI:
    *   sfsb-arch approve-plan --file spec/architecture\_plan\_vN.json.

### 5.3 ModuleSpecSet

*   Artifact: spec/module\_specs\_vN.json.
*   Validated via module\_specs.schema.json + model.
*   One ModuleSpec per module.

Conceptual fields per ModuleSpec:

*   id (e.g. mod.project\_service)
*   name
*   layer
*   description
*   responsibilities (list)
*   inputs (references to CTO data\_models/api\_resources)
*   outputs (models, events)
*   dependencies (other module IDs)
*   invariants (list)
*   non\_functional (performance/security/reliability notes)
*   Optional \_meta: assumptions/missing\_info, etc.

#### 5.3.1 Generation

*   Task: generate\_module\_specs.
*   Input: CTO + ArchitecturePlan.
*   LLM with .sfsb/prompts/phase3\_module\_specs/.

#### 5.3.2 Validation

*   Task: validate\_module\_specs.
*   Checks:
    *   Every ArchitecturePlan module has exactly one ModuleSpec.
    *   References (models, APIs) exist in CTO.
    *   dependencies allowed by ArchitecturePlan and policies.
*   Module graph revalidated for consistency.

### 5.4 FunctionSpecSet

*   Artifact: spec/function\_specs\_vN.json.
*   Validated via function\_specs.schema.json + model.
*   Multiple FunctionSpecs per module.

Conceptual fields per FunctionSpec:

*   id (e.g. fn.project\_service.create\_project)
*   module\_id (e.g. mod.project\_service)
*   name (e.g. create\_project)
*   visibility (public / internal)
*   description
*   inputs: list of:
    *   name
    *   model (ref to CTO data\_models)
    *   direction (in/out for clarity)
*   outputs: list, same structure.
*   errors: list of error types.
*   preconditions: list.
*   postconditions: list.
*   side\_effects:
    *   has\_side\_effects (boolean, required)
    *   categories (list; e.g. \["db\_write", "metrics", "logging", "network\_call", "file\_io"\])
    *   description (string)
*   complexity\_estimate:
    *   Enum/string; e.g. TRIVIAL, LOW, MEDIUM, HIGH, VERY\_HIGH.
*   called\_functions: list of function IDs:
    *   e.g. fn.project\_repository.insert\_project.
*   related\_workflows: list of workflow IDs from CTO.
*   Optional \_meta: assumptions/missing\_info, notes.

#### 5.4.1 Generation

*   Task: generate\_function\_specs.
*   Input: CTO + ArchitecturePlan + ModuleSpecSet.
*   LLM with .sfsb/prompts/phase3\_function\_specs/.

#### 5.4.2 Validation & Graphs

*   Task: validate\_function\_specs\_and\_build\_graphs.
*   Checks:
    *   module\_id matches existing ModuleSpecs.
    *   Models in inputs/outputs exist in CTO.
    *   called\_functions reference existing FunctionSpecs.
    *   Cross-module calls respect architecture layers.

Graphs:

*   Per-module function graphs:
    *   Nodes: functions in that module.
    *   Edges: intra-module calls.
*   Inter-module function interface edges:
    *   Summarized module→module call edges from cross-module called\_functions.

These combined form the architecture DAG for code generation and analysis.

### 5.5 Human Approval

*   Review ArchitecturePlan + ModuleSpecs + FunctionSpecs.
*   Approve entire set:
    *   CLI: sfsb-arch approve-all --plan ... --modules ... --functions ...
    *   Or via UI.

Only then can Phase 4 (generator creation) and Phase 5 (builds) proceed.

* * *

6\. Phase 4 – Generator Script Creation (Python CLIs + Jinja2)
--------------------------------------------------------------

### 6.1 Objective

Design and refine deterministic **Python generator CLIs** and **Jinja2 templates** which:

*   Consume CTO + ArchitecturePlan + ModuleSpecs + FunctionSpecs.
*   Emit TS/Python code, DB schemas, etc.
*   Embed spec-grain IDs and comments into code.
*   Are run without LLMs in Phase 5.

### 6.2 v0 Generator Types

For v0, in scope:

1.  **Backend routers (FastAPI)**:
    
    *   Input:
        *   cto\_vN.json
        *   architecture\_plan\_vN.json
        *   module\_specs\_vN.json
        *   function\_specs\_vN.json
    *   Output:
        *   FastAPI routers under e.g. backend/app/routers/.
        *   Route handlers that:
            *   Map CTO api\_resources operations to modules+functions.
            *   Include FunctionSpec ID comments.
2.  **Backend modules/services**:
    
    *   Input:
        *   ArchitecturePlan + ModuleSpecs + FunctionSpecs.
    *   Output:
        *   Python modules under backend/app/modules/.
        *   One file per module (or as architected).
        *   Function stubs or minimal implementations with:
            *   Signatures derived from FunctionSpecs.
            *   Comments showing spec-grain IDs, side\_effects, complexity, etc.
3.  **DB schema/migrations**:
    
    *   Input:
        *   CTO.data\_models and datastores.
    *   Output:
        *   DB schema artifacts under backend/db/:
            *   SqlAlchemy models, Alembic migrations, or raw SQL DDL.

Additional types (Fastify routes, workflow machines, tests) are planned but not required for v0.

### 6.3 Generator Artifacts and Requirements

*   Scripts under generators/:
    *   e.g. gen\_backend\_routers.py, gen\_backend\_services.py, gen\_db\_schema.py.
*   Templates under templates/:
    *   Organized by language/component.

Requirements:

*   Plain Python CLIs:
    *   No network/LLM dependencies.
    *   No time/env randomness; deterministic given inputs.
*   Allowed imports restricted to:
    *   Python stdlib and approved libs (e.g. Jinja2, json, pathlib).
*   CLIs accept:
    *   Paths to CTO, ArchitecturePlan, ModuleSpecs, FunctionSpecs.
    *   Output directory or base path.
*   Emit reproducible code.

### 6.4 LLM‑assisted Design & Refinement

Prompts under .sfsb/prompts/phase4\_generators/.

Two flows:

1.  **Initial design**:
    
    *   For each generator type:
        *   LLM proposes a generator script and basic templates.
        *   Output is written to generators/ and templates/.
        *   assumptions/missing\_information recorded.
2.  **Refinement**:
    
    *   After failures or Lessons Learned:
        *   LLM suggests modifications to specific generators/templates.
        *   Same validation & human review steps.

### 6.5 Validation of Generators

*   Static validation:
    *   Parse Python.
    *   Enforce import whitelist.
    *   Check CLI interface.
*   Deterministic smoke test:
    *   Run generator with sample specs in a sandbox.
    *   Ensure generated code compiles (Python) or type-checks (TS) at least minimally.

Human review via PR completes the approval.

* * *

7\. Phase 5 – Deterministic Build & Orchestration
-------------------------------------------------

### 7.1 Objective

Using approved:

*   NLSpec, CTO, diagrams,
*   ArchitecturePlan, ModuleSpecs, FunctionSpecs,
*   Generators and templates,

run deterministic builds via Prefect + Docker:

*   Generate code.
*   Install deps and run tests.
*   Collect metrics.
*   Enforce commit ↔ build consistency.

### 7.2 Git Preconditions

*   Before starting a build:
    *   Check Git status.
    *   If there are uncommitted changes in:
        *   spec/,
        *   .sfsb/prompts/,
        *   .sfsb/artifacts/,
        *   generators/, templates/:
            *   In strict mode: refuse to run until changes are committed or stashed.
*   Each build logs:
    *   repo\_commit\_hash, branch\_name, dirty\_state.

### 7.3 Prefect Flow

Typical build flow:

1.  **Init**:
    
    *   Read commit hash, spec versions, generator versions.
    *   Create a BuildExecution record.
2.  **Docker environments**:
    
    *   Python container.
    *   Node/TS container.
3.  **Code generation**:
    
    *   Run generator CLIs inside containers:
        *   Backend routers.
        *   Backend modules.
        *   DB schema/migrations.
    *   Code emitted into tracked source directories.
4.  **Dependencies & compilation**:
    
    *   Node/TS: npm install, npm test etc.
    *   Python: pip install, pytest, optional mypy/ruff.
5.  **Tests and checks**:
    
    *   Record results and logs.
6.  **Post-build Git check (optional enforce)**:
    
    *   Optionally warn/enforce that generated changes should be committed.

All steps are deterministic given inputs.

* * *

8\. Phase 6 – Validation, Lessons, and Causal Feedback
------------------------------------------------------

### 8.1 Objective

After builds:

*   Validate spec↔code alignment.
*   Capture Lessons Learned.
*   Aggregate metrics.
*   Run causal analysis (DoWhy) over historical runs.
*   Use insights to adjust earlier phases (architecture, prompts, models).

### 8.2 Spec↔Code Alignment

Using IDs in code comments (from FunctionSpecs/ModuleSpecs):

*   Scan code for SpecGrain comments like:
    *   SpecGrain: fn.project\_service.create\_project.
*   Validate:
    *   Every FunctionSpec ID appears in exactly one function definition.
    *   Every ModuleSpec ID appears in the appropriate module file(s).
*   Report:
    *   Missing implementations.
    *   Stale references.

### 8.3 Lessons Learned

On failures:

*   When tests fail, or generated code has issues, or humans patch code/generators:
    *   Record LessonsLearned entries:
        *   BuildExecution ID, commit hash.
        *   Error types, messages, stack traces.
        *   Relevant spec snippets (CTO, ArchitecturePlan, ModuleSpecs, FunctionSpecs).
        *   Generator/template references.
        *   Human fix description (if any).
*   Store in Postgres (and optionally a vector DB).

### 8.4 Metrics & Causal Analysis

Per build/LLM step, log:

*   Build metrics:
    *   Task runtimes.
    *   Success/failure states.
    *   Test coverage metrics (if available).
*   Architecture metrics:
    *   Module/function graph metrics (fan-in/out, depth, complexity distribution).
*   LLM metrics:
    *   Model, tokens, latencies.
    *   Prompt files and hashes.
*   Generator/template versions:
    *   File paths and hashes.

Periodically:

*   A Prefect flow runs DoWhy:
    *   Build causal graphs linking:
        *   Architecture properties,
        *   Function complexities, side-effects,
        *   Prompt/template variants,
        *   Build outcomes (failures, instability, cost).
    *   Outputs a causal\_weights.json or equivalent in .sfsb/artifacts/:
        *   Used in future:
            *   ArchitecturePlan scoring.
            *   Model and prompt choices.
            *   Refinement depth in Phase 3.

* * *

9\. Artifacts and External Materials (Implementation Checklist)
---------------------------------------------------------------

To implement v0, you’ll need to create:

*   **Backend schemas & models** (in backend repo):
    
    *   backend/schemas/nlspec.schema.json
    *   backend/schemas/cto.schema.json
    *   backend/schemas/architecture\_plan.schema.json
    *   backend/schemas/module\_specs.schema.json
    *   backend/schemas/function\_specs.schema.json
    *   Corresponding Pydantic models in backend/models/\*.py.
*   **Initial prompt files**:
    
    *   .sfsb/prompts/phase1\_nl\_spec/system.md, questions.md.
    *   .sfsb/prompts/phase2\_cto/system.md.
    *   .sfsb/prompts/phase2\_diagrams/system.md.
    *   .sfsb/prompts/phase3\_arch\_plan/system.md.
    *   .sfsb/prompts/phase3\_module\_specs/system.md.
    *   .sfsb/prompts/phase3\_function\_specs/system.md.
    *   .sfsb/prompts/phase4\_generators/system.md (and per‑generator prompts later).
*   **Minimal generator scripts (v0)**:
    
    *   generators/gen\_backend\_routers.py
    *   generators/gen\_backend\_services.py
    *   generators/gen\_db\_schema.py
    *   Matching Jinja2 templates under templates/.
*   **Core Prefect flows**:
    
    *   Phase 3 planning flow.
    *   Phase 5 build flow.
    *   Phase 6 causal analysis flow.
*   **FastAPI endpoints & CLI wrappers** aligned with phases:
    
    *   e.g., sfsb-spec, sfsb-cto, sfsb-arch, sfsb-gen, sfsb-build, sfsb-metrics, sfsb-causal.

