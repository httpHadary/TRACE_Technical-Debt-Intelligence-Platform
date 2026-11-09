package com.example.TechDept365.controller;

import org.springframework.http.MediaType;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HomeController {

    @GetMapping(value = "/", produces = MediaType.TEXT_HTML_VALUE)
    public String home(CsrfToken csrf) {
        return """
                <h1>TechDept365</h1>
                <p><a href="/oauth2/authorization/github">Sign in with GitHub</a></p>
                <p><a href="/api/me">/api/me</a> &middot; <a href="/api/repos">/api/repos</a></p>
                <form method="post" action="/logout">
                  <input type="hidden" name="%s" value="%s">
                  <button>Logout</button>
                </form>
                """.formatted(csrf.getParameterName(), csrf.getToken());
    }
}
