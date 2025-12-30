# Original Conversation Log

**User:** I have been working on a small-medium size web app project. I have been testing an AI driven workflow. The idea is that there is a loop of human->ai->human->ai...etc step by step development from specifications to production code. I have completed the specification phase and have begun generating the codebase. During the spec phase, at each step a spec document was generated and additionally I had a RAG database continually updated from the specifications. A prompt would then be generated from what had already been done in order to generate the next specification. In between I would (human) review the step, make any changes, etc, to keep things on track. I had hoped that this systematic well documented approach would keep things grounded.
Yet now throughout the sql/code generation process inconsistencies seem to continually pile up. My agent recently had a critical discrepancy between SQL and .ts schemas-- which seems to be a well grounded truth that should of been procedurally simple. What is going wrong? Is there any steps that can be taken to prevent having to loop back and fix (obvious) errors-- all which cost time and money in additional token/prompt use? It is not clear that this is really any faster then 100% human driven development, which might seem slower initially but does not have nearly as many 'loopbacks' that waste time and money, and also confuse those overseeing the development.

**Assistant:** This is a very common frustration in the current state of AI-assisted development. You have hit the **"Probabilistic vs. Deterministic Wall."**

You are trying to use a probabilistic engine (LLM/AI) to manage a deterministic system (SQL schemas and Type definitions) using a fuzzy storage method (RAG).

Here is a breakdown of what is going wrong and specific architectural shifts you can make to stop the bleeding.

### The Diagnosis: Why RAG and Specs are Failing You

1.  **RAG is Fuzzy, Code is Strict:** RAG (Retrieval-Augmented Generation) retrieves "relevant" chunks of text. However, when generating a TypeScript interface that matches a SQL table, "relevant" isn't good enough. The AI needs the **exact, current, and complete** definition. If the RAG retrieves an outdated spec snippet or misses a constraint, the AI hallucinates the gap.
2.  **The "Telephone" Game:** Your workflow is currently `Spec -> AI -> SQL` and `Spec -> AI -> TS`.
    *   The AI interprets the Spec to make SQL.
    *   The AI interprets the Spec (again) to make TS.
    *   Because LLMs are non-deterministic, these two interpretations will drift apart.
3.  **Context Contamination:** As you iterate, your RAG database fills with "plans," "revisions," and "deprecated ideas." The AI often struggles to distinguish between *what we planned to do* (Spec v1) and *what we actually decided* (Spec v2).

### The Solution: Shift to "Schema-First" Generation

To stop the inconsistencies, you must stop asking the AI to generate code from English specifications and start forcing it to generate code from a **Single Source of Truth (SSOT)**.

Here is the corrected workflow to prevent loopbacks:

#### 1. Establish a Machine-Readable SSOT
Stop relying on text documents as the bridge between SQL and Code.
*   **The Fix:** Create a "Canonical Data Model." This could be a `schema.prisma` file, an OpenAPI (Swagger) spec, or even a master JSON file defining your entities.
*   **The Workflow:**
    1.  Human/AI Loop: Generate the **Canonical Schema** from the Specs.
    2.  **Freeze the Schema.**
    3.  AI Task: "Generate SQL DDL *strictly* from this Schema file."
    4.  AI Task: "Generate TypeScript Interfaces *strictly* from this Schema file."

By deriving both the DB and the Code from the same rigid artifact (rather than the fuzzy English spec), you mathematically reduce the chance of discrepancy.

#### 2. Abandon RAG for Core Definitions (Context Stuffing)
RAG is for searching documentation or finding old discussions. It is **not** for maintaining active state.
*   **The Fix:** When generating code, do not rely on the AI to "retrieve" the schema. **Hard-inject** the current schema into the system prompt.
*   **Prompt Strategy:** "You are a coding engine. Here is the EXACT content of `schema.json`. Do not deviate. Do not use outside knowledge. Generate the SQL table for User."

#### 3. Implement "Compiler-Driven" Feedback Loops
You are currently doing the review. You are the compiler. This is expensive.
*   **The Fix:** Before the code reaches your eyes, it must pass a mechanical check.
*   **The Workflow:**
    1.  AI generates TypeScript types.
    2.  A script automatically runs a linter or a type-checker (e.g., `tsc --noEmit`).
    3.  **If it fails:** The error message is fed back to the AI automatically. "You generated code that caused this error: [Error]. Fix it."
    4.  **If it passes:** Only *then* do you review it.

