---
authors:
  - denis
date:
  created: 2026-06-22
categories:
  - jOOQ
tags:
  - jooq
  - postgres
  - repository
  - testing
  - kotlin
  - spring-boot
---

# A jOOQ Repository Pattern for Spring Boot

[jOOQ](https://www.jooq.org/) gives you type-safe SQL generated from your real database. Over several services I converged on a small repository pattern that keeps data access typed, testable, and free of leaking `DSLContext`. It builds on my [`jooq-starter`](https://github.com/denis-markushin/common-libs).

<!-- more -->

## 1. Generate jOOQ from Liquibase with Testcontainers

Generate jOOQ classes from your real Postgres schema via Liquibase and Testcontainers, so the generated types always reflect your actual migrations — no schema drift, no manual updates. I packaged the whole setup into a convention plugin, [`io.github.denis-markushin.jooq-codegen`](https://plugins.gradle.org/plugin/io.github.denis-markushin.jooq-codegen):

```kotlin
plugins {
    id("io.github.denis-markushin.jooq-codegen") version "<latest-version>"
}
```

That single line spins up a throwaway PostgreSQL container at codegen time, applies your `src/main/resources/liquibase/changelog-master.yml`, and generates type-safe classes against the resulting schema. It also bakes in a set of opinionated defaults so you never repeat them across services:

- `timestamptz` → `java.time.LocalDateTime` (forced type)
- no POJOs, no DAOs, no `RecordN` — just `Record`s and `DSLContext`
- generated sources land in a dedicated `jooq` source set (`build/generated/sources/jooq`), wired into `main`/`test` and kept out of your hand-written code
- `databasechangelog` / `databasechangeloglock` excluded

Override any default through the `demaJooq` extension — it is deep-merged on top of the defaults, not a replacement:

```kotlin
demaJooq {
    databaseImage = "postgresql:17.5-alpine"
    configuration {
        generator {
            database {
                includes = "custom_.*"
            }
        }
    }
}
```

Under the hood it builds on the official jOOQ Gradle plugin plus my [`jooq-liquibase-testcontainer`](https://github.com/denis-markushin/common-libs) database provider — wire those two directly if you would rather not add a convention plugin.

**Why it matters:**

- **Types from real Postgres:** generated classes reflect the exact column types your database uses, so compile-time errors catch mismatches before runtime.
- **Migrations are the source of truth:** the codegen reads Liquibase changelogs, so renaming a column immediately breaks the build if query code is not updated.
- **One line, opinionated defaults:** the convention plugin removes the repetitive jOOQ codegen config — no schema drift, no hand-maintained mapping classes.

## 2. One repository per table on `AbstractRepository`

Create one repository class per table, extending `AbstractRepository` from the starter. The base class wires up `DSLContext` as a protected `dsl` property and provides common CRUD operations — your subclass only adds the queries specific to that table.

```kotlin
import org.dema.jooq.AbstractRepository
import org.jooq.impl.DSL.noCondition
import org.springframework.stereotype.Component

@Component
class CommentRepo : AbstractRepository<Comments, CommentsRecord>(
    table = COMMENTS,
    baseCondition = noCondition(),
) {
    fun commenterIdsOf(workItemId: UUID): List<UUID> =
        dsl.selectDistinct(COMMENTS.AUTHOR_ID)
            .from(COMMENTS)
            .where(COMMENTS.WORK_ITEM_ID.eq(workItemId))
            .fetch(COMMENTS.AUTHOR_ID)
}
```

**Why it matters:**

- **`protected dsl` not injected:** `DSLContext` stays inside the repository layer — service classes never touch it.
- **Common CRUD included:** `findById`, `store`, `delete` and friends come from the base class, keeping subclasses small.
- **Records only:** returning `*Record` types keeps the API honest and avoids proliferating custom DTO classes for simple queries.

## 3. Bake soft-delete into `baseCondition`

Pass a `baseCondition` to the base class constructor that filters out deleted or archived rows. Every query the base class generates automatically applies this condition, so there is no risk of accidentally exposing stale data.

```kotlin
@Component
class ProjectRepo : AbstractRepository<Projects, ProjectsRecord>(
    table = PROJECTS,
    baseCondition = PROJECTS.DELETED_AT.isNull.and(PROJECTS.ARCHIVED_AT.isNull),
) {
    fun contractorIdOf(projectId: UUID): UUID? =
        dsl.select(PROJECTS.CONTRACTOR_ID)
            .from(PROJECTS)
            .where(PROJECTS.ID.eq(projectId).and(baseCondition))
            .fetchOne(PROJECTS.CONTRACTOR_ID)

    fun getOneByIdIncludingDeleted(id: UUID): ProjectsRecord? =
        dsl.selectFrom(PROJECTS).where(PROJECTS.ID.eq(id)).fetchOne()
}
```

**Why it matters:**

- **Automatic filtering:** every inherited base-class query inherits the condition — soft-deleted rows are invisible by default.
- **Explicit escape hatch:** when you genuinely need deleted rows, you write a dedicated method like `getOneByIdIncludingDeleted` that bypasses `baseCondition`, making the intent obvious.
- **No global filter surprises:** the filter is declared at construction time in one place, not scattered across query sites.

## 4. Custom queries live as repository methods

All SQL for a given table belongs in that table's repository. The `commenterIdsOf` method on `CommentRepo` runs a `SELECT DISTINCT` across comment rows for a work item. The `contractorIdOf` method on `ProjectRepo` does a single-column lookup and returns `null` when the row does not exist. Services call these named methods — they never construct queries themselves. This boundary means you can refactor SQL in one place and the rest of the application does not need to change.

**Why it matters:**

- **Colocation:** queries sit next to the table they operate on, making it easy to audit what SQL a table is involved in.
- **Service layer stays readable:** service methods read like domain operations, not data-access plumbing.
- **Testable in isolation:** repository methods can be tested against a real database without starting a full application context.

## 5. Keep `DSLContext` in the repository layer

Service classes depend on repositories, never on `DSLContext` directly. This keeps the boundary clean: data access is a repository concern, business logic is a service concern.

```kotlin
@Service
class ProjectService(
    private val projectRepo: ProjectRepo,
) {
    fun contractorId(projectId: UUID): UUID? = projectRepo.contractorIdOf(projectId)
}
```

**Why it matters:**

- **Testable services:** you can test `ProjectService` by providing a fake or stub `ProjectRepo` without any database involvement.
- **Clear layering:** grep for `DSLContext` and it only appears inside repository classes — the architecture is self-documenting.
- **Refactor-safe:** changing a query signature only requires updating the repository and its callers, not hunting across service classes for raw SQL.

## 6. Free audit timestamps

The starter ships a `TimestampsRecordListener` that populates `created_at` and `updated_at` automatically on every `store()` call. Enable it with two lines of configuration and never set those fields by hand again.

```yaml
dema:
  jooq:
    timestamps:
      enabled: true
      created-at-column: created_at
      updated-at-column: updated_at
```

**Why it matters:**

- **Zero manual wiring:** timestamps are set consistently on insert and update without any code in your records or services.
- **Configurable column names:** the column names are properties, so renaming a column in a migration is a one-line config change.
- **No forgotten updates:** it is impossible to call `store()` and accidentally leave `updated_at` stale.

## Wrapping up

These six patterns — codegen from real migrations, one repo per table, baked-in soft-delete, SQL colocation, a hard `DSLContext` boundary, and automatic timestamps — give you a data layer that is typed end-to-end, easy to read, and straightforward to test.

If you are coming from Spring Data JPA, the earlier post [How to Integrate Spring Data and jOOQ](../../2024/10/2024-10-01-how-to-integrate-spring-data-and-jooq.md) covers how jOOQ fits into a Spring Boot project alongside (or instead of) Spring Data. For testing the repository layer against a real database, the patterns in [Level Up Your Kotlin and Spring Boot Testing](../../2025/02/2025-02-23-kotlin-and-spring-boot-testing.md) apply directly.
