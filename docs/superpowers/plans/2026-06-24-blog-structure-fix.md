# Blog Structure Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Normalize the MkDocs blog's category/tag taxonomy and move layer-specific testing content out of the grab-bag Testing post into the jOOQ and DGS series.

**Architecture:** The blog has no explicit `nav:`; sections are the categories the `blog` plugin derives from each post's `categories:` frontmatter. The fix is two-fold: (1) rewrite `categories:`/`tags:` in all 8 posts to a four-category topic axis; (2) add a "Testing" section to the jOOQ and DGS posts, then strip the DGS test (and the `DgsQueryExecutor` field) out of the Testing post and replace it with cross-links. The regression guard is `mkdocs build --strict`.

**Tech Stack:** MkDocs + Material theme, `mkdocs-material` blog plugin, Python. `strict: true` in `mkdocs.yml` (line 98) turns any broken relative link into a build failure.

---

## Before you start — working-tree note

All 8 target posts already carry **uncommitted in-progress edits** from the author's working session (`git status` shows them as `M`/`AM`). The commits in this plan will include those pre-existing edits, because they live in the same files. If you want the author's edits committed separately, commit them first before running Task 1. Do **not** revert or discard any existing change — every edit here layers on top.

There is also a 9th untracked post, `docs/posts/2026/06/2026-06-23-kotlin-spring-config-metadata-kdoc.md`, which is **out of scope** — do not touch it.

---

## Task 0: Baseline — confirm the build is green before changes

**Files:** none (verification only)

- [ ] **Step 1: Confirm mkdocs is available**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs --version`
Expected: prints a version (e.g. `mkdocs, version 1.6.x`).
If it fails with "command not found", run `pip install -r requirements.txt` first, then retry. If still unavailable, STOP and report — every later verification depends on it. As a fallback, verify relative-link targets by hand against the file tree.

- [ ] **Step 2: Run the strict build on the current tree**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs build --strict 2>&1 | tail -20`
Expected: `INFO - Documentation built in ...` with **no** `WARNING`/`ERROR`. 
If it already fails on the unchanged tree, note the exact warning — it is pre-existing, not caused by this plan. Proceed only once you know the baseline state.

---

## Task 1: Normalize taxonomy in all 8 posts

Rewrite the `categories:` and `tags:` blocks. Categories use the fixed set `{jOOQ, GraphQL & DGS, Testing, Spring Boot}`; tags are `lowercase-kebab`. Each Edit is an exact-match replacement of the frontmatter block.

**Files:**
- Modify: `docs/posts/2024/10/2024-10-01-how-to-integrate-spring-data-and-jooq.md`
- Modify: `docs/posts/2024/10/2024-10-10-how-to-generate-interactive-database-documentation.md`
- Modify: `docs/posts/2024/12/2024-12-11-hot-use-dgs-virtual-threads-and-spring-security.md`
- Modify: `docs/posts/2025/02/2025-02-03-integration-feign-clients-and-openapi-generator.md`
- Modify: `docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md`
- Modify: `docs/posts/2026/06/2026-06-22-graphql-schema-design-conventions-with-dgs.md`
- Modify: `docs/posts/2026/06/2026-06-22-implementing-dgs-resolvers.md`
- Modify: `docs/posts/2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md`

- [ ] **Step 1: Edit post 1 — spring-data-and-jooq**

In `docs/posts/2024/10/2024-10-01-how-to-integrate-spring-data-and-jooq.md`, replace:

```yaml
categories:
  - Kotlin
  - Jooq
tags:
  - Kotlin
  - Jooq
```

with:

```yaml
categories:
  - jOOQ
tags:
  - jooq
  - spring-data
  - kotlin
  - spring-boot
```

- [ ] **Step 2: Edit post 2 — interactive-db-documentation**

In `docs/posts/2024/10/2024-10-10-how-to-generate-interactive-database-documentation.md`, replace (note the trailing space after `Plugins`):

```yaml
categories:
  - Plugins 
tags:
  - Gradle
  - SchemaSpy
  - Database
  - Testcontainers
```

with:

```yaml
categories:
  - Spring Boot
tags:
  - gradle
  - schemaspy
  - database
  - testcontainers
```

- [ ] **Step 3: Edit post 3 — dgs-virtual-threads**

