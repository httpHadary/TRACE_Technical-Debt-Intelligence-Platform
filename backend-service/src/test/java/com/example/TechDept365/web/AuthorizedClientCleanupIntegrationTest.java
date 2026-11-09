package com.example.TechDept365.web;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;
import org.springframework.security.oauth2.client.web.OAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

import java.net.http.HttpTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Uses the application's REAL authorized-client storage (whatever Spring Boot wires up) to prove
 * that a GitHub 401 removes only the current user's client and nothing else does.
 */
@SpringBootTest(properties = {
        "spring.security.oauth2.client.registration.github.client-id=test-id",
        "spring.security.oauth2.client.registration.github.client-secret=test-secret"
})
class AuthorizedClientCleanupIntegrationTest {

    @Autowired GithubExceptionHandler handler;
    @Autowired OAuth2AuthorizedClientRepository repository;
    @Autowired ClientRegistrationRepository registrations;

    private Authentication alice;
    private Authentication bob;

    @BeforeEach
    void storeClientsForTwoUsers() {
        alice = UsernamePasswordAuthenticationToken.authenticated("alice", "n/a", List.of());
        bob = UsernamePasswordAuthenticationToken.authenticated("bob", "n/a", List.of());
        store(alice);
        store(bob);
    }

    @Test
    void github401RemovesOnlyTheCurrentUsersAuthorizedClient() {
        assertThat(load(alice)).isNotNull();

        handler.unauthorized(unauthorized(), alice, new MockHttpServletRequest(), new MockHttpServletResponse());

        assertThat(load(alice)).isNull();
        OAuth2AuthorizedClient bobsClient = load(bob);
        assertThat(bobsClient).isNotNull();
        assertThat(bobsClient.getAccessToken().getTokenValue()).isEqualTo("token-of-bob");
    }

    @Test
    void theRemovedClientCannotBeReusedByTheNextRequest() {
        handler.unauthorized(unauthorized(), alice, new MockHttpServletRequest(), new MockHttpServletResponse());

        // What @RegisteredOAuth2AuthorizedClient("github") would look up on the next request:
        assertThat(load(alice)).isNull();

        // A second 401 for the same user is harmless (idempotent cleanup).
        handler.unauthorized(unauthorized(), alice, new MockHttpServletRequest(), new MockHttpServletResponse());
        assertThat(load(alice)).isNull();
        assertThat(load(bob)).isNotNull();
    }

    @Test
    void aFreshAuthorizationAfterCleanupStoresANewToken() {
        handler.unauthorized(unauthorized(), alice, new MockHttpServletRequest(), new MockHttpServletResponse());
        assertThat(load(alice)).isNull();

        store(alice, "fresh-token-of-alice"); // what a new GitHub login does

        assertThat(load(alice).getAccessToken().getTokenValue()).isEqualTo("fresh-token-of-alice");
    }

    @Test
    void statusesOtherThan401LeaveTheAuthorizedClientInPlace() {
        handler.forbiddenOrRateLimited(clientError(HttpStatus.FORBIDDEN));
        handler.forbiddenOrRateLimited(clientError(HttpStatus.TOO_MANY_REQUESTS));
        handler.upstreamFailure(HttpServerErrorException.create(HttpStatus.BAD_GATEWAY, "Bad Gateway",
                new HttpHeaders(), new byte[0], StandardCharsets.UTF_8));
        handler.network(new ResourceAccessException("t", new HttpTimeoutException("request timed out")));

        assertThat(load(alice)).isNotNull();
        assertThat(load(bob)).isNotNull();
    }

    // ---- helpers ----

    private void store(Authentication user) {
        store(user, "token-of-" + user.getName());
    }

    private void store(Authentication user, String tokenValue) {
        ClientRegistration github = registrations.findByRegistrationId("github");
        OAuth2AccessToken token = new OAuth2AccessToken(OAuth2AccessToken.TokenType.BEARER, tokenValue,
                Instant.now(), Instant.now().plusSeconds(3600), Set.of("repo", "read:user"));
        repository.saveAuthorizedClient(new OAuth2AuthorizedClient(github, user.getName(), token),
                user, new MockHttpServletRequest(), new MockHttpServletResponse());
    }

    private OAuth2AuthorizedClient load(Authentication user) {
        return repository.loadAuthorizedClient("github", user, new MockHttpServletRequest());
    }

    private static HttpClientErrorException.Unauthorized unauthorized() {
        return (HttpClientErrorException.Unauthorized) clientError(HttpStatus.UNAUTHORIZED);
    }

    private static HttpClientErrorException clientError(HttpStatus status) {
        return HttpClientErrorException.create(status, status.getReasonPhrase(), new HttpHeaders(),
                new byte[0], StandardCharsets.UTF_8);
    }
}
