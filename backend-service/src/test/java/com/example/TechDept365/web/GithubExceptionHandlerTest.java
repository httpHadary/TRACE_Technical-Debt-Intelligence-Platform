package com.example.TechDept365.web;

import com.example.TechDept365.exception.RepositoryLimitExceededException;
import com.example.TechDept365.service.GithubService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

import java.net.ConnectException;
import java.net.http.HttpConnectTimeoutException;
import java.net.http.HttpTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;

import static org.hamcrest.Matchers.not;
import static org.hamcrest.Matchers.containsString;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oauth2Client;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oauth2Login;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
        "spring.security.oauth2.client.registration.github.client-id=test-id",
        "spring.security.oauth2.client.registration.github.client-secret=test-secret"
})
@AutoConfigureMockMvc
class GithubExceptionHandlerTest {

    private static final String RAW_GITHUB_BODY = "{\"message\":\"internal-github-detail-do-not-leak\"}";

    @Autowired MockMvc mvc;
    @MockitoBean GithubService githubService;

    private ResultActions callRepos() throws Exception {
        return mvc.perform(get("/api/repos").with(oauth2Login()).with(oauth2Client("github")));
    }

    private static HttpClientErrorException clientError(HttpStatus status, HttpHeaders headers) {
        return HttpClientErrorException.create(status, status.getReasonPhrase(), headers,
                RAW_GITHUB_BODY.getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8);
    }

    // ---- 401 ----

    @Test
    void revokedOrInvalidTokenBecomes401() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.UNAUTHORIZED, new HttpHeaders()));

        callRepos().andExpect(status().isUnauthorized())
                .andExpect(content().contentTypeCompatibleWith("application/problem+json"))
                .andExpect(jsonPath("$.status").value(401))
                .andExpect(jsonPath("$.detail").value(containsString("again")))
                .andExpect(jsonPath("$.reauthorizeUrl").value("/oauth2/authorization/github"));
    }

    // ---- 403 vs 429 ----

    @Test
    void genuinePermissionFailureStays403() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.FORBIDDEN, new HttpHeaders()));

        callRepos().andExpect(status().isForbidden())
                .andExpect(jsonPath("$.status").value(403))
                .andExpect(header().doesNotExist("Retry-After"));
    }

    @Test
    void primaryRateLimit403Becomes429WithRetryAfterFromResetHeader() throws Exception {
        HttpHeaders h = new HttpHeaders();
        h.add("X-RateLimit-Remaining", "0");
        h.add("X-RateLimit-Reset", String.valueOf(Instant.now().getEpochSecond() + 120));
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.FORBIDDEN, h));

        callRepos().andExpect(status().isTooManyRequests())
                .andExpect(header().exists("Retry-After"))
                .andExpect(jsonPath("$.status").value(429));
    }

    @Test
    void secondaryRateLimitUsesGithubsRetryAfterHeader() throws Exception {
        HttpHeaders h = new HttpHeaders();
        h.add("Retry-After", "60");
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.FORBIDDEN, h));

        callRepos().andExpect(status().isTooManyRequests())
                .andExpect(header().string("Retry-After", "60"));
    }

    @Test
    void explicit429IsPassedThroughEvenWithoutRateLimitHeaders() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.TOO_MANY_REQUESTS, new HttpHeaders()));

        callRepos().andExpect(status().isTooManyRequests())
                .andExpect(header().doesNotExist("Retry-After"));
    }

    @Test
    void malformedRateLimitHeadersDoNotBreakTheHandler() throws Exception {
        HttpHeaders h = new HttpHeaders();
        h.add("X-RateLimit-Remaining", "0");
        h.add("X-RateLimit-Reset", "not-a-number");
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.FORBIDDEN, h));

        callRepos().andExpect(status().isTooManyRequests())
                .andExpect(header().doesNotExist("Retry-After"));
    }

    // ---- 502 ----

    @Test
    void githubServerErrorBecomes502() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(HttpServerErrorException.create(
                HttpStatus.SERVICE_UNAVAILABLE, "Service Unavailable", new HttpHeaders(),
                RAW_GITHUB_BODY.getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8));

        callRepos().andExpect(status().isBadGateway())
                .andExpect(jsonPath("$.status").value(502));
    }

    @Test
    void unexpectedGithubClientErrorBecomes502() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.NOT_FOUND, new HttpHeaders()));

        callRepos().andExpect(status().isBadGateway());
    }

    @Test
    void nonTimeoutNetworkFailureBecomes502() throws Exception {
        when(githubService.fetchAllRepos(any()))
                .thenThrow(new ResourceAccessException("refused", new ConnectException("Connection refused")));

        callRepos().andExpect(status().isBadGateway());
    }

    // ---- 504 ----

    @Test
    void readTimeoutBecomes504() throws Exception {
        when(githubService.fetchAllRepos(any()))
                .thenThrow(new ResourceAccessException("timeout", new HttpTimeoutException("request timed out")));

        callRepos().andExpect(status().isGatewayTimeout())
                .andExpect(jsonPath("$.status").value(504));
    }

    @Test
    void connectTimeoutBecomes504() throws Exception {
        when(githubService.fetchAllRepos(any()))
                .thenThrow(new ResourceAccessException("timeout", new HttpConnectTimeoutException("connect timed out")));

        callRepos().andExpect(status().isGatewayTimeout());
    }

    // ---- pagination limit ----

    @Test
    void repositoryLimitBecomes422WithTheLimit() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(new RepositoryLimitExceededException(5000));

        callRepos().andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.status").value(422))
                .andExpect(jsonPath("$.detail").value(containsString("5000")));
    }

    // ---- nothing sensitive leaks ----

    @Test
    void responsesNeverContainGithubBodyOrExceptionDetails() throws Exception {
        when(githubService.fetchAllRepos(any())).thenThrow(clientError(HttpStatus.UNAUTHORIZED, new HttpHeaders()));

        callRepos().andExpect(content().string(not(containsString("internal-github-detail"))))
                .andExpect(content().string(not(containsString("HttpClientErrorException"))))
                .andExpect(content().string(not(containsString("at com.example"))));
    }
}
