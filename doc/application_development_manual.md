# Comprehensive Application Development Manual: A Schema-First, Vertical Slicing Approach

This manual outlines a modern, robust methodology for developing full-stack applications using AI assistance. The core doctrine is **Schema-First, Vertical Slicing**, a philosophy designed to combat the "loopback" problem where inconsistencies arise between database schemas and application code. This guide provides the theoretical foundation, practical architecture, and operational workflows to build deterministically correct software with the aid of large reasoning models.

## Part 1: Theoretical Framework

### The Challenge of Probabilistic AI in Deterministic Domains

The integration of Large Language Models (LLMs) into software development presents a fundamental mismatch: AI is inherently probabilistic, trained to predict the next word or token, while software development is a deterministic discipline where syntax, types, and logic must be exact. Relying on Retrieval-Augmented Generation (RAG) to find "relevant" code snippets or documentation is flawed because relevance does not equate to correctness in a formal system [[Trustworthy Generative AI — Be...](https://developers.liveperson.com/trustworthy-generative-ai-prompt-library-best-practices.html)]. An AI might retrieve a function that matches keywords in a prompt but fails to adhere to the precise API contract or business rules, leading to subtle, hard-to-debug errors.

### The Schema-First Doctrine as a Single Source of Truth

To resolve this, the "Schema-First" doctrine establishes a rigid, formal schema as the Single Source of Truth (SSOT) for the entire application. Instead of relying on natural language specifications or fragmented RAG results, a machine-readable schema file (e.g., Prisma's `schema.prisma`) is treated as the master artifact [[TypeScript ORM for SQL Databas...](https://www.prisma.io/typescript)]. This schema is a formal specification of the data model, relationships, constraints, and types. The core argument is that **no code generation should occur from English prose alone**. Any implementation drift between the database and the application code is a catastrophic failure, and the only way to prevent it is to generate code directly from the SSOT.

### Context Stuffing: The Correct Integration Pattern

The solution to the RAG problem is **Context Stuffing**. This technique involves directly injecting the exact content of the SSOT schema, along with other key artifacts like generated TypeScript types, into the AI's prompt context. By doing so, the AI is no longer guessing or retrieving; it is grounded in the literal truth of the system's definition. For example, a prompt to generate a backend route must include the relevant Prisma schema model and the generated TypeScript interface. This transforms the AI's task from one of knowledge retrieval to one of precise code composition, dramatically increasing the accuracy and reliability of its output.

## Part 2: Architecture & Stack Specifications

### Full-Stack Technology Stack

The target architecture is a modern, serverless-friendly stack designed for a lightweight bookkeeping application:
*   **Backend:** [Fastify](https://www.fastify.io/), a high-performance, low-overhead web framework for Node.js.
*   **Database:** [Supabase](https://supabase.com/), providing a hosted PostgreSQL database with Row Level Security (RLS) for fine-grained access control.
*   **Frontend Components:** [Svelte](https://svelte.dev/), a compiler-based JavaScript framework for building reactive UIs.
*   **Routing and SSR:** [Astro](https://astro.build/), a build tool for server-side rendering and hybrid static sites.
*   **Hosting:** [Cloudflare](https://www.cloudflare.com/), for edge computing and storage.

### Fastify and Supabase/PostgreSQL Integration

To integrate Fastify with PostgreSQL, the core plugin `@fastify/postgres` is used [[Core Plugins](https://fastify.io/ecosystem/)]. This plugin allows the creation of a shared, configurable connection pool that can be accessed by any part of the backend server, ensuring efficient database connections. The connection string is derived from the Supabase-provided `DATABASE_URL` environment variable.

To securely integrate with Supabase's RLS, the authenticating bearer token (typically from a Supabase client session) must be passed from the frontend to the Fastify backend. The backend then uses this token to establish a database connection with the correct user context, ensuring all RLS policies are enforced. This pattern locks every database operation to a single user via a `user_id`, enabling natural single-tenancy.

### Type Sharing Between Prisma, Svelte, and Astro

The lynchpin of this architecture is **automatic type generation** from the Prisma schema. The `prisma generate` command processes the `schema.prisma` file and produces TypeScript types for all database models (e.g., `User`, `Transaction`) within the `@prisma/client` package or a custom output directory [[Type safety | Prisma Documenta...](https://www.prisma.io/docs/orm/prisma-client/type-safety)].

1.  After defining or updating the schema, run `npx prisma generate`.
2.  The generated types can be imported directly into any TypeScript file, including Fastify route handlers or Svelte component scripts.
3.  For a monorepo structure, these types can be published to a private npm package to be shared seamlessly between a backend (Fastify) and a frontend (Svelte/Astro) that might be in separate codebases but share the same database model [[Sharing Prisma Between Multipl...](https://medium.com/@nolawnchairs/sharing-prisma-between-multiple-applications-5c7a7d131519)].

A central Prisma client instance is created in a `src/lib/prisma.ts` file on the backend, managing the connection lifecycle and adapter configuration (e.g., `@prisma/adapter-pg` for PostgreSQL) [[How to use Prisma ORM and Pris...](https://www.prisma.io/docs/guides/astro)].

## Part 3: Slicing Strategy

### Vertical Slicing for Feature Development

Feature development follows the **Vertical Slice Architecture**, a design principle advocated by Jimmy Bogard [[Vertical Slice Architecture](https://www.jimmybogard.com/vertical-slice-architecture/)]. Instead of building the application horizontally by layer (e.g., complete all database models, then all API routes, then all UI components), the team builds vertically by feature.

A "vertical slice" encapsulates all the code required for a single, end-to-end user-facing feature, from the database query to the user interface component and the connecting API route. This means for the "Expense Manager" feature, all related changes (a new database model, a new API endpoint in Fastify, a new Svelte component for the form, and a new page in Astro) are developed, tested, and deployed together as one unit.

The primary benefit is a significant reduction in complexity and cognitive load. Each slice is a self-contained unit of work, minimizing coupling with other features [[Vertical Slice Architecture](https://www.jimmybogard.com/vertical-slice-architecture/)]. This makes the codebase easier to understand, change, and test.

### Order of Implementation and Dependencies

The six core modules of the bookkeeping application should be implemented in a prioritized order based on their dependencies:

1.  **Client Directory**: Establishes core `Client` data.
2.  **Project Management**: Depends on `Client`, adding a `Project` model with a relation to `Client`.
3.  **Expense Manager**: Depends on `Project`, allowing expenses to be logged against a specific project.
4.  **Transaction Hub**: The central ledger, relates directly to `Client` and possibly `Project`.
5.  **Dashboard**: Pulls data from `Transaction Hub`, `Expense Manager`, and `Project Management` for summary views, so it depends on all four.
6.  **Reporting**: Generates insights from all data sources, making it the most dependent module.

Within each slice, the workflow is **test-driven**. Before writing any logic, a unit test is created to define the expected behavior. This provides an immediate, automated feedback loop to catch AI hallucinations.

## Part 4: Prompt Engineering Library

### Grounded Meta-Prompts for AI-Assisted Development

To ensure the AI generates correct code, a library of "meta-prompts" is used. These prompts are carefully structured to include the exact, unambiguous context needed.

1.  **Schema Injection Prompt**: "Generate a PostgreSQL `CREATE TABLE` statement for the following Prisma model from our SSOT. Ensure all constraints, data types, and relationships are accurately reflected:
    ```prisma
    model Expense {
      id        Int      @id @default(autoincrement())
      projectId Int
      project   Project  @relation(fields: [projectId], references: [id])
      amount    Decimal
      currency  String   @default("USD")
      date      DateTime @default(now())
      notes     String?
    }
    ```"
2.  **Type Specification Prompt**: "Write a TypeScript type guard function that validates an incoming HTTP request body. Use the following generated Prisma type as your true definition:
    ```ts
    import { Prisma } from '@prisma/client';
    type ExpenseCreateInput = Prisma.ExpenseCreateInput;
    ```
    The function should return `true` if the body is a valid `ExpenseCreateInput`, `false` otherwise."
3.  **Example-Driven Prompt**: "Generate a Svelte component that displays a list of `<Transaction>`s. Here is an example of the expected output HTML structure:
    ```html
    <div class="transaction-item">
        <span class="date">2025-12-26</span>
        <span class="description">Consulting Fee</span>
        <span class="amount">$1,000.00</span>
    </div>
    ```
    Use Svelte's `#each` block and bind it to an array of `Transaction` objects."
4.  **Step-by-Step Prompt**: "We are creating the 'Add Expense' feature. Complete this in three steps:
    Step 1: Define the new Prisma schema model for `Expense`.
    Step 2: After the schema is updated and `prisma generate` is run, write the Fastify route POST `/api/expenses` that creates a new expense. Assume a pre-existing `user_id` is available in the request context.
    Step 3: Write the Svelte form component to submit the data to this endpoint."
5.  **Constraint Enforcement Prompt**: "Create the API documentation for the `/api/transactions` endpoint. It must list the `GET` and `POST` methods. For the `POST` request body, **only** include the fields `amount`, `currency`, and `description`. Do not invent additional fields."

## Part 5: Quality Control

### Automated Feedback Loops for Hallucination Detection

The quality control process relies heavily on automated feedback to catch AI-generated errors before human review. This is a compiler-driven development loop.

1.  **Compiler-First Validation**: Every piece of generated code must pass strict TypeScript compilation immediately. Type errors are the first and most effective line of defense against hallucinated function names, property accesses, or incorrect data types [[Modernizing Database Interacti...](https://leapcell.io/blog/modernizing-database-interactions-with-prisma-in-typescript)].
2.  **Linting and Formatting**: Tools like ESLint and Prettier enforce code style and catch common bugs or anti-patterns.
3.  **Test-Driven Generation (TDG)**: For every feature, relevant tests are written first. For backend logic, use Vitest for unit and integration tests. For end-to-end user flows (e.g., can a user add a transaction and see it on the dashboard?), use Playwright. If the generated code fails these pre-written tests, it is rejected.
4.  **Idempotent Seeding**: Database test fixtures and seed data are created using idempotent scripts (e.g., `UPSERT` statements in a `seed.ts` file). This allows the database to be wiped and reset to a known state before every test run, ensuring a clean and consistent environment [[How to use Prisma ORM and Pris...](https://www.prisma.io/docs/guides/astro)]. This process is documented in the Prisma guide for Astro [[How to use Prisma ORM and Pris...](https://www.prisma.io/docs/guides/astro)].

### Human-in-the-Loop for Security and Design

While automation catches syntactic and basic logical errors, human experts are essential for higher-order concerns.
*   **Red-Teaming**: Developers must actively search for vulnerabilities, especially path traversal or injection attacks, that an AI might inadvertently introduce by using unsafe constructs [[What are AI hallucinations and...](https://snyk.io/blog/ai-hallucinations/)]. This is a critical human intervention checkpoint.
*   **Code Reviews**: A final human review ensures the code is maintainable, efficient, and aligns with the overall architectural vision, not just functionally correct.

## Part 6: References & Further Reading

*   Bogard, J. (2018). *Vertical Slice Architecture* [[Vertical Slice Architecture](https://www.jimmybogard.com/vertical-slice-architecture/)].
*   Prisma Documentation. *Type Safety with Prisma Client* [[Type safety | Prisma Documenta...](https://www.prisma.io/docs/orm/prisma-client/type-safety)].
*   Snyk. (2023). *What are AI Hallucinations and Why Should Developers Care?* [[What are AI hallucinations and...](https://snyk.io/blog/ai-hallucinations/)].
*   Fowler, M. *Domain-Driven Design*.
*   Le, T. *How to write better prompts for AI code generation* [[How to write better prompts fo...](https://graphite.com/guides/better-prompts-ai-code)].
*   Rajab, R., et al. (2024). *Schema-first vs. code-first approach in GraphQL API design*. Sage Journals [[Core Plugins](https://fastify.io/ecosystem/)].
*   Syriani, E. *Model-Driven Engineering: A Survey*. IEEE Xplore [[Core Plugins](https://fastify.io/ecosystem/)].