1. **Intent → CTO Spec (Schema‑First Grounding)**  
   - Input: natural‑language description of the target app.  
   - LLM (translator) produces a **CTO JSON/graph** containing:
     - `data_models`, `api_resources`, `workflows`, `services`, `datastores`, `external_systems`, `architecture_policies`.  
   - LLM also produces **Mermaid diagrams** (system `flowchart`, workflow `stateDiagram-v2`, optional `sequenceDiagram`).  
   - Options:
     - Represent CTO as pure JSON Schema + OpenAPI, or as a richer graph (Neo4j/NetworkX).  
     - Store in Git + optional vector/graph index.  
   - Human reviews & approves CTO + diagrams; frozen as ground truth.

2. **Architecture Planning (Phase 1.5 – Modularity Plan)**  
   - Input: CTO + diagrams + architectural rules + Lessons Learned.  
   - LLM generates one or more **ArchitecturePlan.json** candidates:
     - Layers (e.g., `domain`, `infra`, `api`)  
     - Modules (`id`, `file`, `layer`, `exports`, `imports_from`).  
   - Evaluator:
     - Builds module dependency graph; checks cycles & layer violations.  
     - Computes metrics: `num_modules`, `max_fan_in`, `max_fan_out`, etc.  
   - Options:
     - **Refinement loop (Prefect)**: generate candidates → score → pick best until:
       - No score improvement over a threshold or max iterations.  
       - Constraints satisfied (no cycles, bounded fan‑in).  
     - Use **causal weights** (from DoWhy) to shape the scoring function.

3. **Generator Script Creation (LLM as Translator, Phase 2)**  
   - Input: frozen CTO + ArchitecturePlan (+ diagrams + Lessons Learned).  
   - LLM generates **deterministic Python generator scripts** (each a small CLI) using Jinja2:
     - `gen_ts_schema.py`: CTO `data_models` → TS interfaces + Zod.  
     - `gen_db_schema.py`: `data_models` → Prisma/SQL schema.  
     - `gen_workflow_machine.py`: Mermaid workflows → TS state machines.  
     - `gen_middleware.py`: `api_resources` + Plan → Express/Nest routes/controllers.  
     - `gen_tests.py`: spec invariants + APIs → Jest/Vitest tests.  
   - Constraints:
     - No network/time/random; only whitelisted imports.  
     - All code emitted via templates, not inline concatenation.  
   - Options:
     - Single `generator.py` with subcommands vs multiple scripts.  
     - Different target stacks (Express, NestJS, Fastify; Prisma vs raw SQL).

4. **Deterministic Build in Sandbox (Phase 3, Orchestrated DAG)**  
   - Orchestrator: Prefect (or similar).  
   - Steps:
     1. Load CTO + Plan + diagrams; select generators.  
     2. Run architecture planning (if not already frozen).  
     3. **Parallelizable generation**:
        - TS models, DB schema, workflow machines in parallel.  
        - Fan‑out per resource for middleware and tests.  
     4. Compile and run tests in a container (Docker), with pinned deps and `PYTHONHASHSEED=0`.  
   - Options:
     - Dynamic concurrency based on project size/complexity and past causal insights.  
     - Alternative orchestrators (Airflow, Dagster, Argo) if preferred.

5. **Validation, Testing, and Lessons Learned (Phase 4)**  
   - Run:
     - TS/Node tests (Jest/Vitest, Supertest).  
     - Static checks (TS compile, lint).  
     - Optional property/contract tests (fast‑check, Schemathesis/Hypothesis).  
     - Diagram/spec consistency checks (e.g., every module in Plan has code).  
   - On failures or manual fixes:
     - Capture diffs, related spec/plan snippets, error messages.  
     - Store as **Lessons Learned** in a vector/graph store for future prompts.  
   - Options:
     - Auto‑repair loops: LLM proposes generator/template patches → rebuild → re‑test, with human gate if failing repeatedly.

6. **Metrics Harvesting & Causal Feedback (Phase 4.5)**  
   - After each build/version, aggregate **architecture history** row including:
     - From Plan/graphs: `num_modules`, `num_cycles`, `max_fan_in/out`, `arch_refinement_iterations`.  
     - From pipeline: task durations, parallelism levels, wall‑clock build time.  
     - From LLM wrapper: tokens, latency, models per step.  
     - From Git/CI: bugfix commits/PRs, CI red‑green cycles, prod incidents.  
   - Periodic Prefect flow:
     - Use **DoWhy** to estimate causal effects:
       - E.g., `max_fan_in -> bugfix_commits`, `num_cycles -> ci_failures`, `max_parallel_tasks -> build_time`.  
     - Emit `causal_weights.json` with effect sizes.  
   - Next iterations:
     - Use these weights in architecture scoring, parallelism policy, and planning prompts.  

7. **Governance, Human‑in‑the‑Loop, and Bootstrapping**  
   - Governance:
     - Specs, Plans, diagrams, generator scripts, and generated code are all versioned in Git and reviewed via PRs.  
     - Human approvals at: spec/CTO, Plan, generator scripts, and promotion to production.  
   - Bootstrapping:
     - Treat the **System Builder** itself as a project with its own CTO + Plan.  
     - Manually implement v0 generators and flows.  
     - Use the system to iteratively re‑generate and refine its own architecture and generators.