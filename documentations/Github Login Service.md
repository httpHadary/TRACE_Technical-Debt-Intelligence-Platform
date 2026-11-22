# GitHub Integration Service

**Project:** TechDept365  
**Module:** GitHub Authentication & Repository Discovery  
**Status:** Implemented and locally verified with `./mvnw clean verify`  
**Last documented source snapshot:** 9 November 2026

## 1. Purpose and scope

The GitHub Integration Service connects an authenticated TechDept365 user to GitHub. It is responsible for:

1. Starting and completing GitHub OAuth 2.0 authorization.
2. Maintaining the authenticated user's GitHub authorized client through Spring Security.
3. Exposing the signed-in GitHub profile to the application.
4. Listing repositories visible to that user's GitHub authorization, including accessible private repositories.
5. Handling pagination safely and mapping GitHub failures to consistent API responses.
6. Removing an invalid stored GitHub authorization after GitHub rejects its token with HTTP 401.

This module does **not** clone repositories, download source code, inspect files, calculate technical debt, or start the analysis pipeline. Repository overview/selection/confirmation is also outside the current implemented scope.

## 2. Technology stack

| Concern | Implementation |
|---|---|
| Language | Java 25 |
| Framework | Spring Boot 4.1.2 |
| Security | Spring Security OAuth2 Client |
| HTTP API | Spring MVC / `spring-boot-starter-webmvc` |
| GitHub HTTP client | Spring `RestClient` backed by JDK `HttpClient` |
| Serialization | Jackson record mapping |
| Build | Maven Wrapper |
| Tests | JUnit 5, Spring Boot Test, MockMvc, Spring Security Test, Mockito, AssertJ |

The Maven project uses `spring-boot-starter-security-oauth2-client` for OAuth login and authorized-client support. Test dependencies are `spring-boot-starter-webmvc-test` and `spring-boot-starter-security-test`.

## 3. High-level architecture

```text
Browser / Frontend
       |
       | 1. GET /oauth2/authorization/github
       v
Spring Security OAuth2 Client
       |
       | Redirect to GitHub authorization page
       v
GitHub OAuth
       |
       | 2. User approves requested scopes
       | 3. Redirect to /login/oauth2/code/github
       v
Spring Security OAuth2 Login
       |
       | Exchanges authorization code for access token
       | Loads authenticated principal and stores authorized client
       v
Authenticated application session
       |
       +-----------------------+
       |                       |
       v                       v
GET /api/me              GET /api/repos
       |                       |
       v                       v
OAuth2User attributes    GithubController
                               |
                               | Current user's GitHub access token
                               v
                         GithubService
                               |
                               | GET https://api.github.com/user/repos
                               | Sequential pagination
                               v
                           GitHub API
```

### Main components

| Component | Responsibility |
|---|---|
| `SecurityConfig` | Public/protected routes, OAuth login, browser redirects, API 401 behavior, logout |
| `GithubClientConfig` | Configures the reusable GitHub `RestClient`, API headers and network timeouts |
| `GithubController` | Exposes `/api/me` and `/api/repos` |
| `GithubService` | Calls GitHub's repository endpoint and collects all permitted pages |
| `GithubRepo` | Maps the repository fields returned by GitHub |
| `GithubExceptionHandler` | Converts GitHub/network/pagination exceptions into safe Problem Details responses; removes invalid user authorization on 401 |
| `RepositoryLimitExceededException` | Signals that the configured pagination safety cap was reached |
| `HomeController` | Provides a minimal HTML landing page with login, API links and CSRF-protected logout form |

## 4. Authentication and authorization

### 4.1 OAuth application configuration

The application uses a GitHub OAuth App registered in Spring Security under registration ID `github`.

The client ID and client secret are injected from environment variables:

- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

They must not be committed to source control or written into logs. In IntelliJ, configure them as separate environment variables in the application's Run Configuration.

### 4.2 Requested scopes

Default scopes:

| Scope | Purpose |
|---|---|
| `read:user` | Read the authenticated user's GitHub profile |
| `repo` | Read public and private repositories the user is authorized to access |

