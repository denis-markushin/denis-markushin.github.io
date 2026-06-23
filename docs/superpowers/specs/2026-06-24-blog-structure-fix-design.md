# Blog Structure Fix — Design

Date: 2026-06-24
Status: approved (design)

## Problem

The MkDocs blog has no explicit `nav:`; sections are the categories the blog
plugin derives from each post's `categories:` frontmatter. Two classes of
problem exist.

### Taxonomy defects (between sections)

- `Jooq` and `jOOQ` are two category pages for one topic (case-sensitive duplicate).
- `Plugins ` carries a trailing space — a fragile one-post category.
- `GraphQL` and `DGS` overlap inconsistently: one post is GraphQL-only, one
  DGS-only, one both. No single axis.
- Single-post categories (`Testing`, `Openapi`, `Feign`, `Plugins`) are noise,
  not navigation.
- `Kotlin` (6 posts) and `Spring Boot` (5 posts) are too broad to discriminate
  topics.
- Tags mix TitleCase and lowercase across posts — the same duplicate-page defect
  as `Jooq`/`jOOQ`, one axis down.

### Content / SRP defects (the Testing post)

`docs/posts/2025/02/2025-02-23-kotlin-and-spring-boot-testing.md` is a six-tip
grab-bag spanning three responsibilities:

- general testing: `List(n){}`, assertk `prop`, `Int.uuid()` (tips 2–4)
- jOOQ-layer testing: `TestRecordFactory` invoke, `storeRec` (tips 1, 5)
- DGS/GraphQL testing: `DgsClient.buildQuery` typed query (tip 6)

The integration base class `AbstractIntegrationTest` (tip 5) holds both
`dsl: DSLContext` (jOOQ) and `queryExecutor: DgsQueryExecutor` (DGS) — the literal
seam between two layers in one snippet. The DGS test (tip 6) carries no `DGS`/
`GraphQL` category, so it is invisible from the DGS series, and
`implementing-dgs-resolvers` ships zero testing content despite being the natural
home for "how do I test this resolver".

## Decision

Two approved forks:

1. Testing content — **redistribute into existing topic series** (not 3 new posts,
   not taxonomy-only).
2. Category scheme — **topic axis, four categories**; everything finer goes to tags.

## Part 1 — Taxonomy

Each post gets one primary topic category from the fixed set
`{jOOQ, GraphQL & DGS, Testing, Spring Boot}`. `Spring Boot` is the catch-all for
posts with no sharper topic. Finer facets (language, technologies, techniques) go
to `tags`, normalized to `lowercase-kebab`.

| Post | category (now → after) | tags (after) |
|---|---|---|
| spring-data-and-jooq | Kotlin, Jooq → **jOOQ** | jooq, spring-data, kotlin, spring-boot |
| interactive-db-documentation | Plugins␣ → **Spring Boot** | gradle, schemaspy, database, testcontainers |
| dgs-virtual-threads | Kotlin, DGS → **GraphQL & DGS** | dgs, graphql, virtual-threads, spring-security, kotlin |
| feign-openapi | Openapi, Feign, Spring Boot → **Spring Boot** | openapi, feign, spring-boot, kotlin |
| kotlin-spring-testing | Kotlin, Spring Boot, Testing → **Testing** | testing, kotlin, spring-boot, testcontainers, assertk |
| graphql-schema-design | Kotlin, Spring Boot, GraphQL → **GraphQL & DGS** | graphql, dgs, federation, schema-design, kotlin, spring-boot |
| implementing-dgs-resolvers | Kotlin, Spring Boot, GraphQL, DGS → **GraphQL & DGS** | graphql, dgs, dataloader, federation, testing, kotlin, spring-boot |
| jooq-repository-pattern | Kotlin, Spring Boot, jOOQ → **jOOQ** | jooq, postgres, repository, testing, kotlin, spring-boot |

Resulting sections: jOOQ=2, GraphQL & DGS=3, Spring Boot=2, Testing=1. The
duplicate `Jooq`/`jOOQ`, the `Plugins␣` space, the GraphQL/DGS overlap, and the
single-post categories are gone.

## Part 2 — Content redistribution

The only physical move is tip 6 plus the `queryExecutor` field leaving the Testing
post. Everything else is added sections and cross-links — no copy-pasted code.

| Artifact | Home | Action |
|---|---|---|
| Tips 1–4 (factory `invoke`, `List`, assertk `prop`, UUID) | Testing post | stay — general techniques |
| `AbstractIntegrationTest` base class | Testing post | stay as the stack-general scaffold; **remove the `queryExecutor: DgsQueryExecutor` field** (removes the jOOQ+DGS seam) |
| Tip 6 + `queryExecutor` | implementing-dgs-resolvers | new "Testing resolvers" section; link back to the scaffold in the Testing post |
| jOOQ-layer test (factory / `storeRec` against real Postgres) | jooq-repository-pattern | expand the existing trailing link into a real "Testing the repository" section; link to the scaffold |

After this: the base class no longer mixes layers; DGS testing lives in the DGS
series (gap closed); jOOQ testing lives in the jOOQ series; general techniques stay
in Testing. No code duplication — the topic sections link to the scaffold rather
than re-pasting it.

## Cross-links to add or update

All links are relative `.md` paths (validated by `strict: true`).

- Testing post: replace the removed tip-6 section with a pointer to the DGS post's
  "Testing resolvers"; add a pointer to the jOOQ post's "Testing the repository";
  update the conclusion (drop the "type-safe GraphQL operations" claim).
- implementing-dgs-resolvers: "Testing resolvers" section links back to the Testing
  post scaffold.
- jooq-repository-pattern: "Testing the repository" section links back to the
  Testing post scaffold (the post already links to Testing at the end — expand it).

## Verification

- Run `mkdocs build --strict`; it must pass with no warnings (broken relative link
  = strict failure).
- If mkdocs is not installed in the environment, flag it and verify every relative
  link path by hand against the file tree.
- Category/tag renames touch no file paths, so they cannot break links.

## Out of scope

- `docs/posts/2026/06/2026-06-23-kotlin-spring-config-metadata-kdoc.md` — a 9th,
  untracked post created after the analysis. Not covered here. Fold it into the
  scheme only on explicit request.
- No prose rewriting beyond what the moves require.
- No new posts, no `nav:` introduction, no theme changes.

## Risk

- `strict: true` turns any stale relative link into a build failure — the
  verification step is mandatory, not optional.
- The working tree already holds the author's in-progress edits to all eight posts;
  these edits must be preserved — taxonomy and content changes layer on top, they do
  not revert anything.
