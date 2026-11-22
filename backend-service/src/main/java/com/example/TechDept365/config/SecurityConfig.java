package com.example.TechDept365.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.HttpStatusEntryPoint;
import org.springframework.security.web.servlet.util.matcher.PathPatternRequestMatcher;
import org.springframework.http.MediaType;
import org.springframework.security.web.authentication.LoginUrlAuthenticationEntryPoint;
import org.springframework.security.web.util.matcher.MediaTypeRequestMatcher;
import org.springframework.security.web.util.matcher.NegatedRequestMatcher;
import java.util.Set;

@Configuration
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {

        MediaTypeRequestMatcher htmlMatcher =
                new MediaTypeRequestMatcher(MediaType.TEXT_HTML);

        htmlMatcher.setIgnoredMediaTypes(Set.of(MediaType.ALL));

        http.authorizeHttpRequests(auth -> auth
                        .requestMatchers("/", "/error").permitAll()
                        .anyRequest().authenticated())
            .oauth2Login(Customizer.withDefaults()) // Browser flow: unauthenticated users are redirected to GitHub's login/consent page.
                .exceptionHandling(ex -> ex
                        // API requests always receive 401.
                        .defaultAuthenticationEntryPointFor(
                                new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED),
                                PathPatternRequestMatcher.pathPattern("/api/**")
                        )

                        // Browser requests receive a redirect to GitHub login.
                        .defaultAuthenticationEntryPointFor(
                                new LoginUrlAuthenticationEntryPoint("/oauth2/authorization/github"),
                                htmlMatcher
                        )

                        // Non-browser requests receive 401.
                        .defaultAuthenticationEntryPointFor(
                                new HttpStatusEntryPoint(HttpStatus.UNAUTHORIZED),
                                new NegatedRequestMatcher(
                                        new NegatedRequestMatcher(htmlMatcher)
                                )
                        )
                )
            .logout(logout -> logout.logoutSuccessUrl("/")); // API calls get a clean 401 JSON-friendly response instead of a redirect.
        return http.build();
    }
}
