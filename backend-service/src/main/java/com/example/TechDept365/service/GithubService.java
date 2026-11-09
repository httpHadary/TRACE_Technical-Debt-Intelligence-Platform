package com.example.TechDept365.service;

import com.example.TechDept365.dto.GithubRepo;
import com.example.TechDept365.exception.RepositoryLimitExceededException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.ArrayList;
import java.util.List;

@Service
public class GithubService {

    private static final int PER_PAGE = 100; // GitHub's maximum

    private final RestClient client;
    private final int maxPages;

    public GithubService(RestClient githubRestClient,
                         @Value("${github.api.max-pages:50}") int maxPages) {
        if (maxPages < 1) {
            throw new IllegalArgumentException("github.api.max-pages must be at least 1");
        }
        this.client = githubRestClient;
        this.maxPages = maxPages;
    }

    /**
     * Fetches every repo the token's user owns, collaborates on, or can access via an org.
     * Pages are fetched sequentially; at most {@code maxPages} requests are made.
     *
     * @throws RepositoryLimitExceededException if every allowed page was full, i.e. more
     *         repositories may exist than the limit lets us fetch. We fail instead of silently
     *         returning a truncated list. (An account with exactly maxPages * 100 repositories
     *         is also rejected; the limit is a safety cap, not an exact count.)
     */
    public List<GithubRepo> fetchAllRepos(String accessToken) {
        List<GithubRepo> allRepos = new ArrayList<>();

        for (int page = 1; page <= maxPages; page++) {
            final int currentPage = page;

            List<GithubRepo> batch = client.get()
                    .uri(uri -> uri.path("/user/repos")
                            .queryParam("per_page", PER_PAGE)
                            .queryParam("page", currentPage)
                            .queryParam("sort", "updated")
                            // Public + private, only what the token's user/app authorization can see.
                            // GitHub enforces access: repos the user cannot access are never returned.
                            .queryParam("visibility", "all")
                            .queryParam("affiliation", "owner,collaborator,organization_member")
                            .build())
                    .headers(h -> h.setBearerAuth(accessToken))
                    .retrieve()
                    .body(new ParameterizedTypeReference<List<GithubRepo>>() {});

            if (batch == null || batch.isEmpty()) return allRepos;

            allRepos.addAll(batch);

            if (batch.size() < PER_PAGE) return allRepos; // last page
        }

        // Every allowed page came back full: there may be more repositories we will not fetch.
        throw new RepositoryLimitExceededException(maxPages * PER_PAGE);
    }
}