The default is configured as:

```properties
spring.security.oauth2.client.registration.github.scope=${GITHUB_OAUTH_SCOPE:read:user,repo}
```

`GITHUB_OAUTH_SCOPE` can override the default. For example, `read:user,public_repo` limits the requested repository permission to public repositories.

**Important permission trade-off:** GitHub OAuth Apps do not provide a read-only OAuth scope for private repository access. The `repo` scope is broad and includes write permissions, even though this service currently performs read-only GitHub API calls. A GitHub App with minimum repository permissions should be evaluated before source-code analysis is introduced.

#### Organization repository access

The `organization_member` affiliation does not guarantee that every organization repository will appear. GitHub controls visibility based on both the user's membership and the OAuth application's authorization:

- **Third-party OAuth App restrictions:** an organization can restrict OAuth Apps. An organization owner may need to approve this application under the organization's third-party access settings before its private repositories become visible.
- **SAML SSO:** if an organization enforces SAML SSO, the user may need to authorize the OAuth token for that organization. Without this authorization, the organization's repositories may be omitted.
- **Missing repositories are not necessarily an application defect:** verify the organization's OAuth App policy and SSO authorization before investigating the listing implementation.

#### Scope changes and existing users

Changing `GITHUB_OAUTH_SCOPE` changes the scopes requested during a new authorization; it does not upgrade tokens that users have already granted. A user who previously authorized only `read:user,public_repo` will continue to have a token limited to public repository access until they authorize again. The service's login entry point is `/oauth2/authorization/github`. After reauthorization, Spring Security stores the newly authorized client for the user.

Operational procedure when changing scopes:

1. Deploy the application with the intended scope configuration.
2. Ask existing users to sign in again through `/oauth2/authorization/github` (or revoke the app in GitHub settings and then sign in again).
3. Verify that GitHub's consent screen displays the expected permissions.
4. Verify repository visibility using an account with the relevant public, private, or organization repositories.

#### Future permission model

Before implementing repository-content download or source-code analysis, evaluate migrating from the OAuth App to a GitHub App. A GitHub App can use narrower repository permissions, such as read-only Metadata for repository discovery and read-only Contents when source analysis is implemented. This is a future architectural decision, not part of the current service implementation; installation-based repository access and token lifecycle would need to be designed and tested.

### 4.3 Login flow

1. The client navigates to `/oauth2/authorization/github`.
2. Spring Security constructs the GitHub authorization URL, including `client_id`, `redirect_uri`, `state`, and requested scopes.
3. GitHub authenticates the user and asks for consent when required.
4. GitHub redirects to `/login/oauth2/code/github` with the authorization response.
5. Spring Security completes the authorization-code exchange and creates the authenticated principal.
6. Spring Security stores the user's GitHub `OAuth2AuthorizedClient` using the configured authorized-client repository.
7. Subsequent authenticated requests can access the principal and the corresponding authorized client.

The application does not manually receive, parse, or persist the access token in controller code. Spring Security owns that lifecycle.

### 4.4 Request authorization behavior

- `/` and `/error` are public.
- All other application paths require authentication.
- Unauthenticated `/api/**` requests return HTTP 401, not a redirect to GitHub.
- Unauthenticated browser requests that accept `text/html` are redirected to `/oauth2/authorization/github`.
- Other non-browser requests receive HTTP 401.
- Logout uses Spring Security's POST `/logout` endpoint and requires a CSRF token.
- Successful logout redirects to `/`.

The application retains Spring Security's CSRF protection; the landing page includes a CSRF token in its logout form.

### 4.5 Session model

The current implementation relies on Spring Security's default servlet-session behavior to maintain the authenticated browser session and authorized-client association. There is no Redis integration or custom distributed session store in this module. Consequently, the current approach is intended for the present single-instance deployment model; a multi-instance deployment would require an explicitly shared session/authorized-client strategy or appropriate sticky-session design.

## 5. HTTP API

All application API endpoints are under `/api` and require an authenticated session.

### 5.1 `GET /api/me`

Returns selected attributes from the authenticated GitHub principal. The attributes are loaded by Spring Security during OAuth login.