In `docs/posts/2024/12/2024-12-11-hot-use-dgs-virtual-threads-and-spring-security.md`, replace:

```yaml
categories:
  - Kotlin
  - DGS
tags:
  - Kotlin
  - DGS
```

with:

```yaml
categories:
  - GraphQL & DGS
tags:
  - dgs
  - graphql
  - virtual-threads
  - spring-security
  - kotlin
```

- [ ] **Step 4: Edit post 4 — feign-openapi**

In `docs/posts/2025/02/2025-02-03-integration-feign-clients-and-openapi-generator.md`, replace:

```yaml
categories:
  - Openapi
  - Feign
  - Spring Boot
tags:
  - openapi
  - feign
  - spring-boot
```

with:

```yaml
categories:
  - Spring Boot
tags:
  - openapi
  - feign
  - spring-boot
  - kotlin
```

- [ ] **Step 5: Edit post 5 — kotlin-spring-testing**

In `docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md`, replace:

```yaml
categories:
  - Kotlin
  - Spring Boot
  - Testing
tags:
  - kotlin
  - spring-boot
  - testing
```

with:

```yaml
categories:
  - Testing
tags:
  - testing
  - kotlin
  - spring-boot
  - testcontainers
  - assertk
```

- [ ] **Step 6: Edit post 6 — graphql-schema-design**

In `docs/posts/2026/06/2026-06-22-graphql-schema-design-conventions-with-dgs.md`, replace:

```yaml
categories:
  - Kotlin
  - Spring Boot
  - GraphQL
tags:
  - kotlin
  - spring-boot
  - graphql
  - dgs
  - federation
```

with:

```yaml
categories:
  - GraphQL & DGS
tags:
  - graphql
  - dgs
  - federation
  - schema-design
  - kotlin
  - spring-boot
```

- [ ] **Step 7: Edit post 7 — implementing-dgs-resolvers**

In `docs/posts/2026/06/2026-06-22-implementing-dgs-resolvers.md`, replace:

```yaml
categories:
  - Kotlin
  - Spring Boot
  - GraphQL
  - DGS
tags:
  - kotlin
  - spring-boot
  - graphql
  - dgs
  - dataloader
```

with:

```yaml
categories:
  - GraphQL & DGS
tags:
  - graphql
  - dgs
  - dataloader
  - federation
  - testing
  - kotlin
  - spring-boot
```

- [ ] **Step 8: Edit post 8 — jooq-repository-pattern**

In `docs/posts/2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md`, replace:

```yaml
categories:
  - Kotlin
  - Spring Boot
  - jOOQ
tags:
  - kotlin
  - spring-boot
  - jooq
  - postgres
```

with:

```yaml
categories:
  - jOOQ
tags:
  - jooq
  - postgres
  - repository
  - testing
  - kotlin
  - spring-boot
```

- [ ] **Step 9: Verify no stray old category strings remain**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -rn -E "^\s+- (Kotlin|Jooq|Plugins|Openapi|Feign|GraphQL|DGS)\s*$" docs/posts --include=*.md`
Expected: **no output** (every old category string is gone). If any line prints, fix that post's frontmatter.

- [ ] **Step 10: Run the strict build**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs build --strict 2>&1 | tail -20`
Expected: builds with no WARNING/ERROR (matches the Task 0 baseline).

- [ ] **Step 11: Commit**

```bash
cd "C:/projects/github/denis-markushin/denis-markushin.github.io"
git add docs/posts
git commit -m "chore: normalize blog categories to a four-topic axis and lowercase tags"
```

---

## Task 2: Add a "Testing the repository layer" section to the jOOQ post

This creates the link target the Testing post will point to later. The example reuses `CommentRepo.commenterIdsOf` (defined in section 2 of the same post) and the `storeRec` helper from the Testing post's base class.

**Files:**
- Modify: `docs/posts/2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md`

- [ ] **Step 1: Insert the new section before "## Wrapping up"**

Replace:

```markdown
- **No forgotten updates:** it is impossible to call `store()` and accidentally leave `updated_at` stale.

## Wrapping up
```

with the following (note: the inserted block is markdown that itself contains a kotlin fence):

````md
- **No forgotten updates:** it is impossible to call `store()` and accidentally leave `updated_at` stale.

## 7. Testing the repository layer

