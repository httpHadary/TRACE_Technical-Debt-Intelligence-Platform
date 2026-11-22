package com.example.TechDept365.web;

import com.example.TechDept365.exception.RepositoryLimitExceededException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.web.OAuth2AuthorizedClientRepository;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

import java.net.SocketTimeoutException;
import java.net.http.HttpTimeoutException;
import java.security.Principal;
import java.time.Instant;

/**
 * Maps GitHub API failures to safe, consistent RFC 9457 problem responses.
 *
 * Responses never contain GitHub's response body, exception messages, tokens or stack traces
 * (Spring's exception messages for HTTP client errors embed the upstream body, so they are
 * deliberately not logged or returned either: only status codes are logged).
 *
 * A GitHub 401 additionally removes the CURRENT user's stored GitHub authorized client, so the
 * revoked token is never reused. No other status triggers cleanup.
 */
@RestControllerAdvice
public class GithubExceptionHandler {

    /** Must match spring.security.oauth2.client.registration.<id> */
    static final String REGISTRATION_ID = "github";
    /** Spring Security's built-in endpoint that starts a fresh GitHub OAuth flow. */
    static final String REAUTHORIZE_URL = "/oauth2/authorization/" + REGISTRATION_ID;

    private static final Logger log = LoggerFactory.getLogger(GithubExceptionHandler.class);

    private final OAuth2AuthorizedClientRepository authorizedClientRepository;

    public GithubExceptionHandler(OAuth2AuthorizedClientRepository authorizedClientRepository) {
        this.authorizedClientRepository = authorizedClientRepository;
    }

    /**
     * The user's GitHub token is invalid, expired or revoked. Remove that user's stored GitHub
     * authorized client (only theirs, only for the "github" registration) and tell the client to
     * re-establish the GitHub connection.
     */
    @ExceptionHandler(HttpClientErrorException.Unauthorized.class)
    ResponseEntity<ProblemDetail> unauthorized(HttpClientErrorException.Unauthorized ex,
                                               Principal principal,
                                               HttpServletRequest request,
                                               HttpServletResponse response) {
        log.warn("GitHub rejected the access token (401)");
        removeCurrentUsersAuthorizedClient(principal, request, response);

        ProblemDetail body = ProblemDetail.forStatusAndDetail(HttpStatus.UNAUTHORIZED,
                "Your GitHub connection is invalid or has been revoked. Please sign in with GitHub again.");
        body.setProperty("reauthorizeUrl", REAUTHORIZE_URL);
        return respond(body, null);
    }

    /** GitHub signals rate limiting with 403 or 429; every other 403 is a genuine permission failure. */
    @ExceptionHandler({HttpClientErrorException.Forbidden.class, HttpClientErrorException.TooManyRequests.class})
    ResponseEntity<ProblemDetail> forbiddenOrRateLimited(HttpClientErrorException ex) {
        int status = ex.getStatusCode().value();
        HttpHeaders headers = ex.getResponseHeaders();
        if (isRateLimited(status, headers)) {
            log.warn("GitHub rate limit reached (status {})", status);
            return problem(HttpStatus.TOO_MANY_REQUESTS,
                    "GitHub rate limit reached. Please try again later.", retryAfterSeconds(headers));
        }
        log.warn("GitHub denied access (status {})", status);
        return problem(HttpStatus.FORBIDDEN, "GitHub denied access to the requested resource.", null);
    }

    /** Any other 4xx from GitHub means our request was not acceptable: an upstream problem, not the user's. */
    @ExceptionHandler(HttpClientErrorException.class)
    ResponseEntity<ProblemDetail> unexpectedClientError(HttpClientErrorException ex) {
        log.warn("GitHub returned an unexpected client error (status {})", ex.getStatusCode().value());
        return problem(HttpStatus.BAD_GATEWAY, "GitHub returned an unexpected response.", null);
    }

    /** GitHub itself is failing (5xx). */
    @ExceptionHandler(HttpServerErrorException.class)
    ResponseEntity<ProblemDetail> upstreamFailure(HttpServerErrorException ex) {
        log.warn("GitHub returned a server error (status {})", ex.getStatusCode().value());
        return problem(HttpStatus.BAD_GATEWAY, "GitHub is currently unavailable.", null);
    }