Example response:

```json
{
  "login": "octocat",
  "name": "The Octocat",
  "avatarUrl": "https://avatars.githubusercontent.com/u/1",
  "profileUrl": "https://github.com/octocat"
}
```

Fields:

| Field | Source GitHub attribute | Notes |
|---|---|---|
| `login` | `login` | GitHub username/login |
| `name` | `name` | May be `null` or absent for users without a public name |
| `avatarUrl` | `avatar_url` | Avatar image URL |
| `profileUrl` | `html_url` | GitHub profile URL |

The response is assembled with a `LinkedHashMap`, which permits a null `name` value.

Unauthenticated response: `401 Unauthorized`.

### 5.2 `GET /api/repos`

Returns the repositories visible to the authenticated user's GitHub authorization.

The controller obtains the current user's authorized client with `@RegisteredOAuth2AuthorizedClient("github")` and passes that client's access token to `GithubService`. It does not accept a token from the caller.

Example response (illustrative subset of the DTO fields):

```json
[
  {
    "id": 123456,
    "name": "hello",
    "full_name": "octocat/hello",
    "description": "A sample repository",
    "html_url": "https://github.com/octocat/hello",
    "clone_url": "https://github.com/octocat/hello.git",
    "ssh_url": "git@github.com:octocat/hello.git",
    "private": false,
    "fork": false,
    "archived": false,
    "language": "Java",
    "topics": ["example"],
    "stargazers_count": 5,
    "forks_count": 2,
    "open_issues_count": 1,
    "default_branch": "main",
    "visibility": "public",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2026-11-01T10:00:00Z",
    "pushed_at": "2026-11-02T10:00:00Z",
    "owner": {
      "login": "octocat",
      "html_url": "https://github.com/octocat"
    }
  }
]
```

The exact fields returned are defined by the `GithubRepo` record. Unknown JSON fields from GitHub are ignored. Optional fields such as `description`, `language`, `topics`, timestamps, and nullable Boolean repository flags may be absent or null.

An account with no visible repositories receives an empty JSON array (`[]`).

Unauthenticated response: `401 Unauthorized`.

## 6. GitHub API integration

### 6.1 Upstream endpoint

The service calls:

```http
GET https://api.github.com/user/repos
Authorization: Bearer <current-user-access-token>
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

The base URL is configurable through `github.api.base-url`; its default is `https://api.github.com`.

### 6.2 Query parameters

Each page request includes:

| Parameter | Value | Purpose |
|---|---|---|
| `per_page` | `100` | GitHub's maximum page size |
| `page` | `1`, `2`, ... | Sequential page number |
| `sort` | `updated` | Sort repositories by last update |
| `visibility` | `all` | Include public and private repositories visible to the token |
| `affiliation` | `owner,collaborator,organization_member` | Include repositories owned by, collaborated on, or accessible through organization membership |

GitHub remains the authority on which repositories are visible. The service does not probe guessed repository names or expose repositories the token cannot access.

Organization repositories may be absent if an organization restricts third-party OAuth Apps or requires SAML SSO authorization that has not been granted. These are GitHub-side authorization constraints, not necessarily service defects; see Section 4.2 for the checks to perform.

### 6.3 Pagination algorithm

`GithubService.fetchAllRepos(accessToken)` performs sequential requests:

1. Start at page 1.
2. Request up to 100 repositories.
3. If the response is null or empty, return the repositories collected so far.
4. Append the returned batch.
5. If fewer than 100 repositories were returned, this is the last page; return the complete list.
6. Otherwise request the next page, until the configured page limit is reached.
7. If every allowed page was full, throw `RepositoryLimitExceededException` rather than silently returning a potentially incomplete list.

Configuration:

```properties
github.api.max-pages=50
```

Default maximum: 50 pages × 100 repositories = 5,000 repositories per request. Reaching this cap results in HTTP 422. Because the service cannot know whether another page exists without making another request, an account with exactly 5,000 repositories is also rejected when all 50 pages are full. This is an intentional safety-cap behavior documented in the code.

### 6.4 HTTP client timeouts

