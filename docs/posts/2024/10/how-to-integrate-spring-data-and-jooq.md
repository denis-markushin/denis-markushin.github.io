---
date: 2024-10-01
categories:
  - Kotlin
  - Jooq
tags:
  - Kotlin
  - Jooq
---

# Integrating Jooq with Spring Data

In this post, we will explore the [jooq-utils] library, which provides seamless integration between Spring Data and
Jooq. With [jooq-utils], you can retrieve data using Jooq and get a `Page` object (from
`org.springframework.data.domain.Page`) as a result, and easily use `Pageable` as input for repository methods.

<!-- more -->

## Overview

The `jooq-utils` library simplifies the pagination of Jooq results by enabling you to:

- Use Spring Data’s `Pageable` in your Jooq queries.
- Return paginated results in the form of `Page<T>`.

This is especially useful in Spring-based applications that use Jooq for database interaction, where you need to
integrate the pagination functionality of Spring Data.

## Sample Code

Let’s walk through a sample use case to show how this library can be applied in your projects.

### 1. Create the Repository

```kotlin
import org.jooq.Condition
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.stereotype.Component
import org.dema.Tables.USERS
import org.dema.jooq.AbstractRepository
import org.dema.jooq.JooqUtils

@Component
class UsersRepository : AbstractRepository<Users, UsersRecord>(table = USERS) {

  fun getPageBy(pageable: Pageable, condition: Condition): Page<UsersRecord> {
    val query = baseQuery({ condition })
    return JooqUtils.paginate(dsl, query, pageable, USERS)
  }

  private fun baseQuery(vararg where: (Users) -> Condition): SelectConditionStep<UsersRecord> {
    return dsl.selectFrom(USERS)
      .where(foldConditions(where))
  }
}
```

In the above code:

We define a UsersRepository class that extends AbstractRepository.
The getPageBy() method allows pagination of the user records based on the provided Condition and Pageable parameters.
The actual pagination logic is handled by JooqUtils.paginate().

### 2. Use the Repository in a Service

```kotlin
import org.jooq.Condition
import org.jooq.impl.DSL.noCondition
import org.springframework.data.domain.Page
import org.springframework.data.domain.Pageable
import org.springframework.stereotype.Service
import org.springframework.core.convert.ConversionService
import org.springframework.transaction.annotation.Transactional

@Service
@Transactional(readOnly = true)
class UsersService(
  @Qualifier("mvcConversionService") private val cs: ConversionService,
  private val usersRepository: UsersRepository,
) {

  fun search(filter: UsersFilter, pageable: Pageable): UsersPage {
    val filterCondition: Condition = filter?.let(cs::convert) ?: noCondition()
    val userRecordsPage: Page<UsersRecord> = usersRepository.getPageBy(pageable, filterCondition)
    return cs.convert(userRecordsPage)!!
  }
}
```

In the UsersService class:

* We define a `search()` method that receives a `UsersFilter` and a `Pageable`.
* The service converts the `filter` into a `Condition`, which is passed to the repository method `getPageBy()`.
* The paginated result is returned as a `UsersPage` after conversion.

### 3. Conclusion

That’s it! You now have a working example of integrating Spring Data’s pagination functionality into Jooq using
`jooq-utils`. The provided repository and service examples demonstrate how to handle pagination in your Jooq queries
with
minimal code changes.

[jooq-utils]: https://github.com/denis-markushin/common-libs/tree/main/jooq-utils