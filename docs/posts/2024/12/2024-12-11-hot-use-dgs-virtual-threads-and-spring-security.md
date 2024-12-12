---
date: 2024-12-11
categories:

  - Kotlin
  - DGS
tags:
  - Kotlin
  - DGS
---

# How to Use Virtual Threads in DGS

In this post, I’ll explain how to use virtual threads with Netflix DGS in a GraphQL application. While exploring this
feature, I encountered several undocumented challenges and found solutions that I’m excited to share.

<!-- more -->

## Overview

The DataLoader pattern is essential for solving the **N + 1 problem** in GraphQL.
The [DGS Framework](https://netflix.github.io/dgs/) provides a convenient `@DgsDataLoader` annotation for implementing
DataLoaders.

To handle batched loading, I implemented the [
`org.dataloader.MappedBatchLoader`](https://netflix.github.io/dgs/data-loaders/#mappedbatchloader) interface.
`MappedBatchLoader` is ideal when not all keys are expected to have values, as it creates a `Map` of key/values for a
`Set` of keys rather than a `List` for a `List`.

Additionally, DGS introduced virtual threads to improve concurrency. Below, I’ll explain the steps I followed, the
challenges I faced, and how I resolved them.

## Sample Code

### Implementing a DataLoader

The `@DgsDataLoader` annotation simplifies creating DataLoaders. Here's my implementation:

```kotlin
@DgsDataLoader(caching = true)
class UsersDataLoader(
  private val usersService: UsersService,
  private val dgsAsyncTaskExecutor: Executor,
) : MappedBatchLoader<String, User?> {

  override fun load(ids: Set<String>): CompletionStage<Map<String, User?>> {
    return CompletableFuture.supplyAsync({
      usersService.getAllByUserIds(ids)
        .associateBy { it.id }
        .let { resultMap -> keys.associateWith { resultMap[it] } }
    }, dgsAsyncTaskExecutor)
  }
}
```

This implementation ensures efficient batching and mapping using `MappedBatchLoader`.

## Virtual Threads in DGS

### Enabling Virtual Threads

DGS Framework supports using virtual threads through a simple property:

```properties
dgs.graphql.virtualthreads.enabled=true
```

When enabled, each user-defined data fetcher executes in a new virtual thread, as confirmed by logs like:

```
2024-12-11 22:51:29.494 +0300 [,,] [dgs-virtual-thread-2] INFO [Logger] : #getById(...) in 389.88ms
```

### Issue with Spring Security

However, when integrating Spring Security, if you use `@PreAuthorize`\\`@Secured`\etc. for access control, you might
encounter issues with context propagation. I encountered the following error:

```
An Authentication object was not found in the SecurityContext
```

This occurs because virtual threads do not automatically propagate the `SecurityContext`. For details, see
the [Spring Security documentation](https://docs.spring.io/spring-security/reference/features/integrations/concurrency.html).

## Fixing Security Context Propagation

The `DgsAutoConfiguration` class declares a bean for an `AsyncTaskExecutor` when the property
`dgs.graphql.virtualthreads.enabled` is set to `true`:

```kotlin
@Bean
@Qualifier("dgsAsyncTaskExecutor")
@ConditionalOnJava21
@ConditionalOnMissingBean(name = ["dgsAsyncTaskExecutor"])
@ConditionalOnProperty(name = ["dgs.graphql.virtualthreads.enabled"], havingValue = "true", matchIfMissing = false)
open fun virtualThreadsTaskExecutor(contextRegistry: ContextRegistry): AsyncTaskExecutor {
  LOG.info("Enabling virtual threads for DGS")
  val contextSnapshotFactory = ContextSnapshotFactory.builder().contextRegistry(contextRegistry).build()
  return VirtualThreadTaskExecutor(contextSnapshotFactory)
}
```

However, this default `AsyncTaskExecutor` does not propagate the `SecurityContext`. To ensure compatibility with Spring
Security, I wrapped it in a `DelegatingSecurityContextAsyncTaskExecutor`.

### Custom Configuration

Here’s the updated configuration:

```kotlin
@Configuration(proxyBeanMethods = false)
class AsyncExecutorConfig {

  @Bean
  fun dgsAsyncTaskExecutor(contextRegistry: ContextRegistry): AsyncTaskExecutor {
    log.info("Enabling virtual threads for DGS")
    val contextSnapshotFactory = ContextSnapshotFactory.builder().contextRegistry(contextRegistry).build()
    return DelegatingSecurityContextAsyncTaskExecutor(VirtualThreadTaskExecutor(contextSnapshotFactory))
  }
}
```

This ensures that the security context is properly propagated while using virtual threads.

!!! note
    If you enable `dgs.graphql.virtualthreads.enabled=true`, you must disable this property to avoid conflicts with the
    `DgsAutoConfiguration`-provided bean that does not propagate the `SecurityContext`.

## Results

After applying these changes, my Data Fetchers run seamlessly on virtual threads while maintaining proper security
context propagation. Logs show improved execution:

```
2024-12-11 22:51:30.496 +0300 [,,] [dgs-virtual-thread-4] INFO [Logger] : #getAllByIds(['1', '2']): [...] in 140.02ms
```

## Conclusion

Using virtual threads in DGS can significantly enhance concurrency. However, for projects with Spring Security,
additional configuration is required to propagate the `SecurityContext`. The steps outlined above should help you
integrate this effectively and make the most of virtual threads in your GraphQL applications.