    /** Connect/read timeouts become 504; other network failures (DNS, refused connection) become 502. */
    @ExceptionHandler(ResourceAccessException.class)
    ResponseEntity<ProblemDetail> network(ResourceAccessException ex) {
        if (isTimeout(ex)) {
            log.warn("Timed out calling GitHub");
            return problem(HttpStatus.GATEWAY_TIMEOUT, "GitHub did not respond in time.", null);
        }
        log.warn("Network error calling GitHub ({})", ex.getCause() == null ? "unknown" : ex.getCause().getClass().getSimpleName());
        return problem(HttpStatus.BAD_GATEWAY, "Could not reach GitHub.", null);
    }

    /** The account has more repositories than the configured pagination limit allows us to fetch. */
    @ExceptionHandler(RepositoryLimitExceededException.class)
    ResponseEntity<ProblemDetail> tooManyRepositories(RepositoryLimitExceededException ex) {
        log.warn("Repository pagination limit reached (limit {})", ex.getLimit());
        return problem(HttpStatus.UNPROCESSABLE_ENTITY,
                "This account has more repositories than this service can list (limit: " + ex.getLimit() + ").", null);
    }

    // ---- cleanup ----

    private void removeCurrentUsersAuthorizedClient(Principal principal,
                                                    HttpServletRequest request,
                                                    HttpServletResponse response) {
        if (!(principal instanceof Authentication authentication)) {
            return; // no authenticated user to clean up for
        }
        try {
            // Scoped to this one user + the "github" registration: other users are never touched.
            authorizedClientRepository.removeAuthorizedClient(REGISTRATION_ID, authentication, request, response);
        } catch (RuntimeException e) {
            // Never let cleanup failure change the response; log the type only (no tokens/messages).
            log.warn("Could not remove the invalid GitHub authorized client ({})", e.getClass().getSimpleName());
        }
    }

    // ---- helpers ----

    private static boolean isRateLimited(int status, HttpHeaders headers) {
        if (status == HttpStatus.TOO_MANY_REQUESTS.value()) return true;
        if (headers == null) return false;
        return "0".equals(headers.getFirst("X-RateLimit-Remaining"))
                || headers.getFirst(HttpHeaders.RETRY_AFTER) != null; // secondary rate limit
    }

    /** Seconds to wait: GitHub's Retry-After if present, otherwise derived from X-RateLimit-Reset. */
    private static Long retryAfterSeconds(HttpHeaders headers) {
        if (headers == null) return null;
        Long retryAfter = parseLong(headers.getFirst(HttpHeaders.RETRY_AFTER));
        if (retryAfter != null && retryAfter > 0) return retryAfter;
        Long reset = parseLong(headers.getFirst("X-RateLimit-Reset"));
        if (reset != null) return Math.max(1, reset - Instant.now().getEpochSecond());
        return null;
    }

    private static Long parseLong(String value) {
        if (value == null) return null;
        try {
            return Long.parseLong(value.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static boolean isTimeout(Throwable ex) {
        for (Throwable t = ex; t != null; t = t.getCause()) {
            if (t instanceof SocketTimeoutException || t instanceof HttpTimeoutException) return true;
        }
        return false;
    }

    private static ResponseEntity<ProblemDetail> problem(HttpStatus status, String detail, Long retryAfterSeconds) {
        return respond(ProblemDetail.forStatusAndDetail(status, detail), retryAfterSeconds);
    }

    private static ResponseEntity<ProblemDetail> respond(ProblemDetail body, Long retryAfterSeconds) {
        ResponseEntity.BodyBuilder builder = ResponseEntity.status(body.getStatus())
                .contentType(MediaType.APPLICATION_PROBLEM_JSON);
        if (retryAfterSeconds != null) {
            builder.header(HttpHeaders.RETRY_AFTER, String.valueOf(retryAfterSeconds));
        }
        return builder.body(body);
    }
}
