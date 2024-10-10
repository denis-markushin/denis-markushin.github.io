---
date: 2024-10-10
categories:
  - Plugins 
tags:
  - Gradle
  - SchemaSpy
  - Database
  - Testcontainers
---

# How to generate Interactive Database Documentation with SchemaSpy and Gradle

Gradle plugin that lets you generate database [documentation](https://schemaspy.org/samples/epivirusurf/)
using [Schemaspy](https://schemaspy.org)
and [Testcontainers](https://testcontainers.com)

<!-- more -->

## Overview

The [schemaspy-gradle-plugin] allows you to generate database documentation via [DDL]. Let`s consider an example. In the
example I'll use [postgres sakila schema].

The plugin uses the following tools:

* SchemaSpy is a tool that generates interactive database documentation by analyzing your database schema. It's
  especially useful for visualizing relationships between tables and understanding the overall structure of the
  database.
* Gradle is a versatile build tool that automates the process of building, testing, and deploying software. Here, we use
  it to integrate SchemaSpy easily into our build workflow.
* Testcontainers is a Java library that provides throwaway instances of databases (among other things) for integration
  testing. In this context, it allows you to run a real instance of your database for generating documentation.

These tools together allow you to automate the creation of up-to-date database documentation within your CI/CD pipeline,
ensuring that developers and analysts always have the latest version available.

## How to use

1. Add dependency:
   ```kotlin
   plugins {
    id("io.github.denis-markushin.schemaspy-plugin")
   }
   ```
2. Configure the plugin using an extension:
   ```kotlin
   schemaspyConfig {
     dbName = "sakila"
     liquibaseChangelog = file("${project.projectDir}/src/main/resources/liquibase/changelog.yml")
     outputDir = project.layout.buildDirectory.dir("schemaspy/sakila")
   }
   ```
3. Run `gradle generateSchemaspyDocs`.
4. Get output in gradle `build/schemaspy/db/output` folder.
   ![SchemaSpy Sakila DB example](schemaspy-sakila-db-example.gif)

    !!! note
        Open `build/schemaspy/sakila/output/index.html` locally

## Plugin Configuration Breakdown

Let’s break down the configuration steps in more detail to clarify the purpose of each setting:

1. `dbName`:
   This property specifies the name of the database for which you want to generate the documentation. In our example,
   it's set to "sakila" (a sample database for practice).
2. `liquibaseChangelog`:
   This refers to the path of the Liquibase changelog file. Liquibase is a tool for managing database schema changes. By
   specifying the changelog file here, the plugin can track and apply any updates to your database schema before
   generating the documentation.
3. postgresDockerImage:
   The plugin uses Docker to run a PostgreSQL instance for generating the database documentation. This property allows
   you to define which version of the PostgreSQL image to use. By default, it’s set to "postgres:13.5-alpine", but you
   can customize it if needed.
4. `schemaspyDockerImage`:
   This defines the Docker image for SchemaSpy itself, which will be used to generate the interactive documentation. The
   default value is "schemaspy/schemaspy:6.1.0", ensuring you're using a specific version of SchemaSpy.
5. `excludeTables`:
   This property specifies tables that should be excluded from the documentation generation. By default, it excludes
   Liquibase’s internal tables like "databasechangeloglock" and "databasechangelog", as they are not relevant for schema
   documentation purposes.
6. `unzipOutput`:
   A boolean property that determines whether the output should be unzipped or not after the documentation is generated.
   The default value is true, which means the documentation files will be unzipped for easier access.
7. `outputDir`:
   This property defines the directory where the generated SchemaSpy output will be saved. You can specify any directory
   of your choice, but in this case, it’s configured to the build/schemaspy/sakila folder.

These settings provide a lot of flexibility, allowing you to customize the plugin’s behavior according to your project’s
requirements.

## Conclusion

Using the SchemaSpy Gradle plugin, you can effortlessly generate comprehensive database documentation. This
documentation is not only beneficial for analytics but also serves various other purposes:

- **For Developers**: It helps developers understand the database structure, relationships, and dependencies, making it
  easier to work with the data layer.
- **For Testers**: Testers can refer to the documentation to create effective test cases based on the actual database
  schema and its constraints.
- **For Compliance**: Regulatory compliance often requires detailed documentation of data structures. This plugin
  facilitates adherence to such requirements by providing clear and updated documentation.

Additionally, you can integrate this process into your CI/CD pipeline to ensure that documentation is automatically
generated and deployed to platforms like [GitLab](https://docs.gitlab.com/ee/user/project/pages/)
or [GitHub](https://pages.github.com), keeping your team aligned with the latest schema changes.

The full example can be found on [GitHub](https://github.com/denis-markushin/schemaspy-gradle-plugin/tree/main/example).

[schemaspy-gradle-plugin]: https://github.com/denis-markushin/schemaspy-gradle-plugin
[DDL]: https://en.wikipedia.org/wiki/Data_definition_language
[postgres sakila schema]: https://github.com/denis-markushin/schemaspy-gradle-plugin/blob/main/example/src/main/resources/liquibase/scripts/postgres-sakila-schema.sql