#### 4. Switch from Horizontal to Vertical Development
You mentioned you "completed the specification phase" and are now doing the "codebase generation." This implies a Waterfall approach (Spec everything -> Code everything). AI struggles with this because it loses the thread of logic over long durations.

*   **The Fix:** Vertical Slicing.
*   **The Workflow:** Pick **one** feature (e.g., "User Login").
    1.  Spec the Login.
    2.  Update the SSOT Schema for Login.
    3.  Generate SQL for Login.
    4.  Generate TS for Login.
    5.  Verify consistency.
    6.  *Move to the next feature.*

### Is it actually faster?

If you continue with the "Pure Generative" approach (Text -> Code), **no, it is not faster.** You will spend more time debugging the AI's hallucinations than writing the code yourself.

However, it becomes faster if you treat the AI as a **Transpiler**, not an Architect.

**Summary of Immediate Actions:**
1.  **Stop generating code from English specs.**
2.  Create a rigid schema file (e.g., using Prisma, TypeORM, or simple JSON) that serves as the absolute master.
3.  Force the AI to read that file directly (not via RAG) to generate the SQL and TS.
4.  If the SQL and TS don't match, the fault lies in the Schema file, giving you one place to fix it, rather than two places to debug.

---

**User:** ok. so say I was starting with this initial specification:
[...Project specification details...]

****
Following your recommendations, what would be the steps to generate the application efficiently?

**Assistant:** This is a high-quality, detailed specification. It is perfect for the **Schema-First** approach because it contains specific logic (status derivations, RLS requirements) that usually gets lost in "fuzzy" generation.

Here is the step-by-step execution plan to build this efficiently, ensuring the SQL and TypeScript never drift apart.

### Phase 1: The "Frozen" Artifact (Day 1)

We will not write a single line of UI code yet. We are going to create the **Single Source of Truth (SSOT)**. Even though you are using Supabase (Postgres), we will use **Prisma Schema Language** (`schema.prisma`) as our design artifact.

*Why Prisma?* LLMs speak "Prisma" much better than they speak raw SQL DDL or TypeScript interfaces. It is concise, defines relationships clearly, and is strictly typed.

**Step 1: Generate the Master Schema**
*   **Prompt:** "Act as a Senior Database Architect. Take the following project specification and convert the 'Data Model' section into a strict `schema.prisma` file. Ensure every model has a `user_id` field for RLS. Use Enums for statuses. Add comments for logic like 'sum=0 -> Unpaid'."
*   **Action:** Paste your Spec.
*   **Output:** You will get a file defining `User`, `Client`, `Project`, `Document`, `LineItem`, etc.
*   **Human Review:** Check this file manually. Does `Document` have `project_id`? Is it optional? **Fix it here. Once this file is saved, it is the Law.**

### Phase 2: The Database Layer (Day 1-2)

Now, we stop using the English spec. We only use the `schema.prisma` file.

**Step 2: Generate SQL & RLS**
*   **Prompt:** "You are a PostgreSQL expert. Read this `schema.prisma` file. Generate the raw PostgreSQL DDL to create these tables.
    1. Add Row Level Security (RLS) policies ensuring users can only select/insert/update rows where `user_id = auth.uid()`.
    2. Create the Indexes defined in the schema."
*   **Input:** The `schema.prisma` file.

**Step 3: Generate Logic Triggers (The "Hard" Logic)**
Your spec has complex logic (e.g., *Invoice status derived from payments*). Do not put this in the frontend. Put it in the DB.
*   **Prompt:** "Read the `schema.prisma` file. I need a PostgreSQL Function and Trigger for the `Document` table.
    Logic: When a `Payment` is inserted/updated, recalculate the `Document.status`.
    Rules: If sum=0 -> 'Unpaid'. If sum < total -> 'Partial'. If sum >= total -> 'Paid'.
    Generate the SQL."

**Step 4: Verification**
*   Run these SQL scripts in Supabase. If they fail, paste the error to the AI. Do not move forward until the DB exists and triggers work.

