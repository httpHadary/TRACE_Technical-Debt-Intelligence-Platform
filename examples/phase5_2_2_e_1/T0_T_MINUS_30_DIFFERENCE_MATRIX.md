# T0 versus T−30 configuration differences

Both columns below are independently derived static models. T0 additionally has
its separate D.3 effective model and E.0.6 actual compile proof. T−30 has neither;
no T0 effective-model identity or runtime profile result is transferred.

| Dimension | T0 | T−30 |
| --- | --- | --- |
| Commons Parent |76|74|
| Tracked files |117|116|
| Java production files |26|26; same paths and byte hashes|
| JUnit Jupiter/API/engine/params |5.11.1|5.11.0|
| Imported project JUnit BOM |5.11.1|5.11.0|
| Direct Commons IO (test) |2.17.0|2.16.1|
| Direct Mockito (test) |4.11.0|4.11.0|
| Surefire plan descriptor |3.5.0|3.4.0|
| Buildnumber compile plugin |3.2.1|3.2.0|
| Compiler |3.13.0/release8|3.13.0/release8; no execution yet|
| Build-plan default tasks |deploy, actually checked|deploy, static descriptor/config verified|
| Resources/generation |Original resource rules; actual T0 evidence|Same static sections/antrun resource task; behavior unverified|
| SCM |Actual configured fallback observed|Same fallback config, older plugin; behavior UNKNOWN|
| Profiles |Static candidates + separate actual D.3 evidence|25 static records; actual activation UNKNOWN|
| Actual effective model |D.3 verified|UNVERIFIED; hash null|
| Compilation |COMPILE_PASS|NOT_EXECUTED|

Full declared/managed plugin version changes:

| Scope/plugin | T0 | T−30 |
| --- | --- | --- |
|plugins: `com.github.spotbugs:spotbugs-maven-plugin`|4.8.6.4|4.8.6.2|
|plugins: `org.apache.maven.plugins:maven-surefire-plugin`|3.5.0|3.4.0|
|plugins: `org.codehaus.mojo:buildnumber-maven-plugin`|3.2.1|3.2.0|
|managed_plugins: `com.github.spotbugs:spotbugs-maven-plugin`|4.8.6.4|4.8.6.2|
|managed_plugins: `org.apache.maven.plugins:maven-failsafe-plugin`|3.5.0|3.4.0|
|managed_plugins: `org.apache.maven.plugins:maven-javadoc-plugin`|3.10.0|3.8.0|
|managed_plugins: `org.apache.maven.plugins:maven-pmd-plugin`|3.25.0|3.24.0|
|managed_plugins: `org.apache.maven.plugins:maven-surefire-plugin`|3.5.0|3.4.0|
|managed_plugins: `org.codehaus.mojo:buildnumber-maven-plugin`|3.2.1|3.2.0|

`configuration_difference.json` records all12 changed inherited properties, complete
managed/build version maps, dependency-management/import/profile inputs, plugin
configurations and raw build resource/default-goal sections. Same source bytes do
not imply identical effective models. Six tracked files differ and one T0 workflow
file is absent at T−30; no production Java file differs. No historical Java test goal was executed.
