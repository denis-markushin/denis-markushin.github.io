---
date: 2025-02-03
categories:
  - Openapi
  - Feign
  - Spring Boot
tags:
  - openapi
  - feign
  - spring-boot
---

# Integration of Feign Clients and OpenAPI Generator: Enabling client_credentials

In this post, we will explore how to integrate
the [OpenAPI Generator Gradle Plugin](https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator-gradle-plugin)
with [Spring Feign clients](https://docs.spring.io/spring-cloud-openfeign/docs/current/reference/html/) to obtain an
OAuth 2.0 token using the `client_credentials` flow.

<!-- more -->

## Overview

We will walk through:

- Declaring the OAuth 2.0 security scheme (client_credentials) in the OpenAPI specification
- Generating Feign clients using the OpenAPI Generator
- Adding Spring Boot OAuth 2.0 client configuration for Keycloak in `application.yml`

## OpenAPI Specification and Security Scheme

To enable OAuth 2.0 with a `client_credentials` flow, you need to define your security scheme in the OpenAPI
specification. Below is a minimal example of how you can declare the scheme (based
on [this reference](https://www.speakeasy.com/openapi/security/security-schemes/security-oauth2#oauth-20-security-scheme-with-multiple-flows-in-openapi)):

```yaml
openapi: 3.0.3
info:
  title: My API
  version: 1.0.0

paths:
  /example:
    get:
      security:
        - OAuth2ClientCredentials: [ ]
      responses:
        '200':
          description: Success

components:
  securitySchemes:
    OAuth2ClientCredentials:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: https://my-keycloak-domain/auth/realms/myrealm/protocol/openid-connect/token
          scopes:
            read: Grants read access
```

When you generate code with the OpenAPI Generator, it will recognize the security scheme and allow for the configuration
of OAuth 2.0 in your client.

!!! note
    The property name for the Keycloak provider settings includes the suffix`Application`. For example, if your scheme is
    called `OAuth2ClientCredentials`, you might see something like
    `spring.security.oauth2.client.registration.oAuth2ClientCredentialsApplication` in your `application.yml`.
  
Below is an example of such a generated configuration class:

```java
import org.springframework.context.annotation.Bean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.oauth2.client.AuthorizedClientServiceOAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizeRequest;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientManager;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.http.HttpHeaders;

import feign.RequestInterceptor;
import feign.RequestTemplate;

import org.springframework.context.annotation.Configuration;


public class ClientConfiguration {

  private static final String CLIENT_PRINCIPAL_APPLICATION = "oauth2FeignClient";

  @Bean
  @ConditionalOnProperty(
    prefix = "spring.security.oauth2.client.registration.oAuth2ClientCredentialsApplication",
    name = "enabled",
    havingValue = "true"
  )
  public OAuth2RequestInterceptor applicationOAuth2RequestInterceptor(
    final OAuth2AuthorizedClientManager applicationAuthorizedClientManager
  ) {
    return new OAuth2RequestInterceptor(
      OAuth2AuthorizeRequest
        .withClientRegistrationId("oAuth2ClientCredentialsApplication")
        .principal(
          new AnonymousAuthenticationToken(
            CLIENT_PRINCIPAL_APPLICATION,
            CLIENT_PRINCIPAL_APPLICATION,
            AuthorityUtils.createAuthorityList("ROLE_ANONYMOUS")
          )
        )
        .build(),
      applicationAuthorizedClientManager
    );
  }

  @Bean
  @ConditionalOnProperty(
    prefix = "spring.security.oauth2.client.registration.oAuth2ClientCredentialsApplication",
    name = "enabled",
    havingValue = "true"
  )
  public OAuth2AuthorizedClientManager applicationAuthorizedClientManager(
    ClientRegistrationRepository clientRegistrationRepository,
    OAuth2AuthorizedClientService authorizedClientService
  ) {
    return new AuthorizedClientServiceOAuth2AuthorizedClientManager(
      clientRegistrationRepository,
      authorizedClientService
    );
  }

  public static class OAuth2RequestInterceptor implements RequestInterceptor {

    private final OAuth2AuthorizedClientManager oAuth2AuthorizedClientManager;
    private final OAuth2AuthorizeRequest oAuth2AuthorizeRequest;

    public OAuth2RequestInterceptor(
      OAuth2AuthorizeRequest oAuth2AuthorizeRequest,
      OAuth2AuthorizedClientManager oAuth2AuthorizedClientManager
    ) {
      this.oAuth2AuthorizeRequest = oAuth2AuthorizeRequest;
      this.oAuth2AuthorizedClientManager = oAuth2AuthorizedClientManager;
    }

    @Override
    public void apply(final RequestTemplate template) {
      template.header(HttpHeaders.AUTHORIZATION, getBearerToken());
    }

    public OAuth2AccessToken getAccessToken() {
      final OAuth2AuthorizedClient authorizedClient = oAuth2AuthorizedClientManager.authorize(oAuth2AuthorizeRequest);
      if (authorizedClient == null) {
        throw new OAuth2AuthenticationException("Client failed to authenticate");
      }
      return authorizedClient.getAccessToken();
    }

    public String getBearerToken() {
      final OAuth2AccessToken accessToken = getAccessToken();
      return String.format(
        "%s %s",
        accessToken.getTokenType().getValue(),
        accessToken.getTokenValue()
      );
    }
  }

}
```

## Spring Application Configuration

### Adding the Spring Boot OAuth2 Starter

Add the following dependency in your `build.gradle` (or `pom.xml` if you are using Maven):

```groovy
dependencies {
  implementation 'org.springframework.boot:spring-boot-starter-oauth2-client'
}
```

This
starter ([see official documentation](https://docs.spring.io/spring-security/reference/servlet/oauth2/index.html#oauth2-client-client-credentials))
provides OAuth2 client support for Spring Boot applications.

### Defining OAuth2 Settings in `application.yml`

Configure your Keycloak settings in `application.yml` so that Feign clients can automatically request tokens using
`client_credentials`:

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          oAuth2ClientCredentialsApplication:
            client-id: your-client-id
            client-secret: your-client-secret
            authorization-grant-type: client_credentials
            scope: read
        provider:
          keycloak:
            token-uri: https://my-keycloak-domain/auth/realms/myrealm/protocol/openid-connect/token
```

Key points here:

- `oAuth2ClientCredentialsApplication` is the registration name for your client credentials setup.
- `client-id` and `client-secret` are values provided by your Keycloak realm.
- `authorization-grant-type` is set to `client_credentials`.
- `provider.keycloak.token-uri` matches the `tokenUrl` in your OpenAPI specification.

Spring Boot will use these settings to fetch the token automatically before calling your Feign clients.

## Conclusion

By defining a `client_credentials` flow in your OpenAPI specification and configuring Spring Boot OAuth 2.0 Client with
Keycloak, you can generate Feign clients that seamlessly retrieve an access token before making API requests. This
approach helps ensure that your microservices remain secure and that credentials are fetched in a standardized,
automated fashion.

Feel free to explore more advanced capabilities of
the [OpenAPI Generator Gradle Plugin](https://github.com/OpenAPITools/openapi-generator/tree/master/modules/openapi-generator-gradle-plugin)
for additional customization options.