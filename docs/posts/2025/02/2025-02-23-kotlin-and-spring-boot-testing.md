---
authors:
  - denis
date:
  created: 2025-02-23
  updated: 2026-06-22
categories:
  - Testing
tags:
  - testing
  - kotlin
  - spring-boot
  - testcontainers
  - assertk
---

# Level Up Your Kotlin and Spring Boot Testing: Quick Tips and Tricks

When writing tests in Kotlin and Spring Boot, a few well-chosen techniques can make your tests more readable,
maintainable, and concise. Here are a couple of handy tips that you can apply to your projects today.

<!-- more -->

## 1. Use the `invoke` Operator to Generate Records

When working with libraries like [jOOQ](https://www.jooq.org/) (or similar), it’s common to create records in tests and
store them in a test database. You can save boilerplate code by encapsulating record creation in an `object` with an
`invoke` operator. This approach allows you to generate “fake” or test records with default values while still letting
you override specific fields as needed.

### Example Code

```kotlin
import java.time.LocalDateTime
import java.util.*

object TestRecordFactory {

  operator fun invoke(
    id: UUID = UUID.randomUUID(),
    name: String = "SampleName",
    description: String = "SampleDescription",
    createdAt: LocalDateTime = LocalDateTime.now(),
    updatedAt: LocalDateTime = LocalDateTime.now(),
    // ... more fields if needed
  ): SomeRecord = SomeRecord().apply {
    this.id = id
    this.name = name
    this.description = description
    this.createdAt = createdAt
    this.updatedAt = updatedAt
    // ... more fields
  }
}
```

In the snippet above:

* We define an `object` called `TestRecordFactory`.
* The `operator fun invoke(...)` method is where default values for each field are provided.
* Within the `apply` block, we set the properties on an instance of `SomeRecord` (a placeholder for your actual jOOQ
  record
  type).

### Usage in Tests

Here’s how you might use it in a test:

```kotlin
@Test
fun `should store a new record with default values`() {
  // Insert a record with all default values
  val record = TestRecordFactory()
  dsl.store(record)
  // ... further assertions or verifications
}

@Test
fun `should override some fields when needed`() {
  // Insert a record with a custom name
  val customRecord = TestRecordFactory(
    name = "MyCustomName"
  )
  dsl.store(customRecord)
  // ... further assertions or verifications
}
```

**Why it’s useful:**

* **Less boilerplate:** No need to manually fill out every field for each test.
* **Flexible overrides:** You can customize just the fields you need to.
* **Improved readability:** Test code clearly shows intent (creating a “fake” record) without clutter.

## 2. Generate Multiple Objects with Kotlin’s List Function

If you want to create multiple objects at once (e.g., a list of test records), Kotlin provides a handy inline function:

```kotlin
public inline fun <T> List(size: Int, init: (index: Int) -> T): List<T> = MutableList(size, init)
```

This allows you to quickly spin up **N** instances of a class (or record) with default or generated parameters. It’s
especially useful in scenarios where your test setup requires a batch of sample data.

### Example Code

Imagine you have a setup method in your test class that requires creating a certain number of “parent” objects, then
associating “child” objects with them. Here’s how you might do it:

```kotlin
@BeforeEach
fun setUp() {
  // Create 10 "parent" records
  val parentRecords = List(10) {
    TestRecordFactory()  // Use your own factory or constructor
  }
  store(parentRecords)

  // For each parent, create a random number of "child" records
  parentRecords.forEach { parent ->
    val childRecords = List((1..10).random()) {
      ChildRecordFactory(parentId = parent.id) // Example factory usage
    }
    store(childRecords)
  }

  println("Initialized ${parentRecords.size} parent records with associated children.")
}
```

**Why it’s useful:**

* **Batch creation:** Quickly create a fixed (or random) number of objects for test setup.
* **Readable:** The code clearly communicates that you’re initializing multiple objects.
* **Flexible:** Pair this with your record factory (invoke) to customize fields as needed.

## 3. Using `assertk`'s `prop` Function for Property-Based Assertions

When writing tests, comparing every field of an object manually can be tedious and error-prone. The assertk library
provides a convenient `prop` function that allows for clean, property-based assertions.

### Example Code

```kotlin
@Test
fun `using prop method test`() {
  // ...
  // then
  assertThat(result).all {
    isNotNull()
    prop(MyEntity::id).isEqualTo(entityUnderTest.id)
    prop(MyEntity::name).isEqualTo(entityUnderTest.name)
    prop(MyEntity::description).isEqualTo(entityUnderTest.description)
    prop(MyEntity::child).isNotNull()
  }
}
```

**Why it’s useful:**

1. Concise and readable: No need to write repetitive assertThat(result.property).isEqualTo(expected.property)
   statements.
2. Type-safe and expressive: Property-based assertions make it easier to verify structured data.
3. Supports transformations: You can use .transform { ... } to normalize or adjust values before comparison.

## 4. Use a UUID helper method for predictable, structured test data.

When you need unique but deterministic UUIDs in your tests, you can use a simple extension function:

```kotlin
import java.util.*

fun Int.uuid(): UUID = UUID.fromString("00000000-0000-0000-0000-${this.toString().padStart(11, '0')}")
```

### Example Usage

```kotlin
val entity = anEntity(id = 1.uuid())
```

## 5. Integration Tests on a Testcontainers Base Class

For integration tests, put all the wiring in a reusable base class: real infrastructure via Testcontainers,
a clean database before each test, and tiny helpers to persist records. Subclasses stay focused on behavior.

```kotlin
@ActiveProfiles("integration-test")
@TestInstance(Lifecycle.PER_CLASS)
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@ContextConfiguration(initializers = [MinioInitializer::class, KafkaInitializer::class])
abstract class AbstractIntegrationTest {

    @Autowired
    protected lateinit var dsl: DSLContext

    @Autowired
    protected lateinit var queryExecutor: DgsQueryExecutor

    @BeforeEach
    fun cleanup() {
        TABLES_TO_CLEANUP.forEach { dsl.truncate(it).cascade().execute() }
    }

    protected fun <R : UpdatableRecord<R>> R.storeRec(): R = also {
        dsl.attach(it)
        it.store()
    }
}
```

**Why it's useful:**

* **Real infrastructure:** Postgres, Kafka and object storage run in containers, not mocks — no H2 surprises.
* **Deterministic state:** `TRUNCATE ... CASCADE` before each test removes cross-test coupling.
* **Less boilerplate:** `storeRec()` attaches and stores any jOOQ record in one call.

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

## Conclusion

By combining these techniques — from record factories to a shared Testcontainers base class and type-safe GraphQL operations — you’ll streamline both unit and integration test setups, reduce boilerplate, and keep your focus on writing meaningful test logic. Happy testing!