### Phase 3: The Application Layer (Day 2)

Now we generate the TypeScript definitions. Again, we do **not** use the English spec. We use the `schema.prisma` or the SQL DDL.

**Step 5: Generate Zod Schemas & Types**
Since you are using Astro/Svelte (Frontend) and Fastify (Backend), you need shared types.
*   **Prompt:** "Read this `schema.prisma` file. Generate a TypeScript file containing:
    1. TypeScript Interfaces for every model.
    2. Zod Schemas for validation (e.g., `CreateClientSchema`, `UpdateInvoiceSchema`).
    3. Ensure Enums match the database."
*   **Result:** A `types.ts` file that is mathematically guaranteed to match your Supabase DB.

### Phase 4: Vertical Slicing (The Build Loop)

Now we build the app. Do not build "The Backend" then "The Frontend." Build **Module 4 (Clients)** first. It is the dependency for everything else.

**Slice A: Client Directory (The Pilot)**
1.  **Backend (Fastify):**
    *   **Prompt:** "Using the `types.ts` file and the `Client` table definition, write a Fastify route to `POST /clients` and `GET /clients`. Use Supabase-js for the DB connection."
2.  **Frontend (Svelte):**
    *   **Prompt:** "Using the `types.ts` file, create a Svelte component `ClientList.svelte` that fetches data from the API and displays it. Use the `Client` interface for type safety."
3.  **Review:** Does it work? If yes, the pipeline is valid.

**Slice B: Project Management (The Relation)**
1.  **Prompt:** "Refer to `types.ts`. A Project belongs to a Client. Create the Fastify CRUD for Projects. Ensure `client_id` is validated."

**Slice C: The Transaction Hub (The Beast)**
This is the hardest part. Break it down:
1.  **Sub-slice:** Create Invoice Header (no line items).
2.  **Sub-slice:** Add Line Items (UI only).
3.  **Sub-slice:** Save Invoice + Line Items (Transactional Insert).
    *   *Note:* This is where you test the "Number Sequence" logic.
    *   **Prompt:** "I need a Postgres function to handle the `next_invoice_number`. It should look at the `NumberSequences` table for the user, increment it, and return the formatted string. Write the SQL."

### Summary of the "No-Loopback" Workflow

1.  **The Bible:** `schema.prisma` (Text spec is now deprecated).
2.  **The Context:** When prompting for code, **always** paste the relevant section of `schema.prisma` or `types.ts`. Never assume the AI remembers the table structure.
3.  **The Validator:**
    *   **SQL:** Must run in Supabase without error.
    *   **TS:** Must pass `tsc --noEmit`.
    *   **Logic:** Must pass a simple unit test (e.g., "Create Invoice -> Add Payment -> Check Status is 'Partial'").

By forcing the AI to read the Schema/Types (which are strict) rather than the Spec (which is open to interpretation), you eliminate the "hallucinations" where the AI invents fields or forgets constraints.

---

**User:** Can you expand and give more guidelines for how to 'slice' up the generation workflow? Maybe the logical 'cleavage' lines where i need to (as a human) focus at each step? You can contextualize your guidance to the application stack so outlined (fastify/supabase/svelte/astro/cloudflare) as that is a stack I want to specialize in.

**Assistant:** This is a critical strategic shift. Most AI-assisted projects fail because the human tries to build "The Frontend" then "The Backend." That is horizontal slicing.

For your stack (Fastify/Supabase/Svelte/Astro), you must use **Vertical Dependency Slicing**. You only build a slice when its *data dependencies* already exist in the database.

Here is the "Cleavage Map" for your specific project.

### Slice 0: The "Plumbing" (Human Heavy)
*Before generating features, establish the communication lines.*
*   **Goal:** A "Hello World" where a Svelte component hits a Fastify endpoint, which queries Supabase, and returns data.
*   **Human Focus:**
    *   **Auth Context:** Ensure Fastify can decode the Supabase JWT to get the `user_id`. This is the #1 failure point. If this isn't rock solid, RLS will fail later.
    *   **Shared Types:** Set up a monorepo structure (or workspace) where your `types.ts` (generated from Prisma/SQL) is visible to both the Fastify folder and the Astro folder.

