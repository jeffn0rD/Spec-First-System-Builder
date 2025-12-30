You treat feature changes almost the same way as initial creation, but starting from the _existing_ CTO, ArchitecturePlan, and code instead of a blank slate. Roughly:

1.  **Capture the change as intent + diff to the spec**
    
    *   Describe the new feature or behavior change in natural language.
    *   Feed this + the current CTO into the “spec translator” LLM, with instructions:
        *   “Update this CTO to reflect the requested behavior change. Preserve existing semantics unless explicitly changed. Output a new CTO vX.Y.”
    *   The LLM proposes:
        *   New/changed data models (fields, enums, relationships)
        *   New/changed endpoints or workflows
    *   Run schema/consistency checks; review and approve.
    *   Result: **CTO vN+1** that encodes the feature.
2.  **Regenerate / refine diagrams and architecture plan**
    
    *   Regenerate or patch Mermaid diagrams from CTO vN+1:
        *   System diagram: new services or edges if needed
        *   Workflow diagrams: new states/transitions if behavior changed
    *   Either:
        *   Keep the existing ArchitecturePlan if the change is small (e.g., just extend an existing module), or
        *   Run the **architecture planning/refinement** flow constrained to be _minimally invasive_:
            *   “Propose an updated ArchitecturePlan that supports these new CTO changes while changing as few modules/files as possible. Avoid breaking existing interfaces unless CTO requires it.”
    *   Run the plan evaluator:
        *   Ensure no new cycles / layer violations.
        *   See if metrics remain healthy or if the change is starting to create god modules/hotspots.
    *   Approve **ArchitecturePlan vN+1**.
3.  **Regenerate only the affected artifacts (incremental codegen)**  
    With the updated CTO + Plan:
    
    *   Determine the impact set:
        *   Which models changed?
        *   Which endpoints/workflows depend on them?
        *   Which modules in ArchitecturePlan own those responsibilities?
    *   Orchestrator (Prefect) runs only the necessary generators for that set:
        *   If you added fields to Order:
            *   Re-run gen\_ts\_schema.py for Order.
            *   Re-run gen\_db\_schema.py (or only for affected tables).
            *   Re-run middleware/tests for resources using Order.
        *   If you added a new endpoint:
            *   Run gen\_middleware.py and gen\_tests.py for that resource.
            *   Potentially a new controller/service module if Plan says so.
    *   Since generators are deterministic:
        *   Changes are predictable; you can diff generated code vs previous version to see exactly what changed.
4.  **Run tests + validations focused on the change, then full suite**
    
    *   First, run:
        *   Unit/API tests directly related to modified modules/resources.
        *   State-machine/workflow tests if a workflow changed.
    *   Then run:
        *   Full regression suite (can be parallelized).
        *   Static analysis (TS compile, lint).
        *   Diagram/spec consistency checks.
    *   Any failures get:
        *   Logged to Lessons Learned (spec/plan/generator snippet + error).
        *   Optionally fed into an auto‑fix loop (LLM suggests generator/template patch → re‑run).
5.  **Harvest metrics about this change**
    
    *   Tag the build/run with:
        *   Which CTO version and Plan version.
        *   Which features/CTO sections were modified (e.g., feature:order-discount).
    *   After merge and a bit of lifecycle:
        *   Git shows if this feature caused extra bugfix commits or rewrites.
        *   CI shows if it introduced more red‑green cycles.
    *   This becomes another row in architecture\_history for DoWhy:
        *   Helps learn whether certain types of changes (e.g., adding logic to already high fan‑in modules) tend to cause more bugs.
6.  **Use Lessons Learned to guide future similar changes**
    
    *   When you next add a similar feature:
        *   Retrieval (GraphRAG/vector DB) pulls previous failures/fixes around that pattern (e.g., “pagination in this framework”, “discount rules on orders”).
        *   Those constraints/examples are added to prompts for:
            *   Updating the CTO
            *   Updating the ArchitecturePlan
            *   Generating the specific generators/templates

* * *

### Concretely: what you’d do as a user

1.  **Open the “App Spec” in the System Builder UI**
    
    *   Click “Propose change” and describe:
        *   “Add discount codes to orders; users can apply one active discount per order; discounts are time‑bounded and cause recalculation of totals.”
2.  **Approve updated CTO & diagrams**
    
    *   The system shows:
        *   New Discount model, discountCode field in Order, updated order workflow.
    *   You approve CTO v2.3 and updated Mermaid diagrams.
3.  **Review updated ArchitecturePlan**
    
    *   Maybe a new domain.discount module and infra.discountRepository.
    *   The planner indicates metrics are still healthy (no cycles, max fan‑in below threshold).
    *   You approve Plan v2.1.
4.  **Run incremental build**
    
    *   Click “Generate/Update”.
    *   Prefect:
        *   Regenerates TS models for Order + Discount.
        *   Updates DB schema.
        *   Regenerates order routes/middleware and tests.
    *   CI runs tests; you see diffs in a PR.
5.  **Merge after review**
    
    *   If all tests pass and the diff looks good, you merge and deploy.

All of this uses exactly the same system; the key difference for **feature changes** is:

*   You start from existing CTO/Plan/code.
*   You constrain planning and generators to be **backward‑compatible and minimally disruptive** unless the CTO changes say otherwise.
*   You run **incremental parts** of the pipeline, not necessarily full regeneration of everything.