package com.example.TechDept365.controller;

import com.example.TechDept365.dto.GithubRepo;
import com.example.TechDept365.service.GithubService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.List;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oauth2Client;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oauth2Login;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
        "spring.security.oauth2.client.registration.github.client-id=test-id",
        "spring.security.oauth2.client.registration.github.client-secret=test-secret"
})
@AutoConfigureMockMvc
class GithubControllerTest {

    @Autowired MockMvc mvc;
    @MockitoBean GithubService githubService;

    @Test
    void reposReturnsTheLoggedInUsersRepos_usingThatUsersToken() throws Exception {
        OAuth2AccessToken token = new OAuth2AccessToken(
                OAuth2AccessToken.TokenType.BEARER, "alice-token",
                Instant.now(), Instant.now().plusSeconds(3600));
        when(githubService.fetchAllRepos("alice-token")).thenReturn(List.of(sampleRepo()));

        mvc.perform(get("/api/repos")
                        .with(oauth2Login())
                        .with(oauth2Client("github").accessToken(token)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].full_name").value("octocat/hello"))
                .andExpect(jsonPath("$[0].html_url").value("https://github.com/octocat/hello"))
                .andExpect(jsonPath("$[0].private").value(false))
                .andExpect(jsonPath("$[0].stargazers_count").value(5));

        verify(githubService).fetchAllRepos("alice-token");
    }

    @Test
    void reposRejectsAnonymousWith401_andNeverCallsGithub() throws Exception {
        mvc.perform(get("/api/repos")).andExpect(status().isUnauthorized());
        verifyNoInteractions(githubService);
    }

    @Test
    void meReturnsProfileFromGithubAttributes() throws Exception {
        mvc.perform(get("/api/me").with(oauth2Login().attributes(a -> {
                    a.put("login", "octocat");
                    a.put("name", "The Octocat");
                    a.put("avatar_url", "https://avatars.githubusercontent.com/u/1");
                    a.put("html_url", "https://github.com/octocat");
                })))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.login").value("octocat"))
                .andExpect(jsonPath("$.name").value("The Octocat"))
                .andExpect(jsonPath("$.profileUrl").value("https://github.com/octocat"));
    }

    @Test
    void meHandlesGithubUsersWithoutAPublicName() throws Exception {
        mvc.perform(get("/api/me").with(oauth2Login().attributes(a -> a.put("login", "anon"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.login").value("anon"))
                .andExpect(jsonPath("$.name").doesNotExist());
    }

    private static GithubRepo sampleRepo() {
        return new GithubRepo(1L, "hello", "octocat/hello", "demo",
                "https://github.com/octocat/hello",
                "https://github.com/octocat/hello.git",
                "git@github.com:octocat/hello.git",
                false, false, false, "Java", List.of("spring"),
                5, 1, 0, "main", "public",
                Instant.parse("2024-01-01T00:00:00Z"),
                Instant.parse("2024-06-01T00:00:00Z"),
                Instant.parse("2024-06-01T00:00:00Z"),
                new GithubRepo.Owner("octocat", "https://github.com/octocat"));
    }
}