---

### Slice 1: The "Root" Dependencies (Settings & Clients)
*You cannot create an invoice without a Client. You cannot render a PDF without User Settings (Logo/Address).*

**1.1 User Profile & Settings**
*   **AI Task:** Generate SQL for `user_settings` and Svelte forms to edit them.
*   **Human Focus:**
    *   **Image Uploads:** AI struggles with file uploads (Cloudflare R2). You will likely need to hand-code the logic: *Frontend gets presigned URL -> Uploads to R2 -> Saves path to DB.*
    *   **Defaults:** Ensure the "Default Tax Rate" and "Next Invoice Number" logic is seeded correctly.

**1.2 Client Directory**
*   **AI Task:** Standard CRUD. `GET /clients`, `POST /clients`.
*   **Human Focus:**
    *   **Zod Validation:** Ensure the AI generates strict Zod schemas for the Fastify route. (e.g., Email is valid, Name is not empty).
    *   **Svelte Store:** Decide how you handle client state. Do you fetch every time or cache? (Start with fetching every time to keep it simple).

---

### Slice 2: The "Bridge" (Projects)
*Projects connect Clients to Invoices. This is a low-risk slice to test your workflow.*

*   **AI Task:** CRUD for Projects.
*   **Human Focus:**
    *   **Foreign Key Constraints:** Verify that the AI-generated SQL prevents deleting a Client if they have active Projects.
    *   **The "Optional" Logic:** Your spec says Projects are optional. Test that the UI handles a "No Project" state gracefully without crashing.

---

### Slice 3: The "Beast" (Invoices & Quotes)
*This is the hardest slice. It contains 60% of the app's complexity. Do not try to do this in one prompt.*

**3.1 The Data Structure (Header + Lines)**
*   **AI Task:** "Create a Svelte form that allows adding multiple line items. Calculate totals in real-time on the frontend."
*   **Human Focus:**
    *   **Transactional Integrity:** When saving, you are inserting into `Document` AND `LineItems`. Ensure the Fastify handler uses a Supabase transaction (or proper async/await order with error handling) so you don't get "Orphaned Headers" if the line items fail.

**3.2 The Numbering Logic**
*   **AI Task:** "Implement the `getNextInvoiceNumber` function in Postgres."
*   **Human Focus:**
    *   **Concurrency:** What happens if two users hit "Save" at the exact same millisecond? (Postgres sequences handle this, but AI often tries to do `MAX(id) + 1` which is a race condition. **Force the use of a separate sequence table or Postgres Sequence objects.**)

**3.3 Status Logic (The Triggers)**
*   **AI Task:** "Write the Postgres Trigger that updates `Document.total` when `LineItems` change."
*   **Human Focus:**
    *   **Testing:** Manually insert a line item in the DB. Did the Document total update? If not, stop. Fix the trigger.

---

### Slice 4: The "Side Effects" (PDFs & Email)
*Now that data exists, we need to output it. This is pure Fastify/Node work.*

*   **AI Task:** "Create a Fastify service that takes an `invoice_id`, fetches the data, and renders a PDF using `pdfmake` or `puppeteer`."
*   **Human Focus:**
    *   **The "Frozen" Copy:** Your spec requires storing the PDF. Ensure the workflow is: *Generate -> Upload to R2 -> Update DB with URL -> Send Email.*
    *   **Templating:** AI is bad at making PDFs look "pretty." Expect to spend human time tweaking the CSS/Layout of the PDF.

---

### Slice 5: The "Mutators" (Payments & Expenses)
*These modify the state of the Invoices.*

**5.1 Payments**
*   **AI Task:** "Create a modal to add a payment. Update the `Payments` table."
*   **Human Focus:**
    *   **The Trigger Check:** You defined logic: *Sum of payments determines Invoice Status.* Verify the DB trigger you wrote in Phase 2 actually fires. Does adding a $500 payment to a $1000 invoice change status to `Partial`?

**5.2 Expenses**
*   **AI Task:** CRUD for Expenses.
*   **Human Focus:**
    *   **The "Billable" Workflow:** This is complex logic. "Select unbilled expenses -> Add to Invoice."
    *   **Cleavage Line:** Treat "Adding Expense to Invoice" as a separate mini-project. It involves reading expenses, cloning them into line items, and updating the expense status to `billed`.

