import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.FieldDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.expr.FieldAccessExpr;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.NameExpr;
import com.github.javaparser.ast.type.ClassOrInterfaceType;

/**
 * Java Driller - pipeline version of Java_Driller_Data.java.
 *
 * The metric logic (class index, dependency resolution, fan-in, fan-out, coupling, test
 * existence) is the same as in Java_Driller_Data.java; cohesion now follows LCOM4 exactly
 * (see calculateCohesion). What changed, so the
 * output can be joined with SonarQube, CKJM and git for the SAME snapshot:
 *
 *   1. Identity:  a file is identified by its path relative to the repository root
 *                 (e.g. okhttp/src/main/java/okhttp3/Call.java), not by its name or by a
 *                 F000123 number that changes with folder order.
 *   2. Scope:     only the main source folders given with --roots (the folders SonarQube
 *                 scanned, e.g. src/main/java). Test folders are only used for "has test".
 *   3. Snapshot:  --week and --sha are written into every row.
 *   4. Format:    CSV (';'), appended per snapshot - no Excel row limit, no Apache POI.
 *   5. Parser:    language level RAW, so 2006-era code (enum as a name) and Java 17 both parse.
 *
 * Output (appended; header written when the file is new):
 *   <out>/raw_jd_file.csv  week;sha;path;class_count;method_count;fan_in;external_class_count;
 *                          fan_out;coupling;cohesion;has_test;lcom4_classes;noncohesive_classes;
 *                          parse_status   (lcom4_classes = classes measured for cohesion,
 *                          noncohesive_classes = those with LCOM4 > 1, i.e. more than one job)
 *   <out>/raw_jd_deps.csv  week;sha;source_path;target_path
 *
 * Usage:
 *   java -cp javaparser-core-3.26.2.jar:. JavaDriller --root <repo> --roots src/main/java,core/src/main/java
 *        --week 2017-03-10 --sha <40 hex> --out <run folder>
 */
public class JavaDriller {

