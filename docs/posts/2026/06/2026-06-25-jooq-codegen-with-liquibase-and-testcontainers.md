---
authors:
  - denis
date: 2026-06-25
categories:
  - jOOQ
tags:
  - jooq
  - liquibase
  - testcontainers
  - gradle
---

# Generating jOOQ code from Liquibase migrations with Testcontainers

jOOQ's code generator needs a real database schema to read from. If your schema lives in Liquibase
changelogs, you are usually forced into one of two awkward options: maintain a separate DDL script just
for codegen, or point the generator at a long-running database that someone has to keep migrated. Both
drift away from your migrations sooner or later.

The [jooq-liquibase-testcontainer] library removes that choice. It is a jOOQ `Database` implementation
that spins up a throwaway Testcontainers PostgreSQL instance, applies your Liquibase changelog into it,
and lets the generator read the freshly migrated schema. Your generated classes always match your
migrations, with no extra DDL and no database to keep alive.

<!-- more -->

## The problem

The standard jOOQ Gradle plugin reads metadata straight from a JDBC connection. To generate code you
need a database that already has your tables. When migrations are the source of truth, keeping that
database in sync becomes a chore:

- A handwritten DDL snapshot for codegen rots the moment someone adds a changeset.
- A shared dev database couples your build to external state and to whoever migrated it last.
- Generating against production-like infrastructure is slow and fragile in CI.

What you actually want: take the same Liquibase changelog your application runs, apply it to a clean
database, generate from that, and throw the database away.

## How it works

The library ships a single class, `LiquibasePostgresTcDatabase`, that extends jOOQ's `PostgresDatabase`.
Before jOOQ reads metadata, it runs your Liquibase changelog against the connection the generator already
opened — which, thanks to the Testcontainers JDBC driver, is a disposable PostgreSQL container. Migrations
run once per build, then jOOQ introspects the result as usual.

You get:

- **One source of truth** — codegen reads exactly what your migrations produce.
- **No running database** — Testcontainers starts and stops PostgreSQL for you.
- **Reproducible CI** — every build generates from a clean, fully-migrated schema.

## Usage

It plugs directly into the official [jooq-codegen-gradle] plugin.

### 1. Apply the jOOQ plugin

```kotlin
plugins {
    id("org.jooq.jooq-codegen-gradle")
}
```

### 2. Add the library to the generator classpath

```kotlin
dependencies {
    jooqGenerator("org.dema:jooq-liquibase-testcontainer:x.x.x")
}
```

### 3. Point the generator at a Testcontainers URL and your changelog

```kotlin
jooq {
    configuration {
        logging = org.jooq.meta.jaxb.Logging.DEBUG

        jdbc {
            driver = "org.testcontainers.jdbc.ContainerDatabaseDriver"
            url = "jdbc:tc:postgresql:17.5-alpine:///test-db"
        }

        generator {
            database {
                name = "org.dema.jooq.liquibase.LiquibasePostgresTcDatabase"
                includes = ".*"
                excludes = "databasechangelog|databasechangeloglock"
                inputSchema = "public"
                properties {
                    property {
                        key = "liquibaseChangelogFile"
                        value = "${projectDir}/src/main/resources/liquibase/changelog-master.yml"
                    }
                }
            }
        }
    }
}
```

Three pieces do the work:

- **`jdbc.driver` / `jdbc.url`** — the `jdbc:tc:...` URL tells Testcontainers to launch a PostgreSQL
  container (`17.5-alpine` here) on demand. No host, port, or credentials to manage.
- **`database.name`** — points jOOQ at `LiquibasePostgresTcDatabase` instead of the plain Postgres
  database, so migrations run before introspection.
- **`liquibaseChangelogFile` property** — the absolute path to your changelog master file. The library
  resolves sibling files relative to that directory, so `include` references in your changelog keep
  working.

The `excludes` entry hides Liquibase's own bookkeeping tables (`databasechangelog`,
`databasechangeloglock`) from the generated code.

### 4. Generate

```bash
./gradlew jooqCodegen
```

The first run pulls the PostgreSQL image; subsequent runs reuse it. The container starts, your changelog
is applied, jOOQ generates, and the container is torn down — every time, from the same source of truth as
your application.

## Where it fits

This pairs naturally with a typed jOOQ data layer — see the
[jOOQ repository pattern for Spring Boot](2026-06-22-jooq-repository-pattern-for-spring-boot.md) post for
what to build on top of the generated classes.

[jooq-liquibase-testcontainer]: https://github.com/denis-markushin/common-libs/tree/main/jooq-liquibase-testcontainer
[jooq-codegen-gradle]: https://www.jooq.org/doc/latest/manual/code-generation/codegen-gradle/