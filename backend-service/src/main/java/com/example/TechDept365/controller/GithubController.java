package com.example.TechDept365.controller;

import com.example.TechDept365.dto.GithubRepo;
import com.example.TechDept365.service.GithubService;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.annotation.RegisteredOAuth2AuthorizedClient;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class GithubController {

    private final GithubService githubService;

    public GithubController(GithubService githubService) {
        this.githubService = githubService;
    }

    /** Who is logged in (attributes come from GitHub's /user endpoint, loaded during login). */
    @GetMapping("/me")
    public Map<String, Object> me(@AuthenticationPrincipal OAuth2User user) {
        Map<String, Object> attrs = user.getAttributes();
        Map<String, Object> body = new LinkedHashMap<>(); // allows null values (GitHub "name" can be null)

        body.put("login", attrs.get("login"));
        body.put("name", attrs.get("name"));
        body.put("avatarUrl", attrs.get("avatar_url"));
        body.put("profileUrl", attrs.get("html_url"));
        return body;
    }

    /** All repos on the authenticated GitHub account, with details and URLs. */
    @GetMapping("/repos")
    public List<GithubRepo> repos(@RegisteredOAuth2AuthorizedClient("github") OAuth2AuthorizedClient client) {
        return githubService.fetchAllRepos(client.getAccessToken().getTokenValue());
    }
}