    public static void main(String[] args) throws IOException {
        Map<String, String> a = parseArgs(args);
        File root = new File(req(a, "root")).getCanonicalFile();
        String week = req(a, "week");
        String sha = req(a, "sha");
        File out = new File(req(a, "out"));
        List<String> roots = new ArrayList<>();
        for (String r : req(a, "roots").split(",")) {
            if (!r.trim().isEmpty()) {
                roots.add(r.trim());
            }
        }
        if (!root.isDirectory()) {
            System.err.println("JavaDriller: not a directory: " + root);
            System.exit(2);
        }

        ParserConfiguration configuration = new ParserConfiguration();
        configuration.setLanguageLevel(ParserConfiguration.LanguageLevel.RAW);
        configuration.setStoreTokens(false);
        configuration.setAttributeComments(false);
        configuration.setLexicalPreservationEnabled(false);
        configuration.setDetectOriginalLineSeparator(false);
        configuration.setPreprocessUnicodeEscapes(false);
        JavaParser parser = new JavaParser(configuration);

        // STEP 1: main Java files, only inside the given source roots
        List<FileInfo> files = new ArrayList<>();
        for (String r : roots) {
            File dir = new File(root, r);
            if (dir.isDirectory()) {
                findJavaFiles(root, dir, files);
            }
        }
        Collections.sort(files, (x, y) -> x.id.compareTo(y.id));

        // STEP 2: class index (no ASTs kept)
        Map<String, List<FileInfo>> classesByFQCN = new HashMap<>();
        Map<String, List<FileInfo>> classesBySimpleName = new HashMap<>();
        for (FileInfo info : files) {
            CompilationUnit cu = parseFile(parser, info.file);
            if (cu == null) {
                info.parseStatus = "PARSE_FAILED";
                continue;
            }
            info.parseStatus = "OK";
            indexClasses(info, cu, classesByFQCN, classesBySimpleName);
        }

        // STEP 3: test index - class names of .java files in test folders anywhere in the repo
        Set<String> testNames = new HashSet<>();
        collectTestNames(root, testNames, false);

        // STEP 4: per-file metrics and dependency edges
        Map<String, Integer> fanIn = new HashMap<>();
        Map<String, Set<String>> fanInSources = new HashMap<>();
        Map<String, Set<String>> externalClassFanIn = new HashMap<>();
        for (FileInfo info : files) {
            fanIn.put(info.id, 0);
            fanInSources.put(info.id, new HashSet<>());
            externalClassFanIn.put(info.id, new HashSet<>());
        }
        List<MetricInfo> metrics = new ArrayList<>();
        List<String[]> edges = new ArrayList<>();

        for (FileInfo source : files) {
            CompilationUnit cu = parseFile(parser, source.file);
            if (cu == null) {
                metrics.add(new MetricInfo(source.id, 0, 0, 0, new HashSet<>(), new double[] {Double.NaN, 0, 0}, false, "PARSE_FAILED"));
                continue;
            }
            int classCount = cu.findAll(ClassOrInterfaceDeclaration.class).size();
            int methodCount = cu.findAll(MethodDeclaration.class).size();
            Set<FileInfo> dependencies = findDependencies(source, cu, classesByFQCN, classesBySimpleName);
            Map<FileInfo, Set<String>> classDependencies =
                    findClassDependencies(source, cu, classesByFQCN, classesBySimpleName);
            for (Map.Entry<FileInfo, Set<String>> e : classDependencies.entrySet()) {
                for (String sourceClass : e.getValue()) {
                    externalClassFanIn.computeIfAbsent(e.getKey().id, k -> new HashSet<>())
                            .add(source.id + "::" + sourceClass);
                }
            }
            Set<String> fanOutTargetIds = new HashSet<>();
            for (FileInfo target : dependencies) {
                fanOutTargetIds.add(target.id);
                fanIn.put(target.id, fanIn.getOrDefault(target.id, 0) + 1);
                fanInSources.computeIfAbsent(target.id, k -> new HashSet<>()).add(source.id);
                edges.add(new String[] {source.id, target.id});
            }
            metrics.add(new MetricInfo(source.id, classCount, methodCount, dependencies.size(),
                    fanOutTargetIds, cohesionStats(cu), hasTest(cu, testNames), "OK"));
        }

        // STEP 5: write (append) the two CSV tables
        if (!out.isDirectory() && !out.mkdirs()) {
            throw new IOException("Could not create " + out);
        }
        File fileCsv = new File(out, "raw_jd_file.csv");
        boolean newFile = !fileCsv.exists();
        try (PrintWriter w = writer(fileCsv)) {
            if (newFile) {
                w.println("week;sha;path;class_count;method_count;fan_in;external_class_count;"
                        + "fan_out;coupling;cohesion;has_test;lcom4_classes;noncohesive_classes;parse_status");
            }
            for (MetricInfo m : metrics) {
                Set<String> coupling = new HashSet<>(fanInSources.getOrDefault(m.fileId, Collections.emptySet()));
                coupling.addAll(m.fanOutTargetIds);
                w.println(String.join(";", week, sha, csv(m.fileId),
                        String.valueOf(m.classCount), String.valueOf(m.methodCount),
                        String.valueOf(fanIn.getOrDefault(m.fileId, 0)),
                        String.valueOf(externalClassFanIn.getOrDefault(m.fileId, Collections.emptySet()).size()),
                        String.valueOf(m.fanOut), String.valueOf(coupling.size()),
                        Double.isNaN(m.cohesion) ? "" : String.valueOf(m.cohesion), m.hasTest ? "1" : "0",
                        String.valueOf(m.lcom4Classes), String.valueOf(m.noncohesiveClasses), m.status));
            }
        }
        File depCsv = new File(out, "raw_jd_deps.csv");
        boolean newDeps = !depCsv.exists();
        try (PrintWriter w = writer(depCsv)) {
            if (newDeps) {
                w.println("week;sha;source_path;target_path");
            }
            for (String[] e : edges) {
                w.println(String.join(";", week, sha, csv(e[0]), csv(e[1])));
            }
        }
        int failed = 0;
        for (MetricInfo m : metrics) {
            if (!m.status.equals("OK")) {
                failed++;
            }
        }
        System.out.println("JavaDriller: " + files.size() + " files, " + edges.size()
                + " dependencies, " + failed + " not parsed");
    }

    // ---------------------------------------------------------------- helpers

