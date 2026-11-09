package com.example.TechDept365.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UriUtils;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oauth2Login;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
        "spring.security.oauth2.client.registration.github.client-id=test-id",
        "spring.security.oauth2.client.registration.github.client-secret=test-secret"
})
@AutoConfigureMockMvc
class SecurityConfigTest {

    @Autowired MockMvc mvc;

    @Test
    void homePageIsPublicAndContainsLoginLinkAndCsrfProtectedLogoutForm() throws Exception {
        mvc.perform(get("/"))
                .andExpect(status().isOk())
                .andExpect(content().string(org.hamcrest.Matchers.containsString("/oauth2/authorization/github")))
                .andExpect(content().string(org.hamcrest.Matchers.containsString("name=\"_csrf\"")));
    }

    @Test
    void apiEndpointsReturn401InsteadOfRedirectingForAnonymousUsers() throws Exception {
        mvc.perform(get("/api/me")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/repos")).andExpect(status().isUnauthorized());
    }

    @Test
    void otherProtectedPathsRedirectBrowsersToGithubLogin() throws Exception {
        mvc.perform(get("/some-protected-page").accept(MediaType.TEXT_HTML))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/oauth2/authorization/github"));
    }

    @Test
    void nonBrowserClientsGet401InsteadOfARedirectOnOtherProtectedPaths() throws Exception {
        // No Accept: text/html header => not a browser => plain 401 rather than a redirect to github.com
        mvc.perform(get("/some-protected-page"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void loginEndpointRedirectsToGithubWithClientIdStateAndScopes() throws Exception {
        MvcResult result = mvc.perform(get("/oauth2/authorization/github"))
                .andExpect(status().is3xxRedirection())
                .andReturn();

        String location = result.getResponse().getRedirectedUrl();
        assertThat(location)
                .startsWith("https://github.com/login/oauth/authorize")
                .contains("client_id=test-id")
                .contains("state=")
                .contains("scope=")
                .contains("redirect_uri=http://localhost/login/oauth2/code/github");
    }

    @Test
    @DisabledIfEnvironmentVariable(named = "GITHUB_OAUTH_SCOPE", matches = ".+")
    void loginFlowRequestsTheScopeNeededForPrivateRepositories() throws Exception {
        MvcResult result = mvc.perform(get("/oauth2/authorization/github"))
                .andExpect(status().is3xxRedirection())
                .andReturn();

        String rawScope = UriComponentsBuilder.fromUriString(result.getResponse().getRedirectedUrl())
                .build().getQueryParams().getFirst("scope");
        String scope = UriUtils.decode(rawScope, StandardCharsets.UTF_8);

        assertThat(Arrays.asList(scope.split("[ ,]+"))).contains("repo", "read:user");
    }

    @Test
    void logoutWithoutCsrfTokenIsRejected() throws Exception {
        mvc.perform(post("/logout").with(oauth2Login()))
                .andExpect(status().isForbidden());
    }

    @Test
    void logoutWithCsrfTokenRedirectsHome() throws Exception {
        mvc.perform(post("/logout").with(oauth2Login()).with(csrf()))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/"));
    }
}
