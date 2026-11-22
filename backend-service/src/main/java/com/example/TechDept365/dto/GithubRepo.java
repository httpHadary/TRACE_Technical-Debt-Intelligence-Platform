package com.example.TechDept365.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.List;

/** Subset of the fields GitHub returns from GET /user/repos. */
@JsonIgnoreProperties(ignoreUnknown = true)
public record GithubRepo(
        long id,
        String name,
        @JsonProperty("full_name") String fullName,
        String description,
        @JsonProperty("html_url") String htmlUrl,
        @JsonProperty("clone_url") String cloneUrl,
        @JsonProperty("ssh_url") String sshUrl,
        @JsonProperty("private") Boolean isPrivate,
        Boolean fork,
        Boolean archived,
        String language,
        List<String> topics,
        @JsonProperty("stargazers_count") Integer stars,
        @JsonProperty("forks_count") Integer forks,
        @JsonProperty("open_issues_count") Integer openIssues,
        @JsonProperty("default_branch") String defaultBranch,
        String visibility,
        @JsonProperty("created_at") Instant createdAt,
        @JsonProperty("updated_at") Instant updatedAt,
        @JsonProperty("pushed_at") Instant pushedAt,
        Owner owner
) {
    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Owner(String login, @JsonProperty("html_url") String htmlUrl) {}
}
