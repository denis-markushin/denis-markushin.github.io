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
  - dataloader
  - federation
  - testing
  - kotlin
  - spring-boot
---

# Implementing DGS Resolvers: Namespaces, Entity Fetchers, Batch Loaders and Typed Errors

This is the implementation companion to my [GraphQL schema conventions](2026-06-22-graphql-schema-design-conventions-with-dgs.md). Here is how I wire those schemas up with [Netflix DGS](https://netflix.github.io/dgs/) and my [`graphql-dgs-starter`](https://github.com/denis-markushin/common-libs).

<!-- more -->

## 1. Namespace resolvers return `DUMMY_OBJECT`

Namespaced queries use a wrapper type — `ProjectQueries` in the schema — that holds the real fields. The top-level `@DgsQuery` just needs to return something non-null so DGS continues resolving; actual fields are wired via `@DgsData(parentType = ...)`. The `DUMMY_OBJECT` constant from the starter replaces the otherwise cryptic `emptyMap<String, Any>()` one-liner.

```kotlin
import com.netflix.graphql.dgs.DgsComponent
import com.netflix.graphql.dgs.DgsData
import com.netflix.graphql.dgs.DgsQuery
import graphql.relay.Connection
import org.dema.graphql.dgs.pagination.RelayPageable
import org.dema.graphql.dgs.util.Constants.DUMMY_OBJECT
import org.springframework.security.access.prepost.PreAuthorize

@DgsComponent
@PreAuthorize("isAuthenticated()")
class ProjectQueries(
    private val projectService: ProjectService,
) {
    @DgsQuery
    fun project() = DUMMY_OBJECT

    @DgsData(parentType = DgsConstants.PROJECT_QUERIES.TYPE_NAME)
    fun byId(id: UUID): Project = projectService.getById(id)

    @DgsData(parentType = DgsConstants.PROJECT_QUERIES.TYPE_NAME)
    fun all(
        first: Int = 20,
        after: String?,
        sort: ProjectSort = ProjectSort.CREATED_AT_DESC,
        filter: ProjectFilter?,
    ): Connection<Project> {
        val relayPageable = RelayPageable(first = first, after = after, sortingKey = sort)
        return projectService.getAll(relayPageable, filter)
    }
}
```

**Why it matters:**

- The namespace wrapper groups related queries without polluting the root `Query` type.
- `DUMMY_OBJECT` makes the intent explicit; `emptyMap()` leaves future readers guessing.
- `@DgsData(parentType = ...)` keeps each field resolver a small, focused method.

## 2. Entity fetchers for federation

When a federated gateway resolves a `@key` field on your type it calls the `_entities` query. DGS routes this to an `@DgsEntityFetcher`. The `requireUuid` helper from the starter handles the `Map<String, Any>` extraction safely, and the call is forwarded to a batch loader so the gateway's fan-out doesn't produce N+1 queries.

```kotlin
import com.netflix.graphql.dgs.DgsComponent
import com.netflix.graphql.dgs.DgsDataFetchingEnvironment
import com.netflix.graphql.dgs.DgsEntityFetcher
import org.dema.servicecore.extension.requireUuid
import java.util.concurrent.CompletableFuture

@DgsComponent
class ProjectEntityFetcher {

    @DgsEntityFetcher(name = DgsConstants.PROJECT.TYPE_NAME)
    fun project(values: Map<String, Any>, dfe: DgsDataFetchingEnvironment): CompletableFuture<Project> {
        val id = values.requireUuid("id")
        val loader = dfe.getDataLoader<UUID, Project>(ProjectBatchLoader::class.java)
        return loader.load(id)
    }
}
```

**Why it matters:**

- `requireUuid` throws a typed exception instead of hiding a `ClassCastException` or a silent `null`.
- Returning a `CompletableFuture` lets DGS batch all entity requests into a single loader call.
- The fetcher stays at three lines; business logic lives in the service, not here.

## 3. Batch loaders kill the N+1

The starter ships `AbstractBatchLoader<K, V>` so writing a loader is a single-expression subclass. The base class handles the empty-keys edge case and runs the fetch on a dedicated executor.

Base class from the starter:

```kotlin
abstract class AbstractBatchLoader<K, V>(
    private val executor: Executor,
    private val loaderFn: (Set<K>) -> Map<K, V>,
) : MappedBatchLoader<K, V> {

    override fun load(keys: Set<K>): CompletionStage<Map<K, V>> =
        if (keys.isEmpty()) CompletableFuture.completedFuture(emptyMap())
        else CompletableFuture.supplyAsync({ loaderFn(keys) }, executor)
}
```

Your loader (one expression):

```kotlin
import com.netflix.graphql.dgs.DgsDataLoader
import org.dema.graphql.dgs.loader.AbstractBatchLoader
import org.springframework.beans.factory.annotation.Qualifier
import java.util.concurrent.Executor

@DgsDataLoader
class UserBatchLoader(
    @Qualifier("dgsAsyncTaskExecutor") executor: Executor,
    private val userService: UserService,
) : AbstractBatchLoader<UUID, User>(
    executor = executor,
    loaderFn = { userService.getAllByIds(it).associateBy(User::id) },
)
```

And a fetcher that owns a foreign type stub (`UserEntityFetcher`):

```kotlin
@DgsComponent
class UserEntityFetcher {

    @DgsEntityFetcher(name = DgsConstants.USER.TYPE_NAME)
    fun user(values: Map<String, Any>, dfe: DgsDataFetchingEnvironment): CompletableFuture<User> {
        val userId = values.requireUuid("id")
        val loader = dfe.getDataLoader<UUID, User>(UserBatchLoader::class.java)
        return loader.load(userId)
    }
}
```

**Why it matters:**

- All entity keys are collected by DGS before your loader runs, so one DB call replaces N calls.
- `associateBy` is the idiomatic Kotlin way to turn a list into the `Map<K, V>` the interface needs.
- The `dgsAsyncTaskExecutor` qualifier ensures loaders run on the right thread pool, not the DGS default.

## 4. Mutation error handling without boilerplate

Mutations use the same namespace trick as queries. The resolver delegates to `MutationResolver` (from the starter) via Kotlin's `by` delegation to get the `resolveMutation {}` extension on `DataFetchingEnvironment`. This extension runs the service call and returns a sealed `MutationOutcome`; the `when` expression then maps `Success` and `Failure` to the typed result type declared in the schema.

```kotlin
import com.netflix.graphql.dgs.DgsComponent
import com.netflix.graphql.dgs.DgsData
import com.netflix.graphql.dgs.DgsMutation
import graphql.schema.DataFetchingEnvironment
import org.dema.graphql.dgs.mutation.MutationOutcome.Failure
import org.dema.graphql.dgs.mutation.MutationOutcome.Success
import org.dema.graphql.dgs.mutation.MutationResolver
import org.dema.graphql.dgs.util.Constants.DUMMY_OBJECT

@DgsComponent
class ProjectMutations(
    mutationResolver: MutationResolver,
    private val projectService: ProjectService,
) : MutationResolver by mutationResolver {

    @DgsMutation
    fun project() = DUMMY_OBJECT

    @DgsData(parentType = DgsConstants.PROJECT_MUTATIONS.TYPE_NAME)
    fun create(input: CreateProjectInput, dfe: DataFetchingEnvironment): CreateProjectResult =
        when (val r = dfe.resolveMutation { projectService.create(input) }) {
            is Success -> CreateProjectResult(
                recordId = { r.value.id },
                record = { r.value },
                status = { CommonResultStatus.SUCCESS },
                error = { null },
            )
            is Failure -> CreateProjectResult(
                recordId = { null },
                record = { null },
                status = { CommonResultStatus.FAILED },
                error = { r.error },
            )
        }
}
```

This pattern repeats for every mutation in the service — the shape is always the same `when (val r = dfe.resolveMutation { ... })` block. Typed errors (`NotFoundError`, `ConflictError`, and others) are provided by the starter, so you never hand-roll error types.

**Why it matters:**

- `by mutationResolver` delegation avoids open inheritance and keeps the resolver focused on field mapping.
- Clients that select the `error` field get a typed, structured error; clients that don't get a GraphQL top-level error — both are handled by the same code path.
- Exhaustive `when` on a sealed class means the compiler enforces that both outcomes are handled.

## 5. Virtual threads for free

Enabling virtual threads for DGS data fetchers is a single property:

```properties
dgs.graphql.virtualthreads.enabled=true
```

This lets DGS run each data fetcher on a virtual thread, which meaningfully improves throughput on I/O-bound resolvers (DB calls, HTTP fan-out) without any code changes.

One caveat: Spring Security's `SecurityContext` is stored in a `ThreadLocal` and does not propagate automatically to virtual threads. See my earlier post on [how to use DGS virtual threads with Spring Security](../../2024/12/2024-12-11-hot-use-dgs-virtual-threads-and-spring-security.md) for the propagation fix.

**Why it matters:**

- A single property replaces manual async wiring for I/O-bound resolvers.
- Throughput improvements show up immediately under load without changing resolver code.
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

These patterns — namespace resolvers, entity fetchers, batch loaders, typed mutation outcomes, virtual threads, and an integration test that drives the whole stack — cover the implementation side of the schema conventions described in the companion post. For the schema conventions that drive these resolver shapes, see [GraphQL Schema Design Conventions I Use with DGS and Federation](2026-06-22-graphql-schema-design-conventions-with-dgs.md).
