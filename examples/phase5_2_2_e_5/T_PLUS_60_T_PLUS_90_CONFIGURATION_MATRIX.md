# T+60 versus T+90 configuration matrix

Static declarations from each original POM and parent chain. Actual Maven models and profiles remain UNKNOWN.

| Component | T+60 | T+90 |
| --- | --- | --- |
| Parent chain | Commons78 / Apache33 | Commons78 / Apache33 |
| Tracked / production Java files | 138 / 36 | 138 / 36 |
| Commons Text (test scope) | 1.12.0 | 1.13.0 |
| Commons IO (test scope) | 2.18.0 | 2.18.0 |
| JUnit Jupiter (test scope) | 5.11.2 | 5.11.2 |
| Mockito (test scope) | 4.11.0 | 4.11.0 |
| Actual compilation | COMPILE_PASS | NOT_EXECUTED |
|com.github.siom79.japicmp:japicmp-maven-plugin|0.23.0|0.23.0|
|com.github.spotbugs:spotbugs-maven-plugin|4.8.6.4|4.8.6.4|
|org.apache.commons:commons-build-plugin|1.14.0|1.14.0|
|org.apache.commons:commons-release-plugin|1.8.2|1.8.2|
|org.apache.felix:maven-bundle-plugin|5.1.9|5.1.9|
|org.apache.maven.plugins:maven-antrun-plugin|3.1.0|3.1.0|
|org.apache.maven.plugins:maven-artifact-plugin|3.5.1|3.5.1|
|org.apache.maven.plugins:maven-assembly-plugin|3.7.1|3.7.1|
|org.apache.maven.plugins:maven-checkstyle-plugin|3.5.0|3.5.0|
|org.apache.maven.plugins:maven-clean-plugin|3.4.0|3.4.0|
|org.apache.maven.plugins:maven-compiler-plugin|3.13.0|3.13.0|
|org.apache.maven.plugins:maven-dependency-plugin|3.7.1|3.7.1|
|org.apache.maven.plugins:maven-deploy-plugin|3.1.2|3.1.2|
|org.apache.maven.plugins:maven-ear-plugin|3.3.0|3.3.0|
|org.apache.maven.plugins:maven-enforcer-plugin|3.5.0|3.5.0|
|org.apache.maven.plugins:maven-failsafe-plugin|3.5.1|3.5.1|
|org.apache.maven.plugins:maven-gpg-plugin|3.2.4|3.2.4|
|org.apache.maven.plugins:maven-help-plugin|3.4.1|3.4.1|
|org.apache.maven.plugins:maven-install-plugin|3.1.2|3.1.2|
|org.apache.maven.plugins:maven-invoker-plugin|3.7.0|3.7.0|
|org.apache.maven.plugins:maven-jar-plugin|3.4.2|3.4.2|
|org.apache.maven.plugins:maven-javadoc-plugin|3.10.1|3.10.1|
|org.apache.maven.plugins:maven-plugin-plugin|3.13.1|3.13.1|
|org.apache.maven.plugins:maven-plugin-report-plugin|3.13.1|3.13.1|
|org.apache.maven.plugins:maven-pmd-plugin|3.24.0|3.24.0|
|org.apache.maven.plugins:maven-project-info-reports-plugin|3.6.2|3.6.2|
|org.apache.maven.plugins:maven-release-plugin|3.1.0|3.1.0|
|org.apache.maven.plugins:maven-remote-resources-plugin|3.2.0|3.2.0|
|org.apache.maven.plugins:maven-resources-plugin|3.3.1|3.3.1|
|org.apache.maven.plugins:maven-scm-plugin|2.1.0|2.1.0|
|org.apache.maven.plugins:maven-scm-publish-plugin|3.3.0|3.3.0|
|org.apache.maven.plugins:maven-shade-plugin|3.6.0|3.6.0|
|org.apache.maven.plugins:maven-site-plugin|3.12.1|3.12.1|
|org.apache.maven.plugins:maven-source-plugin|3.2.1|3.2.1|
|org.apache.maven.plugins:maven-surefire-plugin|3.5.1|3.5.1|
|org.apache.maven.plugins:maven-surefire-report-plugin|3.3.0|3.3.0|
|org.apache.maven.plugins:maven-war-plugin|3.4.0|3.4.0|
|org.apache.rat:apache-rat-plugin|0.16.1|0.16.1|
|org.codehaus.mojo:build-helper-maven-plugin|3.6.0|3.6.0|
|org.codehaus.mojo:buildnumber-maven-plugin|3.2.1|3.2.1|
|org.codehaus.mojo:exec-maven-plugin|3.4.1|3.4.1|
|org.codehaus.mojo:javancss-maven-plugin|2.1|2.1|
|org.codehaus.mojo:taglist-maven-plugin|3.2.1|3.2.1|
|org.codehaus.mojo:versions-maven-plugin|2.17.1|2.17.1|
|org.cyclonedx:cyclonedx-maven-plugin|2.9.0|2.9.0|
|org.jacoco:jacoco-maven-plugin|0.8.12|0.8.12|
|org.moditect:moditect-maven-plugin|1.2.2.Final|1.2.2.Final|
|org.spdx:spdx-maven-plugin|0.7.4|0.7.4|

Source differences: 11 changed paths; no added/removed paths or mode changes. Two production Java files changed: CommandLine.java and Option.java. Four test files, three workflows, the POM and change log also changed.

Full identities, resource differences, inheritance, properties, profiles, management and original plugin configuration: configuration_difference.json. Descriptor evidence establishes original goals and phases; it does not prove Maven execution or output populations.
