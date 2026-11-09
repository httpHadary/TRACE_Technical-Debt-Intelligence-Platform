package com.example.TechDept365.web;

import com.example.TechDept365.exception.RepositoryLimitExceededException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.web.OAuth2AuthorizedClientRepository;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

import java.net.http.HttpTimeoutException;
import java.nio.charset.StandardCharsets;
import java.security.Principal;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.verifyNoMoreInteractions;

/**
 * Plain unit tests (no Spring context): exactly WHEN the handler removes the stored GitHub
 * authorized client, and with which arguments.
 */
class GithubExceptionHandlerCleanupTest {

    private OAuth2AuthorizedClientRepository repository;
    private GithubExceptionHandler handler;
    private MockHttpServletRequest request;
    private MockHttpServletResponse response;
    private Authentication alice;

    @BeforeEach
    void setUp() {
        repository = mock(OAuth2AuthorizedClientRepository.class);
        handler = new GithubExceptionHandler(repository);
        request = new MockHttpServletRequest();
        response = new MockHttpServletResponse();
        alice = UsernamePasswordAuthenticationToken.authenticated("alice", "n/a", List.of());
    }

    // ---- 401 removes the current user's github client ----

    @Test
    void github401RemovesTheCurrentUsersGithubAuthorizedClient() {
        ResponseEntity<ProblemDetail> result = handler.unauthorized(unauthorized(), alice, request, response);

        verify(repository).removeAuthorizedClient("github", alice, request, response);
        verifyNoMoreInteractions(repository);
        assertThat(result.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        assertThat(result.getBody().getProperties()).containsEntry("reauthorizeUrl", "/oauth2/authorization/github");
    }

    @Test
    void cleanupFailureDoesNotChangeTheResponse() {
        doThrow(new IllegalStateException("storage exploded with token=secret-token-value"))
                .when(repository).removeAuthorizedClient(anyString(), any(), any(), any());

        ResponseEntity<ProblemDetail> result = handler.unauthorized(unauthorized(), alice, request, response);

        assertThat(result.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
        assertThat(result.getBody().getDetail()).doesNotContain("secret-token-value");
    }

    @Test
    void noAuthenticatedUserMeansNothingToCleanUp() {
        handler.unauthorized(unauthorized(), null, request, response);

        verifyNoInteractions(repository);
    }

    @Test
    void aPrincipalThatIsNotAnAuthenticationIsIgnored() {
        Principal plain = () -> "someone";

        handler.unauthorized(unauthorized(), plain, request, response);

        verifyNoInteractions(repository);
    }

    // ---- everything else must NOT trigger cleanup ----

    @Test
    void forbiddenDoesNotTriggerCleanup() {
        ResponseEntity<ProblemDetail> result = handler.forbiddenOrRateLimited(clientError(HttpStatus.FORBIDDEN, new HttpHeaders()));

        assertThat(result.getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        verifyNoInteractions(repository);
    }

    @Test
    void rateLimited429DoesNotTriggerCleanup() {
        ResponseEntity<ProblemDetail> result = handler.forbiddenOrRateLimited(clientError(HttpStatus.TOO_MANY_REQUESTS, new HttpHeaders()));

        assertThat(result.getStatusCode()).isEqualTo(HttpStatus.TOO_MANY_REQUESTS);
        verifyNoInteractions(repository);
    }

    @Test
    void rateLimited403DoesNotTriggerCleanup() {
        HttpHeaders h = new HttpHeaders();
        h.add("X-RateLimit-Remaining", "0");
        ResponseEntity<ProblemDetail> result = handler.forbiddenOrRateLimited(clientError(HttpStatus.FORBIDDEN, h));

        assertThat(result.getStatusCode()).isEqualTo(HttpStatus.TOO_MANY_REQUESTS);
        verifyNoInteractions(repository);
    }

    @Test
    void githubServerErrorDoesNotTriggerCleanup() {
        HttpServerErrorException ex = HttpServerErrorException.create(HttpStatus.SERVICE_UNAVAILABLE,
                "Service Unavailable", new HttpHeaders(), new byte[0], StandardCharsets.UTF_8);

        assertThat(handler.upstreamFailure(ex).getStatusCode()).isEqualTo(HttpStatus.BAD_GATEWAY);
        verifyNoInteractions(repository);
    }

    @Test
    void otherClientErrorsDoNotTriggerCleanup() {
        assertThat(handler.unexpectedClientError(clientError(HttpStatus.NOT_FOUND, new HttpHeaders())).getStatusCode())
                .isEqualTo(HttpStatus.BAD_GATEWAY);
        verifyNoInteractions(repository);
    }

    @Test
    void timeoutsAndLimitErrorsDoNotTriggerCleanup() {
        handler.network(new ResourceAccessException("t", new HttpTimeoutException("request timed out")));
        handler.tooManyRepositories(new RepositoryLimitExceededException(5000));

        verifyNoInteractions(repository);
    }

    // ---- helpers ----

    private static HttpClientErrorException.Unauthorized unauthorized() {
        return (HttpClientErrorException.Unauthorized) clientError(HttpStatus.UNAUTHORIZED, new HttpHeaders());
    }

    private static HttpClientErrorException clientError(HttpStatus status, HttpHeaders headers) {
        return HttpClientErrorException.create(status, status.getReasonPhrase(), headers,
                "{\"message\":\"upstream-body\"}".getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8);
    }
}