---

### Slice 6: The "View Layer" (Dashboard & Reports)
*Do this last. It is easy, and it is rewarding.*

*   **AI Task:** "Write a SQL query to aggregate revenue by month. Create a Chart.js component in Svelte."
*   **Human Focus:**
    *   **Performance:** Ensure the AI writes efficient SQL (using `SUM` and `GROUP BY` in the DB) rather than fetching 10,000 rows and summing them in JavaScript.

---

### Summary: Where to look for "Drift"

In your specific stack, here is where the AI will try to trick you:

1.  **Date Objects:**
    *   *Problem:* Postgres returns ISO strings (`2023-01-01T...`). Svelte expects Date objects. Fastify sends JSON (strings).
    *   *Fix:* In your `types.ts`, define dates as `string` (the wire format) or use a Zod transform to coerce them. Be consistent.

2.  **Supabase Types vs. App Types:**
    *   *Problem:* Supabase generates types based on the DB (snake_case). Your JS code might prefer camelCase.
    *   *Fix:* **Do not fight the database.** Use `snake_case` in your TypeScript interfaces for data objects. It saves hours of mapping code.

3.  **RLS vs. API Logic:**
    *   *Problem:* The AI might write a Fastify check: `if (invoice.user_id === currentUser)`.
    *   *Fix:* This is redundant if RLS is on, but good for defense-in-depth. However, if the AI *forgets* the RLS policy in SQL, the app is insecure. **Always audit the SQL file manually.**

**The Golden Rule:**
Never move to the next slice until the **Types** (TS) and the **Schema** (DB) of the current slice are perfectly aligned and the "Happy Path" works in the browser.

---

**User:** Should I trust an AI to make the slicing recommendations for a more specific project (given the initial spec like I have here)? What would be the best way to prompt for this? Any other general ideas and concepts I need to learn to ensure success?

**Assistant:** ### Should you trust the AI to slice the project?

**Short Answer:** Trust it to **map dependencies**, but do not trust it to **schedule complexity**.

AI is excellent at graph theory (knowing that *Table B* requires *Table A*). It is terrible at estimating friction. It will casually say "Step 3: Implement OAuth and PDF rendering" as if that takes the same effort as "Step 4: Add a button."

**The Strategy:** Use the AI to generate the **Dependency Graph**, then you (the Human) flatten that graph into a linear **Execution List** based on what you want to tackle first.

### How to Prompt for the Perfect Slice

To get a usable roadmap, you must force the AI to think in terms of **Data Dependencies** and **Testability**, not just "features."

**The Prompt:**

> "Act as a Senior Technical Lead. I have a full project specification (attached) and a strict tech stack (Fastify, Supabase, Svelte, Astro).
>
> I need you to break this project down into **Vertical Development Slices**.
>
> **Rules for Slicing:**
> 1. **Dependency Order:** No slice can be built unless its database dependencies exist in a previous slice.
> 2. **Testability:** Each slice must result in a verifiable, working feature (e.g., 'I can save a client to the DB').
> 3. **Granularity:** No slice should take more than 2-4 hours of coding. Break complex features (like Invoicing) into sub-slices (Header, Lines, Calculations).
>
> **Output Format:**
> Return a JSON list where each item contains:
> - `slice_id`: (1.0, 1.1, etc.)
> - `title`: Short name
> - `dependencies`: [list of previous slice_ids]
> - `db_tables`: [tables involved]
> - `complexity`: (Low/Med/High)
> - `verification_step`: One sentence describing how I manually verify this slice works.
>
> Do not write code yet. Just plan the slices."

**The Human Review (The "BS" Check):**
Once the AI generates this list, look for these red flags:
1.  **The "Magic" Step:** If a slice says "Implement Invoicing and Payments" (High complexity), reject it. That is too big. Ask it to split it.
2.  **The Orphan:** If a slice appears early but requires data you haven't built yet (e.g., "Dashboard Reports" appearing before "Invoices"), move it to the end.

---

### General Concepts for Success (The "Meta-Game")

To stop the "Loopback" hell you are experiencing, you need to adopt three specific mental models.