    static Map<String, String> parseArgs(String[] args) {
        Map<String, String> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < args.length; i += 2) {
            m.put(args[i].replaceFirst("^--", ""), args[i + 1]);
        }
        return m;
    }

    static String req(Map<String, String> a, String k) {
        String v = a.get(k);
        if (v == null) {
            System.err.println("JavaDriller: missing --" + k);
            System.exit(2);
        }
        return v;
    }

    static PrintWriter writer(File f) throws IOException {
        return new PrintWriter(new OutputStreamWriter(new FileOutputStream(f, true), StandardCharsets.UTF_8));
    }

    static String csv(String s) {
        return s.replace(";", "_").replace("\n", " ");
    }

    static String rel(File root, File f) throws IOException {
        String r = root.toPath().relativize(f.getCanonicalFile().toPath()).toString();
        return r.replace(File.separatorChar, '/');
    }

    static class FileInfo {
        String id;          // path relative to the repository root
        File file;
        String parseStatus = "NOT_PARSED";

        FileInfo(String id, File file) {
            this.id = id;
            this.file = file;
        }
    }

    static class MetricInfo {
        String fileId;
        int classCount, methodCount, fanOut;
        Set<String> fanOutTargetIds;
        double cohesion;
        int lcom4Classes, noncohesiveClasses;
        boolean hasTest;
        String status;

        MetricInfo(String fileId, int classCount, int methodCount, int fanOut, Set<String> fanOutTargetIds,
                   double[] coh, boolean hasTest, String status) {
            this.fileId = fileId;
            this.classCount = classCount;
            this.methodCount = methodCount;
            this.fanOut = fanOut;
            this.fanOutTargetIds = fanOutTargetIds;
            this.cohesion = coh[0];
            this.lcom4Classes = (int) coh[1];
            this.noncohesiveClasses = (int) coh[2];
            this.hasTest = hasTest;
            this.status = status;
        }
    }

    public static CompilationUnit parseFile(JavaParser parser, File file) {
        try {
            ParseResult<CompilationUnit> result = parser.parse(file);
            return result.getResult().orElse(null);
        } catch (Exception | StackOverflowError e) {
            System.err.println("Could not parse: " + file.getName() + " -> " + e.getMessage());
            return null;
        }
    }

    public static void findJavaFiles(File root, File folder, List<FileInfo> files) throws IOException {
        File[] children = folder.listFiles();
        if (children == null) {
            return;
        }
        for (File f : children) {
            if (f.isDirectory()) {
                String n = f.getName();
                if (n.equals(".git") || n.equals("target") || n.equals("build") || n.equals("test")
                        || n.equals("node_modules") || n.equals("out")) {
                    continue;
                }
                findJavaFiles(root, f, files);
            } else if (f.getName().endsWith(".java")) {
                files.add(new FileInfo(rel(root, f), f));
            }
        }
    }

    public static void indexClasses(FileInfo info, CompilationUnit cu,
                                    Map<String, List<FileInfo>> byFQCN, Map<String, List<FileInfo>> bySimple) {
        String pkg = cu.getPackageDeclaration().map(p -> p.getNameAsString()).orElse("");
        for (ClassOrInterfaceDeclaration c : cu.findAll(ClassOrInterfaceDeclaration.class)) {
            String simple = c.getNameAsString();
            String fqcn = pkg.isEmpty() ? simple : pkg + "." + simple;
            byFQCN.computeIfAbsent(fqcn, k -> new ArrayList<>()).add(info);
            bySimple.computeIfAbsent(simple, k -> new ArrayList<>()).add(info);
        }
    }

    // same resolution order as Java_Driller_Data: imports, same package, imported name, unique name
    public static Set<FileInfo> findDependencies(FileInfo source, CompilationUnit cu,
                                                 Map<String, List<FileInfo>> byFQCN,
                                                 Map<String, List<FileInfo>> bySimple) {
        Set<FileInfo> deps = new HashSet<>();
        cu.getImports().forEach(imp -> {
            if (imp.isAsterisk()) {
                return;
            }
            String name = imp.getNameAsString();
            if (imp.isStatic()) {
                int lastDot = name.lastIndexOf('.');
                if (lastDot > 0) {
                    name = name.substring(0, lastDot);
                }
            }
            List<FileInfo> targets = byFQCN.get(name);
            if (targets != null) {
                for (FileInfo t : targets) {
                    if (!t.id.equals(source.id)) {
                        deps.add(t);
                    }
                }
            }
        });
        String pkg = cu.getPackageDeclaration().map(p -> p.getNameAsString()).orElse("");
        Set<String> imported = getImportedSimpleNames(cu);
        cu.findAll(ClassOrInterfaceType.class).forEach(type -> resolve(type.getNameAsString(), pkg, imported,
                source, byFQCN, bySimple, deps));
        return deps;
    }

    static void resolve(String simple, String pkg, Set<String> imported, FileInfo source,
                        Map<String, List<FileInfo>> byFQCN, Map<String, List<FileInfo>> bySimple,
                        Set<FileInfo> into) {
        List<FileInfo> targets = bySimple.get(simple);
        if (targets == null || targets.isEmpty()) {
            return;
        }
        if (!pkg.isEmpty()) {
            List<FileInfo> same = byFQCN.get(pkg + "." + simple);
            if (same != null) {
                for (FileInfo t : same) {
                    if (!t.id.equals(source.id)) {
                        into.add(t);
                    }
                }
                return;
            }
        }
        if (imported.contains(simple)) {
            for (FileInfo t : targets) {
                if (!t.id.equals(source.id)) {
                    into.add(t);
                }
            }
            return;
        }
        if (targets.size() == 1 && !targets.get(0).id.equals(source.id)) {
            into.add(targets.get(0));
        }
    }

    public static Map<FileInfo, Set<String>> findClassDependencies(FileInfo source, CompilationUnit cu,
                                                                   Map<String, List<FileInfo>> byFQCN,
                                                                   Map<String, List<FileInfo>> bySimple) {
        Map<FileInfo, Set<String>> result = new HashMap<>();
        Set<String> imported = getImportedSimpleNames(cu);
        String pkg = cu.getPackageDeclaration().map(p -> p.getNameAsString()).orElse("");
        for (ClassOrInterfaceDeclaration sourceClass : cu.findAll(ClassOrInterfaceDeclaration.class)) {
            Set<FileInfo> targets = new HashSet<>();
            sourceClass.findAll(ClassOrInterfaceType.class).forEach(type -> resolve(type.getNameAsString(), pkg,
                    imported, source, byFQCN, bySimple, targets));
            String name = pkg.isEmpty() ? sourceClass.getNameAsString() : pkg + "." + sourceClass.getNameAsString();
            for (FileInfo t : targets) {
                result.computeIfAbsent(t, k -> new HashSet<>()).add(name);
            }
        }
        return result;
    }

    public static Set<String> getImportedSimpleNames(CompilationUnit cu) {
        Set<String> names = new HashSet<>();
        cu.getImports().forEach(imp -> {
            if (imp.isAsterisk()) {
                return;
            }
            String name = imp.getNameAsString();
            int lastDot = name.lastIndexOf('.');
            if (lastDot >= 0 && lastDot < name.length() - 1) {
                if (imp.isStatic()) {
                    String before = name.substring(0, lastDot);
                    int prev = before.lastIndexOf('.');
                    if (prev >= 0) {
                        names.add(before.substring(prev + 1));
                    }
                } else {
                    names.add(name.substring(lastDot + 1));
                }
            }
        });
        return names;
    }

    /*
     * Cohesion = 1 / LCOM4 (Hitz and Montazeri 1995), averaged over the file's classes.
     * LCOM4 = number of connected groups in a graph whose points are the class's methods; two
     * methods are linked when
     *   - both use the same field of the class, written as  x  or  this.x , or
     *   - one calls the other, written as  m()  or  this.m()  (overloads share a name and are linked).
     * 1 group = the class does one job (cohesion 1.0); 3 groups = three jobs in one class (0.333).
     * Measured: every class (not interface) with at least one method that has a body; constructors
     * and abstract methods are left out, as in common LCOM4 tools. A class with one method = 1.0.
     * A file with no measurable class returns NaN, written as an empty cell ("not measurable").
     *
     * Changed from Java_Driller_Data.java (2026-10-20): method calls now link methods, "this.x"
     * now counts as using field x, and classes without fields are measured instead of skipped.
     */
    public static double calculateCohesion(CompilationUnit cu) {
        return cohesionStats(cu)[0];
    }

    /** {mean of 1/LCOM4 (NaN if none), classes measured, classes with LCOM4 > 1}. */
    public static double[] cohesionStats(CompilationUnit cu) {
        double total = 0.0;
        int analyzed = 0;
        int noncohesive = 0;
        for (ClassOrInterfaceDeclaration clazz : cu.findAll(ClassOrInterfaceDeclaration.class)) {
            if (clazz.isInterface()) {
                continue;
            }
            Set<String> fieldNames = new HashSet<>();
            for (FieldDeclaration f : clazz.getFields()) {
                f.getVariables().forEach(v -> fieldNames.add(v.getNameAsString()));
            }
            List<String> names = new ArrayList<>();
            List<Set<String>> used = new ArrayList<>();
            List<Set<String>> calls = new ArrayList<>();
            for (MethodDeclaration m : clazz.getMethods()) {
                if (!m.getBody().isPresent()) {
                    continue;                                   // abstract or native: no code
                }
                Set<String> u = new HashSet<>();
                m.findAll(NameExpr.class).forEach(n -> u.add(n.getNameAsString()));
                m.findAll(FieldAccessExpr.class).forEach(fa -> {
                    if (fa.getScope().isThisExpr()) {
                        u.add(fa.getNameAsString());
                    }
                });
                u.retainAll(fieldNames);
                Set<String> c = new HashSet<>();
                m.findAll(MethodCallExpr.class).forEach(mc -> {
                    if (!mc.getScope().isPresent() || mc.getScope().get().isThisExpr()) {
                        c.add(mc.getNameAsString());
                    }
                });
                names.add(m.getNameAsString());
                used.add(u);
                calls.add(c);
            }
            if (names.isEmpty()) {
                continue;
            }
            int groups = lcom4(names, used, calls);
            total += 1.0 / groups;
            analyzed++;
            if (groups > 1) {
                noncohesive++;
            }
        }
        double mean = analyzed == 0 ? Double.NaN : Math.round(total / analyzed * 1000.0) / 1000.0;
        return new double[] {mean, analyzed, noncohesive};
    }

    /** LCOM4 from plain data: method names, fields each method uses, method names each one calls. */
    static int lcom4(List<String> names, List<Set<String>> used, List<Set<String>> calls) {
        int n = names.size();
        int[] parent = new int[n];
        for (int i = 0; i < n; i++) {
            parent[i] = i;
        }
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (!Collections.disjoint(used.get(i), used.get(j))) {
                    union(parent, i, j);
                }
            }
            for (int j = 0; j < n; j++) {
                if (i != j && calls.get(i).contains(names.get(j))) {
                    union(parent, i, j);
                }
            }
        }
        Set<Integer> groups = new HashSet<>();
        for (int i = 0; i < n; i++) {
            groups.add(find(parent, i));
        }
        return groups.size();
    }

    static int find(int[] p, int v) {
        if (p[v] != v) {
            p[v] = find(p, p[v]);
        }
        return p[v];
    }

    static void union(int[] p, int a, int b) {
        int ra = find(p, a), rb = find(p, b);
        if (ra != rb) {
            p[rb] = ra;
        }
    }

    // class names of .java files that sit in a test folder (".../test/...")
    public static void collectTestNames(File folder, Set<String> names, boolean inTest) {
        File[] files = folder.listFiles();
        if (files == null) {
            return;
        }
        for (File f : files) {
            if (f.isDirectory()) {
                String n = f.getName();
                if (n.equals(".git") || n.equals("target") || n.equals("build") || n.equals("node_modules")) {
                    continue;
                }
                collectTestNames(f, names, inTest || n.equals("test") || n.equals("tests"));
            } else if (inTest && f.getName().endsWith(".java")) {
                names.add(f.getName().substring(0, f.getName().length() - 5));
            }
        }
    }

    public static boolean hasTest(CompilationUnit cu, Set<String> testNames) {
        for (ClassOrInterfaceDeclaration c : cu.findAll(ClassOrInterfaceDeclaration.class)) {
            String n = c.getNameAsString();
            if (testNames.contains(n + "Test") || testNames.contains(n + "Tests") || testNames.contains("Test" + n)
                    || testNames.contains(n + "IT") || testNames.contains(n + "IntegrationTest")
                    || testNames.contains(n + "IntegrationTests") || testNames.contains(n + "Spec")
                    || testNames.contains(n + "Specs")) {
                return true;
            }
        }
        return false;
    }
}