`GithubClientConfig` creates a JDK `HttpClient` with:

- Connection timeout: 3 seconds.
- Read timeout: 10 seconds.

The resulting `RestClient` is configured with the GitHub API base URL and required GitHub headers. The client is a reusable Spring bean; the access token is supplied per service call rather than stored as a mutable global default.

## 7. Repository data model

`GithubRepo` is a Java record representing the subset of GitHub's repository response consumed by this service.

| Java property | GitHub JSON property | Java type |
|---|---|---|
| `id` | `id` | `long` |
| `name` | `name` | `String` |
| `fullName` | `full_name` | `String` |
| `description` | `description` | `String` |
| `htmlUrl` | `html_url` | `String` |
| `cloneUrl` | `clone_url` | `String` |
| `sshUrl` | `ssh_url` | `String` |
| `isPrivate` | `private` | `Boolean` |
| `fork` | `fork` | `Boolean` |
| `archived` | `archived` | `Boolean` |
| `language` | `language` | `String` |
| `topics` | `topics` | `List<String>` |
| `stars` | `stargazers_count` | `Integer` |
| `forks` | `forks_count` | `Integer` |
| `openIssues` | `open_issues_count` | `Integer` |
| `defaultBranch` | `default_branch` | `String` |
| `visibility` | `visibility` | `String` |
| `createdAt` | `created_at` | `Instant` |
| `updatedAt` | `updated_at` | `Instant` |
| `pushedAt` | `pushed_at` | `Instant` |
| `owner` | `owner` | nested `Owner` record |

The nested `Owner` record contains `login` and `htmlUrl` (mapped from `html_url`). `@JsonIgnoreProperties(ignoreUnknown = true)` on both records makes mapping tolerant of additional GitHub response fields.

## 8. Error handling contract

`GithubExceptionHandler` is a `@RestControllerAdvice` that returns RFC 9457-style `ProblemDetail` bodies with content type `application/problem+json`.

| GitHub/network condition | Application status | Client-facing detail |
|---|---:|---|
| GitHub 401 (invalid, expired or revoked token) | 401 | GitHub connection is invalid/revoked; sign in again |
| GitHub 403 with primary/secondary rate-limit indicators | 429 | GitHub rate limit reached; try later |
| GitHub 429 | 429 | GitHub rate limit reached; try later |
| Genuine GitHub 403 | 403 | GitHub denied access to the requested resource |
| Other GitHub 4xx | 502 | GitHub returned an unexpected response |
| GitHub 5xx | 502 | GitHub is currently unavailable |
| Connection/read timeout | 504 | GitHub did not respond in time |
| Other network failure (e.g. DNS/refused connection) | 502 | Could not reach GitHub |
| Pagination safety cap reached | 422 | Account exceeds the configured repository listing limit |

### 8.1 Rate-limit detection

A GitHub 403 is treated as rate limiting when either:

- `X-RateLimit-Remaining` is `0`, or
- `Retry-After` is present (secondary rate-limit signal).

An explicit GitHub 429 is always treated as rate limiting. The handler returns a `Retry-After` response header when it can derive a positive delay:

1. Prefer GitHub's `Retry-After` header.
2. Otherwise calculate the delay from `X-RateLimit-Reset`.
3. If neither value is usable, omit the response header.

A normal permission-denied 403 remains 403 and is not misreported as a rate limit.

### 8.2 Invalid-token cleanup

Only GitHub 401 triggers authorized-client cleanup:

1. The handler checks that the request principal is an authenticated Spring `Authentication`.
2. It removes the authorized client for registration ID `github` and that specific principal.
3. It returns HTTP 401 with a `reauthorizeUrl` property set to `/oauth2/authorization/github`.

Other users' authorized clients are not removed. A cleanup failure does not change the 401 response. 403, 429, 5xx, network failures, and pagination-limit errors do not trigger cleanup.

Example response shape:

```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Your GitHub connection is invalid or has been revoked. Please sign in with GitHub again.",
  "reauthorizeUrl": "/oauth2/authorization/github"
}
```

### 8.3 Sensitive-data handling

