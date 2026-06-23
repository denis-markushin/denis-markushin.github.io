---
authors:
  - denis
date:
  created: 2026-06-22
categories:
  - GraphQL & DGS
tags:
  - graphql
  - dgs
  - federation
  - schema-design
  - kotlin
  - spring-boot
---

# GraphQL Schema Design Conventions I Use with DGS and Federation

A consistent GraphQL schema is easier to read, evolve, and compose across a federated graph. Here are the schema-design conventions I apply in every Kotlin/Spring service built on the [Netflix DGS Framework](https://netflix.github.io/dgs/). They are backed by my [`graphql-dgs-starter`](https://github.com/denis-markushin/common-libs), which ships the shared types referenced below.

<!-- more -->

## 1. Split the schema by concern

Keep each concern in its own `.graphql` file. A flat `schema.graphql` becomes a merge-conflict magnet the moment two features land simultaneously.

```text
src/main/resources/schema/
  project-queries.graphql      # queries namespace
  project-mutations.graphql    # mutations namespace + inputs
  comment-api.graphql          # a feature slice
  federated-types.graphqls     # foreign types this service references
```

**Why it matters:**

- **Ownership:** each file has a clear team or domain owner, reducing accidental cross-feature edits.
- **Navigability:** finding a type or mutation is a file-open away, not a scroll through 500 lines.
- **Stable codegen:** adding a feature file does not regenerate unrelated DGS constants.

## 2. A shared `Node` interface

Every domain object implements `Node`, giving every record a globally unique id and audit timestamps. The interface lives in the `graphql-dgs-starter` and is stitched in automatically — you never redeclare it in each service.

```graphql
"Relay-compliant object with a globally unique identifier and audit timestamps."
interface Node {
    "Globally unique identifier of the record."
    id: UUID!
    "Timestamp when the record was created."
    createdAt: LocalDateTime!
    "Timestamp when the record was last updated."
    updatedAt: LocalDateTime!
}

type Project implements Node @key(fields: "id") {
    id: UUID!
    title: String!
    address: String
    dueDate: LocalDateTime
    progressPercent: Int!
    createdAt: LocalDateTime!
    updatedAt: LocalDateTime!
}
```

**Why it matters:**

- **Relay identity:** every object is globally addressable by `id`, which federation routers and client caches expect.
- **Consistent audit fields:** `createdAt`/`updatedAt` land on every type for free — no copy-paste across files.
- **Starter-owned:** the interface is defined once in the shared starter, not duplicated across services.

## 3. Namespaced queries and mutations

Nest all queries behind a namespace type (`ProjectQueries`) instead of dumping everything on the root `Query`. Clients read it as `query.project.byId(...)`, which is self-documenting and keeps the schema root flat.

```graphql
extend type Query {
    project: ProjectQueries!
}

type ProjectQueries {
    "Get a project by id"
    byId(id: UUID!): Project
    "Get all projects (paginated)"
    all(
        first: Int! = 20
        after: String
        sort: ProjectSort! = CREATED_AT_DESC
        filter: ProjectFilter
    ): ProjectConnection
}
```

**Why it matters:**

- **Readable access path:** `query.project.all(...)` signals domain intent without needing to read docs first.
- **No root bloat:** adding ten feature namespaces leaves the root `Query` with ten fields, not a hundred.
- **Singular namespace:** the namespace type is always singular (`ProjectQueries`, not `ProjectsQueries`), matching the resource convention.

## 4. Relay-style pagination

Use cursor-based `Connection`/`Edge`/`PageInfo` types for any list that will grow. Relay pagination composes cleanly with federation and is supported natively in most GraphQL clients.

```graphql
type ProjectConnection {
    pageInfo: PageInfo!
    edges: [ProjectEdge!]!
}

type ProjectEdge {
    cursor: String!
    node: Project
}
```

**Why it matters:**

- **Cursor-based:** stable under concurrent inserts, unlike offset pagination which skips or duplicates rows.
- **Relay standard:** clients and gateways speak `first`/`after`/`pageInfo.hasNextPage` without custom logic.
- **Shared `PageInfo`:** the `pageInfo` type comes from the starter, so its fields are identical across every service.

## 5. Sort enums with a `Sort` suffix

Express sort options as a dedicated enum rather than a raw `String`. This makes all valid orderings discoverable in the schema and maps cleanly onto jOOQ via the `OrderByClausesMapping` provided by the starter.

```graphql
"Sort options"
enum ProjectSort {
    CREATED_AT_DESC
}
```

**Why it matters:**

- **Type-safe:** the client cannot pass an invalid sort string — the schema rejects it before the resolver runs.
- **Predictable naming:** the `Sort` suffix is consistent across all types (`ProjectSort`, `CommentSort`, …).
- **jOOQ integration:** the starter's `OrderByClausesMapping` converts enum values to `SortField` in one line.

## 6. One input type per mutation

Each mutation takes a single named input rather than a flat argument list. This makes the signature stable: you can add optional fields to the input without touching the mutation declaration.

```graphql
input CreateProjectInput {
    "Project id (client-generated for idempotency)"
    id: UUID!
    "Project title"
    title: String!
    "Address"
    address: String!
    "Due date"
    dueDate: LocalDateTime
}
```

**Why it matters:**

- **Backward-compatible evolution:** new optional fields go into the input type without breaking existing callers.
- **Named arguments:** clients pass `input: { ... }` rather than a positional argument list — far clearer in large mutations.
- **Client-generated id:** handing `id` generation to the caller makes every mutation idempotent by default.

## 7. A uniform `MutationResult` contract

All mutations return a type that implements `MutationResult`. The interface enforces a predictable payload shape: the affected record, its id, and an optional typed error instead of relying on the top-level `errors` array.

```graphql
"Common payload contract for mutations returning a single record and an optional typed error."
interface MutationResult {
    "Identifier of the affected record, if available."
    recordId: UUID
    "The affected record, if available."
    record: Node
    "Typed error returned when the mutation fails."
    error: ErrorInterface
}

type CreateProjectResult implements MutationResult {
    recordId: UUID
    record: Project
    status: CommonResultStatus!
    error: ErrorInterface
}
```

**Why it matters:**

- **Uniform contract:** every mutation client has the same shape to handle — `recordId`, `record`, `error`.
- **Typed errors:** clients that select the `error` field get a structured error object, not a freeform string buried in `errors[]`.
- **`record` is a `Node`:** returning the full record avoids a second round-trip to refetch after a write.

## 8. Isolate federated types

Foreign types that this service does not own live in a dedicated `federated-types.graphqls` file. Each foreign type is declared as a stub with only its `@key` field — the owning service fills in the rest at composition time.

```graphql
# federated-types.graphqls — foreign types this service only references
type User @key(fields: "id") {
    id: UUID!
}

type LegalEntity @key(fields: "id") {
    id: UUID!
}
```

```graphql
# in another service that OWNS User — it extends the type with its own fields
extend type User {
    "Signing tasks assigned to me"
    signingTasks(status: SignerTaskStatus): [SignerTask!]!
}
```

**Why it matters:**

- **Clear ownership:** every field belongs to exactly one service; the stub makes cross-service boundaries explicit.
- **Gateway composition:** the router merges stubs with the owning service's definition — no manual coordination needed.
- **Isolated change surface:** a change to `User` in its owning service does not require touching this service's schema.

---

These eight conventions keep schemas readable on day one and evolvable on day two hundred. The [`graphql-dgs-starter`](https://github.com/denis-markushin/common-libs) ships `Node`, `MutationResult`, `PageInfo`, and the `OrderByClausesMapping` so you get the shared vocabulary without copy-paste.

In the next post I show how these schema conventions are implemented in DGS resolvers — namespace fetchers, entity fetchers, batch loaders, and typed mutation handling: [Implementing DGS Resolvers](2026-06-22-implementing-dgs-resolvers.md).
