You are a translator from a CTO JSON spec into a Mermaid system diagram.

Task:
Given the CTO JSON below, produce a single Mermaid `flowchart LR` diagram that shows:
- The client gateway (Node/TypeScript Fastify).
- All services under `services`.
- All datastores under `datastores`.
- All external systems under `external_systems`.
- The relationships defined by `depends_on`.

Rules for nodes:
- Add a `clientGateway` node representing the Fastify client/gateway.
  - Label: `Fastify Client Gateway`.
- For each entry in `services`:
  - Create a node with id `svc_<serviceId>`.
  - Label it with a readable name using title case and "Service" suffix when appropriate.
  - Example: `svc_builder_api[Builder Api Service]`.
- For each entry in `datastores`:
  - Create a node with id `db_<datastoreId>`.
  - Label with the datastore id in title case, plus "DB" or similar.
  - Use database-style node: `db_orders_db[(Orders Db)]`.
- For each entry in `external_systems`:
  - Create a node with id `ext_<externalId>`.
  - Label with `display_name` if present, otherwise a title-cased version of the id.
  - Use double bracket style: `ext_payments_api[[Payments Api]]`.

Rules for edges:
- Draw `clientGateway -->` the primary backend service that exposes the HTTP API (for this system, that is the FastAPI backend, usually something like `builder_api`).
- For each service S and each id D in `services[S].depends_on`:
  - If D is the id of a service: draw `svc_S --> svc_D`.
  - If D is the id of a datastore: draw `svc_S --> db_D`.
  - If D is the id of an external system: draw `svc_S --> ext_D`.
- Do not create edges from datastores or externals back to services unless specified in `depends_on`.

Formatting:
- Use `flowchart LR` as the header.
- Each node and edge on its own line.
- Keep IDs simple (letters, digits, underscores). Do not use spaces in IDs.
- Do not include explanations or comments; output only the Mermaid code, no markdown fences.

Here is the CTO JSON:

<PASTE CTO JSON HERE>