#### 1. "Test-Driven Generation" (TDG)
This is the single most effective way to stop AI hallucinations. Instead of asking the AI to write the code, ask it to write the **Test** first.

*   **The Workflow:**
    1.  **Prompt:** "Write a Playwright (or Vitest) test that visits the `/clients` page, clicks 'Add Client', fills the form, submits, and expects the new client to appear in the list."
    2.  **Review:** Does the test look right? (It's easier to read a test than implementation code).
    3.  **Prompt:** "Now write the Svelte component and Fastify route to make this test pass."
*   **Why it works:** The test acts as a rigid constraint. The AI cannot "drift" because the test defines the exact success criteria.

#### 2. The "Context Budget" & Context Stuffing
You mentioned using RAG. RAG is often "lossy." For code generation, **Context Stuffing** is superior.

*   **The Concept:** LLMs have a finite attention span. If you feed it the whole spec, the SQL schema, the design system, and the last 10 files, it gets confused.
*   **The Fix:** Create "Context Files" for each slice.
    *   When working on **Invoices**, create a temporary text file containing *only* the `Invoice` and `Client` TypeScript interfaces and the specific Spec section for Invoicing.
    *   Paste *that* into the prompt. Do not let the AI guess based on the whole project.

#### 3. Idempotency (The "Reset" Button)
In the early stages, your data model will break. You will realize you forgot a field.
*   **The Concept:** Never manually edit your database.
*   **The Fix:** Maintain a `seed.ts` script.
    *   Every time you finish a slice, update your seed script to generate dummy data for that slice.
    *   When things get weird, run `supabase db reset`.
    *   If you can wipe your DB and rebuild it in 10 seconds, you will never fear "breaking" things, which allows you to iterate faster.

#### 4. The "Interface Wall"
This is specific to your **Fastify <-> Svelte** stack.
*   **The Concept:** The API response is the contract.
*   **The Fix:** Before writing frontend code, ask the AI: *"Generate the JSON response example for `GET /invoices/123`."*
*   **Why:** Once you agree on the JSON shape, you can generate the Frontend and Backend in parallel (or sequentially) without them mismatching. If you skip this, the Backend will send `client_id` and the Frontend will expect `client: { id: ... }` and everything breaks.

### Summary Checklist for your next session:

1.  **Generate the Plan:** Use the prompt above to get your JSON list of slices.
2.  **Freeze the Schema:** Generate your `schema.prisma` (or SQL DDL) and `types.ts`.
3.  **Pick Slice 1:** (Likely "Client Directory").
4.  **Create Context:** Copy *only* the Client-related types and spec into your prompt.
5.  **Generate Test:** "Write a test for creating a client."
6.  **Generate Code:** "Make the test pass."

This feels slower because there is more setup. But it is **monotonic** progress. You never slide backward.

---

**User:** I want to submit the above context to a deep research ai in order to generate a referenced manual that will act as my go to guide for application construction (again its ok to constrain to the application stack we have been discussing). It should have a lot of detail on prompt construction and grounding techniques. The breakdown and slicing seems to be critical as well, and the points of critical human intervention and review. I also need extensive references and further reading recommendations. Can you write me a prompt for this?

**Assistant:** Here is a comprehensive prompt designed for a **Deep Research AI** (like OpenAI o1-pro, ChatGPT with Search, or Perplexity Pro).

This prompt is structured to force the AI to synthesize the specific architectural discussions we have had into a formal, actionable manual.

***

### The Prompt

**Role & Objective:**
Act as a Principal Software Architect and AI Workflow Specialist. Your objective is to generate a comprehensive, referenced **"Field Manual for AI-Assisted Deterministic Development."**

I am building a specific web application (Lightweight Bookkeeping) using a specific stack (Fastify, Supabase/PostgreSQL, Svelte, Astro, Cloudflare). I have been struggling with "Loopbacks"—where AI-generated code drifts from the specification, causing inconsistencies between the Database and the Frontend.

I have established a new workflow hypothesis: **"Schema-First, Vertical Slicing."**

**Input Context:**
1.  **The Project Spec:** [Insert the Bookkeeping Project Spec here]
2.  **The Stack:**
    *   **Database:** Supabase (PostgreSQL + RLS).
    *   **Backend:** Fastify (Node.js).
    *   **Frontend:** Astro (Static/Routing) + Svelte (Interactive Components).
    *   **Infrastructure:** Cloudflare (Hosting/Storage).
    *   **Design Artifact:** Prisma Schema (used as the SSOT, even if not using the Prisma Client runtime).
3.  **The Core Philosophy:**
    *   **Probabilistic vs. Deterministic:** AI is probabilistic; Code is deterministic. We must use AI to generate rigid artifacts (Schemas/Types) first, then force it to code strictly against those artifacts.
    *   **Vertical Slicing:** We do not build "The Backend" then "The Frontend." We build "Feature A" from DB to UI, verify, then move to "Feature B."
    *   **Test-Driven Generation:** We generate tests/validators before implementation code to ground the AI.

**Deliverable Requirements:**
Produce a detailed, step-by-step manual. The tone should be technical, pragmatic, and authoritative. Avoid generic advice.

**Structure of the Manual:**

**Part 1: Theoretical Framework**
*   Explain the "Context Window" problem and why RAG fails for strict syntax generation.
*   Define "Context Stuffing" vs. RAG in the context of coding.
*   Explain the "Schema-First" doctrine: Why the DB schema is the only source of truth.

**Part 2: The Architecture & Stack**
*   Specific guidelines for the Fastify/Supabase/Svelte combination.
*   How to share types (TypeScript interfaces/Zod schemas) between Fastify and Svelte in a monorepo structure to prevent drift.

**Part 3: The Slicing Strategy (The Roadmap)**
*   Analyze the provided Project Spec.
*   Break the project down into a JSON-structured list of **Vertical Slices**.
*   Define the dependencies of each slice.
*   Identify the "Cleavage Lines" (where the human must intervene).

**Part 4: Prompt Engineering & Grounding**
*   Provide a library of **"Meta-Prompts"** for each stage of development:
    *   *Prompt A:* Generating the Prisma Schema from English Specs.
    *   *Prompt B:* Generating SQL/RLS from the Schema.
    *   *Prompt C:* Generating Zod Validators from the Schema.
    *   *Prompt D:* Generating Svelte Components from the Zod Validators.
*   Detail specific **"Grounding Techniques"**: How to inject context (e.g., "Always paste the `types.ts` file into the prompt").

**Part 5: Quality Control & Human Intervention**
*   Create a checklist of **"Stop Points"**—moments where the human MUST review code before proceeding.
*   Define the "BS Check": How to quickly spot AI hallucinations in SQL or TypeScript.

**Part 6: References & Further Reading**
*   Provide annotated references to:
    *   Academic papers or technical articles on "Code Generation with LLMs," "Chain of Thought," and "Context Window Optimization."
    *   Documentation best practices for Supabase RLS and Fastify architecture.
    *   Concepts like "Domain Driven Design" (DDD) applied to AI workflows.

**Execution:**
Use deep research to validate the "Vertical Slicing" and "Test-Driven" approaches. Synthesize the provided project spec into the examples used throughout the manual.

***

### How to use this prompt

1.  **Copy the text above.**
2.  **Insert your Project Spec** where it says `[Insert the Bookkeeping Project Spec here]`.
3.  **Submit** to the strongest reasoning model you have access to (e.g., OpenAI o1, Claude 3.5 Sonnet, or a Deep Research agent).

### What to look for in the output

When the AI returns the manual, check for these specific quality markers:

1.  **The "Meta-Prompts":** Are they generic ("Write me some code") or specific ("Act as a DB Admin, read this schema, generate RLS policies")? You want the latter.
2.  **The Slicing Logic:** Did it correctly identify that **Clients** must be built before **Invoices**? Did it identify that **Settings** (Tax Rates) are a dependency for **Invoices**?
3.  **The References:** It should point you toward concepts like **"Constitutional AI"** (Anthropic's concept of constraining AI behavior), **"Parse-driven generation,"** or **"Type-Chat"** (Microsoft's library for structured AI responses). These are the "real" computer science concepts behind what we are discussing.

---

**User:** Take the deep research generated manual above and create a markdown file. Also take the original conversation, from the beginning of the context until the research prompt and place that in a markdown file as well.