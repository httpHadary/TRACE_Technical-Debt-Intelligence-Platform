package com.example.TechDept365.service;

import com.example.TechDept365.dto.GithubRepo;
import com.example.TechDept365.exception.RepositoryLimitExceededException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.hamcrest.Matchers.allOf;
import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withStatus;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class GithubServiceTest {

    private MockRestServiceServer server;
    private RestClient client;
    private GithubService service;

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder()
                .baseUrl("https://api.github.com")
                .defaultHeader(HttpHeaders.ACCEPT, "application/vnd.github+json")
                .defaultHeader("X-GitHub-Api-Version", "2022-11-28");
        server = MockRestServiceServer.bindTo(builder).build();
        client = builder.build();
        service = new GithubService(client, 50);
    }

    @Test
    void sendsBearerTokenAndGithubHeaders() {
        server.expect(requestTo(containsString("/user/repos")))
                .andExpect(method(HttpMethod.GET))
                .andExpect(header(HttpHeaders.AUTHORIZATION, "Bearer user-token"))
                .andExpect(header("X-GitHub-Api-Version", "2022-11-28"))
                .andRespond(withSuccess("[]", MediaType.APPLICATION_JSON));

        service.fetchAllRepos("user-token");

        server.verify();
    }

    @Test
    void mapsGithubJsonToRecord_andIgnoresUnknownFields() {
        server.expect(requestTo(containsString("/user/repos")))
                .andRespond(withSuccess("[" + repoJson(1) + "]", MediaType.APPLICATION_JSON));

        List<GithubRepo> repos = service.fetchAllRepos("t");

        assertThat(repos).hasSize(1);
        GithubRepo repo = repos.get(0);
        assertThat(repo.id()).isEqualTo(1);
        assertThat(repo.fullName()).isEqualTo("octocat/repo-1");
        assertThat(repo.htmlUrl()).isEqualTo("https://github.com/octocat/repo-1");
        assertThat(repo.isPrivate()).isTrue();
        assertThat(repo.stars()).isEqualTo(3);
        assertThat(repo.owner().login()).isEqualTo("octocat");
    }

    @Test
    void returnsEmptyListForAccountWithNoRepos() {
        server.expect(requestTo(containsString("/user/repos")))
                .andRespond(withSuccess("[]", MediaType.APPLICATION_JSON));

        assertThat(service.fetchAllRepos("t")).isEmpty();
    }

    @Test
    void followsPaginationUntilShortPage() {
        server.expect(requestTo(containsString("&page=1&")))
                .andRespond(withSuccess(repoArray(1, 100), MediaType.APPLICATION_JSON));
        server.expect(requestTo(containsString("&page=2&")))
                .andRespond(withSuccess(repoArray(101, 102), MediaType.APPLICATION_JSON));

        assertThat(service.fetchAllRepos("t")).hasSize(102);

        server.verify(); // exactly two calls, no third one
    }

    @Test
    void stopsOnEmptyPageWhenTotalIsExactMultipleOfPageSize() {
        server.expect(requestTo(containsString("&page=1&")))
                .andRespond(withSuccess(repoArray(1, 100), MediaType.APPLICATION_JSON));
        server.expect(requestTo(containsString("&page=2&")))
                .andRespond(withSuccess("[]", MediaType.APPLICATION_JSON));

        assertThat(service.fetchAllRepos("t")).hasSize(100);

        server.verify();
    }

    @Test
    void propagatesUnauthorizedWhenTokenRevoked() {
        server.expect(requestTo(containsString("/user/repos")))
                .andRespond(withStatus(HttpStatus.UNAUTHORIZED));

        assertThatThrownBy(() -> service.fetchAllRepos("revoked"))
                .isInstanceOf(HttpClientErrorException.Unauthorized.class);
    }

    // ---- pagination safety limit ----

    @Test
    void failsInsteadOfFetchingForeverWhenEveryAllowedPageIsFull() {
        GithubService limited = new GithubService(client, 2);
        server.expect(requestTo(containsString("&page=1&")))
                .andRespond(withSuccess(repoArray(1, 100), MediaType.APPLICATION_JSON));
        server.expect(requestTo(containsString("&page=2&")))
                .andRespond(withSuccess(repoArray(101, 200), MediaType.APPLICATION_JSON));
        // No third expectation: a request for page 3 makes MockRestServiceServer fail the test.

        assertThatThrownBy(() -> limited.fetchAllRepos("t"))
                .isInstanceOf(RepositoryLimitExceededException.class)
                .extracting(e -> ((RepositoryLimitExceededException) e).getLimit())
                .isEqualTo(200);

        server.verify(); // exactly maxPages requests were made
    }

    @Test
    void doesNotFailWhenTheLastAllowedPageIsShort() {
        GithubService limited = new GithubService(client, 2);
        server.expect(requestTo(containsString("&page=1&")))
                .andRespond(withSuccess(repoArray(1, 100), MediaType.APPLICATION_JSON));
        server.expect(requestTo(containsString("&page=2&")))
                .andRespond(withSuccess(repoArray(101, 105), MediaType.APPLICATION_JSON));

        assertThat(limited.fetchAllRepos("t")).hasSize(105);

        server.verify();
    }

    @Test
    void rejectsNonPositivePageLimit() {
        assertThatThrownBy(() -> new GithubService(client, 0))
                .isInstanceOf(IllegalArgumentException.class);
    }

    // ---- private repositories ----

    @Test
    void asksGithubForPublicAndPrivateRepositoriesTheUserCanAccess() {
        server.expect(requestTo(allOf(
                        containsString("/user/repos"),
                        containsString("visibility=all"),
                        containsString("affiliation=owner"),
                        containsString("organization_member"))))
                .andRespond(withSuccess("[]", MediaType.APPLICATION_JSON));

        service.fetchAllRepos("t");

        server.verify();
    }

    @Test
    void returnsBothPublicAndPrivateRepositories() {
        String json = "[" + repoJson(1, false) + "," + repoJson(2, true) + "," + repoJson(3, false) + "]";
        server.expect(requestTo(containsString("/user/repos")))
                .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

        List<GithubRepo> repos = service.fetchAllRepos("t");

        assertThat(repos).hasSize(3);
        assertThat(repos).filteredOn(GithubRepo::isPrivate).extracting(GithubRepo::id).containsExactly(2L);
        assertThat(repos).filteredOn(r -> !r.isPrivate()).extracting(GithubRepo::id).containsExactly(1L, 3L);
    }

    @Test
    void paginationCollectsMixedPublicAndPrivateRepositoriesAcrossPages() {
        server.expect(requestTo(containsString("&page=1&")))
                .andRespond(withSuccess(mixedArray(1, 100), MediaType.APPLICATION_JSON));
        server.expect(requestTo(containsString("&page=2&")))
                .andRespond(withSuccess(mixedArray(101, 110), MediaType.APPLICATION_JSON));

        List<GithubRepo> repos = service.fetchAllRepos("t");

        assertThat(repos).hasSize(110);
        // odd ids are private in mixedArray(): 55 of the 110
        assertThat(repos.stream().filter(GithubRepo::isPrivate).count()).isEqualTo(55);
        server.verify();
    }

    @Test
    void exposesOnlyWhatGithubReturnsAndNeverProbesOtherRepositories() {
        // GitHub omits repositories this user/app authorization cannot access (e.g. an org that
        // restricts OAuth apps). The service must return exactly that list and make no other call.
        server.expect(requestTo(containsString("/user/repos")))
                .andRespond(withSuccess("[" + repoJson(1, true) + "," + repoJson(2, false) + "]",
                        MediaType.APPLICATION_JSON));

        List<GithubRepo> repos = service.fetchAllRepos("t");

        assertThat(repos).extracting(GithubRepo::id).containsExactly(1L, 2L);
        server.verify(); // exactly one request; MockRestServiceServer fails on any unexpected one
    }

    @Test
    void toleratesMissingOptionalFieldsFromGithub() {
        server.expect(requestTo(containsString("/user/repos")))
                .andRespond(withSuccess("[{\"id\":7,\"name\":\"bare\"}]", MediaType.APPLICATION_JSON));

        List<GithubRepo> repos = service.fetchAllRepos("t");

        assertThat(repos).hasSize(1);
        assertThat(repos.get(0).id()).isEqualTo(7);
        assertThat(repos.get(0).isPrivate()).isNull();
        assertThat(repos.get(0).stars()).isNull();
    }

    // ---- helpers ----

    private static String repoJson(int id) {
        return repoJson(id, true);
    }

    private static String repoJson(int id, boolean isPrivate) {
        return """
                {"id":%d,"name":"repo-%d","full_name":"octocat/repo-%d",
                 "html_url":"https://github.com/octocat/repo-%d","private":%b,
                 "stargazers_count":3,"some_new_github_field":"ignored",
                 "owner":{"login":"octocat","html_url":"https://github.com/octocat"}}
                """.formatted(id, id, id, id, isPrivate);
    }

    private static String repoArray(int fromInclusive, int toInclusive) {
        return IntStream.rangeClosed(fromInclusive, toInclusive)
                .mapToObj(GithubServiceTest::repoJson)
                .collect(Collectors.joining(",", "[", "]"));
    }

    /** Odd ids are private, even ids are public. */
    private static String mixedArray(int fromInclusive, int toInclusive) {
        return IntStream.rangeClosed(fromInclusive, toInclusive)
                .mapToObj(id -> repoJson(id, id % 2 == 1))
                .collect(Collectors.joining(",", "[", "]"));
    }
}