Repositories are tested against a real Postgres instance, never a mock or H2. I run them on the shared `AbstractIntegrationTest` Testcontainers base from [Level Up Your Kotlin and Spring Boot Testing](../../2025/02/2025-02-23-kotlin-and-spring-boot-testing.md#5-integration-tests-on-a-testcontainers-base-class), which truncates tables before each test and exposes `storeRec()` to persist any jOOQ record:

```kotlin
@Test
fun `commenterIdsOf returns the distinct authors of a work item`() {
    val workItem = TestWorkItemsRecord().storeRec()
    val author = UUID.randomUUID()
    repeat(2) {
        CommentsRecord().apply {
            id = UUID.randomUUID()
            workItemId = workItem.id
            authorId = author
            text = "c$it"
        }.storeRec()
    }

    val authors = commentRepo.commenterIdsOf(workItem.id)

    assertThat(authors).containsExactly(author)
}
```

**Why it matters:**

- **Real SQL, real types:** the query runs against actual Postgres, so a wrong column or cast fails the test, not production.
- **No `DSLContext` in the test:** the repository is the unit under test; `storeRec` from the base seeds rows without touching `dsl` directly.
- **Deterministic:** `TRUNCATE ... CASCADE` before each test (from the base) means no cross-test bleed.

## Wrapping up
````

- [ ] **Step 2: Update the trailing testing reference in "Wrapping up"**

Replace:

```markdown
If you are coming from Spring Data JPA, the earlier post [How to Integrate Spring Data and jOOQ](../../2024/10/2024-10-01-how-to-integrate-spring-data-and-jooq.md) covers how jOOQ fits into a Spring Boot project alongside (or instead of) Spring Data. For testing the repository layer against a real database, the patterns in [Level Up Your Kotlin and Spring Boot Testing](../../2025/02/2025-02-23-kotlin-and-spring-boot-testing.md) apply directly.
```

with:

```markdown
If you are coming from Spring Data JPA, the earlier post [How to Integrate Spring Data and jOOQ](../../2024/10/2024-10-01-how-to-integrate-spring-data-and-jooq.md) covers how jOOQ fits into a Spring Boot project alongside (or instead of) Spring Data. For testing this repository layer against a real database, see [section 7 above](#7-testing-the-repository-layer), which builds on [Level Up Your Kotlin and Spring Boot Testing](../../2025/02/2025-02-23-kotlin-and-spring-boot-testing.md).
```

- [ ] **Step 3: Verify the section landed**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -n "## 7. Testing the repository layer" docs/posts/2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md`
Expected: one match.

- [ ] **Step 4: Run the strict build**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs build --strict 2>&1 | tail -20`
Expected: no WARNING/ERROR.

- [ ] **Step 5: Commit**

```bash
cd "C:/projects/github/denis-markushin/denis-markushin.github.io"
git add docs/posts/2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md
git commit -m "docs: add a testing-the-repository section to the jOOQ post"
```

---

## Task 3: Add a "Testing resolvers" section to the DGS post

This creates the second link target. It carries the DGS test moved out of the Testing post (the `DgsQueryExecutor` typed-query example) plus the `queryExecutor` field that does not belong in the general base class.

**Files:**
- Modify: `docs/posts/2026/06/2026-06-22-implementing-dgs-resolvers.md`

- [ ] **Step 1: Insert the new section before the closing `---`**

Replace:

```markdown
- The Security context caveat is easy to miss — handle it once in infrastructure, not per resolver.

---
```

with the following (the inserted block is markdown containing two kotlin fences):

````md
- The Security context caveat is easy to miss — handle it once in infrastructure, not per resolver.

## 6. Testing resolvers

Resolvers are worth an integration test that drives the whole path: HTTP-less GraphQL execution against a real database. I run these on the shared `AbstractIntegrationTest` Testcontainers base from [Level Up Your Kotlin and Spring Boot Testing](../../2025/02/2025-02-23-kotlin-and-spring-boot-testing.md#5-integration-tests-on-a-testcontainers-base-class), extended with a `DgsQueryExecutor`:

```kotlin
@Autowired
protected lateinit var queryExecutor: DgsQueryExecutor
```

Build the query with the DGS code-generated client instead of a raw string, execute it, and extract a typed result with `assertk` on the outcome:

```kotlin
@Test
fun `byWorkItem returns comments of the work item`() {
    val project = TestProjectsRecord().storeRec()
    val workItem = TestWorkItemsRecord(projectId = project.id).storeRec()
    repeat(3) {
        CommentsRecord().apply {
            id = UUID.randomUUID()
            workItemId = workItem.id
            authorId = UUID.randomUUID()
            text = "c$it"
            createdAt = LocalDateTime.now().minusSeconds(it.toLong())
            updatedAt = LocalDateTime.now()
        }.storeRec()
    }

    val query = DgsClient.buildQuery(gqlSerializer) {
        comment {
            byWorkItem(workItemId = workItem.id, first = 10, sort = CommentSort.CREATED_AT_DESC) {
                edges { node { id; text } }
            }
        }
    }

    val nodes = queryExecutor.executeAndExtractJsonPathAsObject(
        query, "data.comment.byWorkItem.edges[*].node",
        object : TypeRef<List<Comment>>() {},
    )

    assertThat(nodes).hasSize(3)
}
```

**Why it matters:**

- **No stringly-typed queries:** the codegen client catches typos and schema drift at compile time.
- **Typed extraction:** `executeAndExtractJsonPathAsObject` with a `TypeRef` returns real domain types, not raw maps.
- **Real execution path:** the test drives the actual resolver, data loaders, and SQL — exactly what runs in production.

---
````

- [ ] **Step 2: Update the closing summary to mention testing**

Replace:

```markdown
These five patterns — namespace resolvers, entity fetchers, batch loaders, typed mutation outcomes, and virtual threads — cover the implementation side of the schema conventions described in the companion post. For the schema conventions that drive these resolver shapes, see [GraphQL Schema Design Conventions I Use with DGS and Federation](2026-06-22-graphql-schema-design-conventions-with-dgs.md).
```

with:

```markdown
These patterns — namespace resolvers, entity fetchers, batch loaders, typed mutation outcomes, virtual threads, and an integration test that drives the whole stack — cover the implementation side of the schema conventions described in the companion post. For the schema conventions that drive these resolver shapes, see [GraphQL Schema Design Conventions I Use with DGS and Federation](2026-06-22-graphql-schema-design-conventions-with-dgs.md).
```

- [ ] **Step 3: Verify the section landed**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -n "## 6. Testing resolvers" docs/posts/2026/06/2026-06-22-implementing-dgs-resolvers.md`
Expected: one match.

- [ ] **Step 4: Run the strict build**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs build --strict 2>&1 | tail -20`
Expected: no WARNING/ERROR.

- [ ] **Step 5: Commit**

```bash
cd "C:/projects/github/denis-markushin/denis-markushin.github.io"
git add docs/posts/2026/06/2026-06-22-implementing-dgs-resolvers.md
git commit -m "docs: add a testing-resolvers section to the DGS resolvers post"
```

---

## Task 4: Strip the DGS test from the Testing post and cross-link

Now that both link targets exist, remove the `DgsQueryExecutor` field from the base class (the jOOQ+DGS seam), delete the type-safe-GraphQL tip, replace it with pointers to the two topic sections, and reword the conclusion.

**Files:**
- Modify: `docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md`

- [ ] **Step 1: Remove the `queryExecutor` field from `AbstractIntegrationTest`**

Replace:

```kotlin
    @Autowired
    protected lateinit var dsl: DSLContext

    @Autowired
    protected lateinit var queryExecutor: DgsQueryExecutor

    @BeforeEach
```

with:

```kotlin
    @Autowired
    protected lateinit var dsl: DSLContext

    @BeforeEach
```

- [ ] **Step 2: Replace the entire tip-6 section with cross-links**

Replace the whole block (from the section heading through its last bullet, immediately before `## Conclusion`):

````md
## 6. Type-Safe GraphQL Operations in Tests

Build GraphQL queries with the DGS code-generated client instead of raw strings, then extract a typed result
and assert with `assertk`.

```kotlin
@Test
fun `byWorkItem returns comments of the work item`() {
    val project = TestProjectsRecord().storeRec()
    val workItem = TestWorkItemsRecord(projectId = project.id).storeRec()
    repeat(3) {
        CommentsRecord().apply {
            id = UUID.randomUUID()
            workItemId = workItem.id
            authorId = UUID.randomUUID()
            text = "c$it"
            createdAt = LocalDateTime.now().minusSeconds(it.toLong())
            updatedAt = LocalDateTime.now()
        }.storeRec()
    }

    val query = DgsClient.buildQuery(gqlSerializer) {
        comment {
            byWorkItem(workItemId = workItem.id, first = 10, sort = CommentSort.CREATED_AT_DESC) {
                edges { node { id; text } }
            }
        }
    }

    val nodes = queryExecutor.executeAndExtractJsonPathAsObject(
        query, "data.comment.byWorkItem.edges[*].node",
        object : TypeRef<List<Comment>>() {},
    )

    assertThat(nodes).hasSize(3)
}
```

**Why it's useful:**

* **No stringly-typed queries:** the codegen client catches typos and schema drift at compile time.
* **Typed extraction:** `executeAndExtractJsonPathAsObject` with a `TypeRef` returns real domain types.
* **Readable assertions:** `assertk` keeps the check expressive — pair it with the factory pattern from tip #1.
````

with:

````md
## 6. Where DGS and jOOQ test setups live

These techniques are framework-agnostic. The layer-specific test setups build on the `AbstractIntegrationTest` base above and live with their topic:

* **Testing DGS resolvers** — typed GraphQL queries via `DgsQueryExecutor` and the code-generated client: see [Implementing DGS Resolvers → Testing resolvers](../../2026/06/2026-06-22-implementing-dgs-resolvers.md#6-testing-resolvers).
* **Testing the jOOQ repository layer** — record factories and `storeRec` against real Postgres: see [A jOOQ Repository Pattern → Testing the repository layer](../../2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md#7-testing-the-repository-layer).
````

- [ ] **Step 3: Reword the conclusion**

Replace:

```markdown
By combining these techniques — from record factories to a shared Testcontainers base class and type-safe GraphQL operations — you'll streamline both unit and integration test setups, reduce boilerplate, and keep your focus on writing meaningful test logic. Happy testing!
```

with:

```markdown
By combining these techniques — from record factories to a shared Testcontainers base class — you'll streamline both unit and integration test setups, reduce boilerplate, and keep your focus on writing meaningful test logic. The layer-specific setups (DGS resolvers, jOOQ repositories) build on the same base; follow the links above when you need them. Happy testing!
```

- [ ] **Step 4: Verify the DGS test and field are gone, and the cross-links are present**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -nc -E "DgsQueryExecutor|DgsClient\.buildQuery" docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md`
Expected: `0` (no DGS execution code remains in the Testing post).

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -n "Where DGS and jOOQ test setups live" docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md`
Expected: one match.

- [ ] **Step 5: Run the strict build**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs build --strict 2>&1 | tail -20`
Expected: no WARNING/ERROR.

- [ ] **Step 6: Commit**

```bash
cd "C:/projects/github/denis-markushin/denis-markushin.github.io"
git add docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md
git commit -m "docs: move DGS test out of the Testing post and cross-link to topic sections"
```

---

## Task 5: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Full strict build**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && mkdocs build --strict 2>&1 | tail -30`
Expected: `Documentation built in ...`, no WARNING/ERROR.

- [ ] **Step 2: Confirm the anchor targets exist for the two cross-links**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -n -E "## 6\. Testing resolvers|## 7\. Testing the repository layer|## 5\. Integration Tests on a Testcontainers Base Class" docs/posts/2026/06/2026-06-22-implementing-dgs-resolvers.md docs/posts/2026/06/2026-06-22-jooq-repository-pattern-for-spring-boot.md docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md`
Expected: three matches — the headings that the new cross-links point at (`#6-testing-resolvers`, `#7-testing-the-repository-layer`, `#5-integration-tests-on-a-testcontainers-base-class`).

- [ ] **Step 3: Confirm category inventory is the intended four**

Run: `cd "C:/projects/github/denis-markushin/denis-markushin.github.io" && grep -rhA1 "^categories:" docs/posts --include=*.md | grep -E "^\s+- " | sort | uniq -c`
Expected: only `jOOQ`, `GraphQL & DGS`, `Testing`, `Spring Boot` appear (counts: jOOQ=2, GraphQL & DGS=3, Spring Boot=2, Testing=1).

- [ ] **Step 4: Report**

Summarize: build status, final category counts, and the three commits made (Tasks 1, 2, 3, 4). Note that the 9th untracked post was left untouched.
