package com.example.TechDept365.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.DisabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.registration.ClientRegistrationRepository;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(properties = {
        "spring.security.oauth2.client.registration.github.client-id=test-id",
        "spring.security.oauth2.client.registration.github.client-secret=test-secret"
})
class GithubOAuthScopeTest {

    @Autowired ClientRegistrationRepository registrations;

    @Test
    @DisabledIfEnvironmentVariable(named = "GITHUB_OAUTH_SCOPE", matches = ".+") // env override changes the default
    void defaultScopeAllowsPrivateRepositoriesAndProfile() {
        ClientRegistration github = registrations.findByRegistrationId("github");

        assertThat(github.getScopes()).containsExactlyInAnyOrder("read:user", "repo");
    }
}