The handler intentionally does not return GitHub's upstream response body, exception messages, access tokens, or stack traces. HTTP client exception messages can embed upstream response content, so logs record status codes or exception class names rather than raw upstream bodies. The handler also avoids allowing a cleanup exception to leak its message.

## 9. Configuration reference

| Property / environment variable | Default | Required | Description |
|---|---|---:|---|
| `GITHUB_CLIENT_ID` | None | Yes | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | None | Yes | GitHub OAuth App client secret |
| `GITHUB_OAUTH_SCOPE` | `read:user,repo` | No | Overrides OAuth scopes |
| `github.api.base-url` | `https://api.github.com` | No | GitHub API base URL |
| `github.api.max-pages` | `50` | No | Maximum repository pages fetched per request |

Relevant `application.properties` entries:

```properties
spring.application.name=TechDept365
spring.security.oauth2.client.registration.github.client-id=${GITHUB_CLIENT_ID}
spring.security.oauth2.client.registration.github.client-secret=${GITHUB_CLIENT_SECRET}
spring.security.oauth2.client.registration.github.client-authentication-method=client_secret_post
spring.security.oauth2.client.registration.github.scope=${GITHUB_OAUTH_SCOPE:read:user,repo}
github.api.max-pages=50
```

The GitHub API base URL can be overridden with `github.api.base-url` (the source currently relies on the bean's default rather than declaring it in `application.properties`).

Do not commit real credentials. For local development, define `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in the IDE Run Configuration or shell environment. A local `.env` file is not automatically loaded by Spring Boot unless a separate dotenv mechanism is configured.

## 10. Automated testing

### 10.1 Run the test suite

From the project root:

```bash
./mvnw test
```

To run a clean full Maven verification (compile, tests, and verification lifecycle):

```bash
./mvnw clean verify
```

On Windows, use `mvnw.cmd` instead of `./mvnw`.

The Spring Boot tests provide dummy OAuth client credentials through test properties. They do not require real GitHub credentials or a live GitHub API for the automated test suite.

### 10.2 Test classes and coverage

#### `TechDept365ApplicationTests`

- `contextLoads`: verifies that the Spring application context starts successfully.

#### `GithubOAuthScopeTest`

- `defaultScopeAllowsPrivateRepositoriesAndProfile`: verifies the default registration scopes include `read:user` and `repo`.
- This test is disabled when `GITHUB_OAUTH_SCOPE` is explicitly set, because the environment override changes the expected scope set.

#### `SecurityConfigTest`

Verifies the web security contract:

- Landing page is public and contains the GitHub login link and CSRF-protected logout form.
- Anonymous `/api/me` and `/api/repos` requests receive 401 instead of an OAuth redirect.
- Browser requests to protected non-API routes redirect to `/oauth2/authorization/github`.
- Non-browser requests to protected routes receive 401.
- OAuth authorization redirect contains the expected GitHub endpoint, client ID, state, scope, and callback URL.
- Default login flow requests the private-repository and profile scopes (disabled if an environment scope override is present).
- Logout without a CSRF token is rejected with 403.
- Logout with a CSRF token succeeds and redirects to `/`.

#### `GithubControllerTest`

Verifies controller behavior with a mocked `GithubService`:

- `/api/repos` passes the current authenticated user's GitHub access token to the service and serializes repository data.
- Anonymous repository requests return 401 and do not call the service.
- `/api/me` maps GitHub principal attributes to the API response.
- `/api/me` handles a GitHub user whose public `name` is missing.

#### `GithubServiceTest`

Verifies GitHub API request construction, DTO mapping, and pagination:

- Sends the bearer token and expected GitHub API headers.
- Maps GitHub JSON to `GithubRepo` and ignores unknown fields.
- Returns an empty list when the account has no repositories.
- Follows pages until a short page is received.
- Stops when an empty page follows a full page (including exact page-size multiples).
- Propagates an upstream 401 so the exception handler can process it.
- Throws the repository-limit exception when every permitted page is full.
- Returns successfully when the final allowed page is short.
- Rejects a non-positive configured page limit.
- Requests public and private repositories with the intended visibility and affiliation parameters.
- Returns public and private repositories together.
- Collects mixed public/private repositories across multiple pages.
- Does not expose or probe repositories beyond those returned by GitHub.
- Tolerates missing optional fields in GitHub's response.

#### `GithubExceptionHandlerTest`

Verifies HTTP status mapping and safe responses:

- Invalid/revoked token maps to 401 and includes the reauthorization URL.
- Genuine permission failure remains 403.
- Primary rate-limit 403 maps to 429 and derives `Retry-After` from the reset header.
- Secondary rate-limit 403 uses GitHub's `Retry-After` header.
- Explicit 429 maps to 429 even without rate-limit headers.
- Malformed rate-limit headers do not break handling.
- GitHub server errors map to 502.
- Unexpected GitHub client errors map to 502.
- Non-timeout network failures map to 502.
- Read and connection timeouts map to 504.
- Repository pagination-limit errors map to 422 and include the limit in the detail.
- Responses do not expose GitHub response bodies or exception details.

#### `GithubExceptionHandlerCleanupTest`

Verifies cleanup behavior in isolation:

- A GitHub 401 removes the current user's GitHub authorized client.
- Cleanup failure does not change the response or expose secret material.
- Missing or non-Authentication principals do not trigger cleanup.
- A genuine 403 does not trigger cleanup.
- 429 and rate-limited 403 do not trigger cleanup.
- GitHub 5xx and other 4xx do not trigger cleanup.
- Timeouts and repository-limit errors do not trigger cleanup.

#### `AuthorizedClientCleanupIntegrationTest`

Uses the application's real authorized-client repository implementation to verify user isolation:

- A GitHub 401 removes Alice's authorized client while Bob's remains intact.
- The removed client cannot be loaded for the next request; repeated cleanup is harmless.
- A fresh authorization can store a new token after cleanup.
- Statuses other than 401 leave both users' authorized clients in place.

### 10.3 What the automated tests do not prove

The automated tests use mocked GitHub service behavior or synthetic Spring Security principals/authorized clients. They verify application logic and the configured security contract, but they do not prove that:

- The real GitHub OAuth App credentials are valid.
- GitHub consent screens and organization approval workflows behave as expected for every account.
- A particular user's private or organization repositories are visible under that user's real GitHub permissions.
- GitHub's live API is available or has a particular rate-limit state.

Those cases require the manual integration checks below.

## 11. Manual integration test plan

Run the application with valid OAuth App credentials and test in a browser. Do not paste access tokens, client secrets, or one-time authorization codes into logs, chat, or screenshots.

### 11.1 Configuration and login

1. Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in the run environment.
2. Confirm the GitHub OAuth App callback URL matches the application's callback, typically `http://localhost:8080/login/oauth2/code/github` when running on port 8080. If the application uses another port or host, configure the matching callback URL in GitHub and the corresponding redirect URI in the app.
3. Start the application.
4. Open `/` and click **Sign in with GitHub**.
5. Confirm GitHub displays the expected permissions and complete authorization.
6. Confirm the browser returns to the application and the session is authenticated.

Expected: login completes without `/login?error`; `/api/me` and `/api/repos` can be called in the authenticated session.

### 11.2 Profile endpoint

1. While logged in, request `GET /api/me`.
2. Compare `login`, `name`, `avatarUrl`, and `profileUrl` with the GitHub account.
3. Test with an account that has no public profile name if available.

Expected: the profile fields map correctly; an absent name does not cause a server error.

### 11.3 Repository visibility

1. Use an account with at least one public repository and one private repository.
2. Request `GET /api/repos`.
3. Confirm both repository types appear when the token has the required scope and account access.
4. Confirm the response includes repository metadata such as `full_name`, `private`, URLs, default branch, and timestamps where supplied.

Expected: the service returns repositories GitHub exposes to the authorized token.

### 11.4 Organization repositories

1. Sign in with an account that belongs to an organization with repositories.
2. Check whether the expected organization repositories appear.
3. If private organization repositories are missing, check the organization's third-party OAuth App access policy and SAML SSO authorization.
4. Where approval is required, ask an organization owner to approve the OAuth App and/or complete the SSO authorization, then sign in again and retest.

Expected: only repositories visible to the GitHub token appear. Missing organization repositories may be caused by GitHub organization policy rather than this service.

### 11.5 User isolation

1. Sign in as one GitHub user and record the repositories returned.
2. Sign out.
3. Sign in as a different GitHub user in a separate browser profile/session.
4. Request `/api/repos` again.

Expected: the second user receives repositories visible to their own GitHub authorization, not the first user's list.

### 11.6 Revoked authorization and reauthorization

1. Revoke the application's authorization from the GitHub account settings.
2. With the application session still present, call `GET /api/repos`.
3. Confirm GitHub's 401 is translated to an application 401 with a `reauthorizeUrl` property.
4. Follow `/oauth2/authorization/github` and approve the app again.
5. Retry `GET /api/repos`.

Expected: the invalid authorized client is removed for that user; a new login establishes a fresh authorization and repository listing works again.

### 11.7 Anonymous access and logout

1. Open `/api/me` and `/api/repos` in a logged-out session.
2. Open a protected browser page with an HTML Accept header, if one exists.
3. Use the logout form on `/`.

Expected: API requests receive 401; browser navigation to protected HTML routes initiates GitHub login; logout succeeds with its CSRF token. A POST to `/logout` without a CSRF token should be rejected.

### 11.8 Pagination boundary behavior

The automated service tests cover pagination boundaries. To exercise the live behavior, use a test account with enough repositories or a lower temporary `github.api.max-pages` setting in a controlled environment.

Expected: pages are collected until a short or empty page. If every page up to the configured cap is full, the service returns 422 rather than silently returning a truncated result.

## 12. Operational and security considerations

- Keep OAuth client credentials outside source control.
- Use HTTPS outside local development; OAuth tokens and authenticated sessions are sensitive.
- Never log access tokens, authorization codes, raw GitHub error bodies, or exception messages that may embed upstream responses.
- Treat the `repo` scope as high impact because it includes write permissions for private repositories under an OAuth App.
- Keep the repository pagination cap enabled to bound request count and response size.
- Monitor 429 responses and respect `Retry-After` when supplied.
- The current in-memory/default session approach is suitable only for the current deployment assumptions; revisit before horizontal scaling.
- The current service does not yet download repository contents. Before implementing source-code analysis, revisit the permission model and consider a GitHub App with read-only Contents access and appropriately scoped installation permissions.

## 13. Current limitations and next boundary

The current service provides authentication, profile retrieval, and repository discovery. It does not yet provide:

- A repository detail/overview endpoint for one selected repository.
- Repository selection persistence or confirmation state.
- Clone/download/archive retrieval of repository contents.
- Branch selection or commit pinning for reproducible analysis.
- Analysis-job creation, queueing, status, or cancellation.
- Database persistence for selected repositories or GitHub connection metadata beyond Spring Security's current authorized-client/session handling.

The next planned feature can build on the returned `GithubRepo` data: repository selection, metadata overview, user confirmation, and only then initiation of the analysis workflow.

## 14. Source files

```text
src/main/java/com/example/TechDept365/
├── TechDept365Application.java
├── config/
│   ├── GithubClientConfig.java
│   └── SecurityConfig.java
├── controller/
│   ├── GithubController.java
│   └── HomeController.java
├── dto/
│   └── GithubRepo.java
├── exception/
│   └── RepositoryLimitExceededException.java
├── service/
│   └── GithubService.java
└── web/
    └── GithubExceptionHandler.java

src/test/java/com/example/TechDept365/
├── TechDept365ApplicationTests.java
├── config/
│   ├── GithubOAuthScopeTest.java
│   └── SecurityConfigTest.java
├── controller/
│   └── GithubControllerTest.java
├── service/
│   └── GithubServiceTest.java
└── web/
    ├── AuthorizedClientCleanupIntegrationTest.java
    ├── GithubExceptionHandlerCleanupTest.java
    └── GithubExceptionHandlerTest.java
```
