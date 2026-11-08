"""Explicit source rights, family exposure, language and production-scope rules."""
import re
from pathlib import PurePosixPath
from .contracts import digest, hash_id, revision, utc, MODES, MISSING_WORDS

PILOT_TARGETS = ("java_dominant", "python_dominant", "mixed_python_jsts")
SUFFIXES = {".java": "java", ".py": "py", ".js": "js", ".jsx": "js", ".ts": "ts",
            ".tsx": "ts", ".c": "cpp", ".cc": "cpp", ".cpp": "cpp", ".h": "cpp",
            ".hpp": "cpp", ".cs": "cs", ".go": "go"}
EXCLUDE = frozenset(("test", "tests", "__tests__", "vendor", "node_modules", "generated", "dist", ".git"))
SCOPE_POLICY = {"suffixes": SUFFIXES, "excluded_components": sorted(EXCLUDE), "rename_policy": "no-renames"}
SCOPE_ID = digest(SCOPE_POLICY)


def source_language(path):
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or "\\" in path:
        raise ValueError("Repository-relative POSIX path required")
    return None if any(v.lower() in EXCLUDE for v in p.parts[:-1]) else SUFFIXES.get(p.suffix.lower())


def language_distribution(raw):
    if raw in (None, ""):
        return {}, ["MISSING_LANGUAGE_DISTRIBUTION"]
    values, errors = {}, []
    for token in re.split(r"[;,]", raw):
        m = re.fullmatch(r"([a-zA-Z0-9_+#]+)=([0-9]+)", token.strip())
        if not m or m[1] in values:
            errors.append(token)
        else:
            values[m[1]] = int(m[2])
    return values, errors


def language_family(languages):
    """Programming NCLOC only; XML/CSS/web are not extra programming families."""
    groups = {}
    for key, value in languages.items():
        if type(value) is not int or value < 0:
            raise ValueError("Nonnegative integer NCLOC required")
        if key in set(SUFFIXES.values()):
            group = "jsts" if key in ("js", "ts") else key
            groups[group] = groups.get(group, 0) + value
    total = sum(groups.values())
    if not total:
        return "unknown"
    significant = sorted(k for k, v in groups.items() if v / total >= .1)
    if len(significant) >= 2:
        return "mixed_python_jsts" if significant == ["jsts", "py"] else "mixed_other"
    dominant = max(groups, key=groups.get)
    return ({"java": "java_dominant", "py": "python_dominant", "jsts": "jsts_dominant"}.get(
        dominant, dominant + "_dominant") if groups[dominant] / total >= .8 else "other")


def validate_registration(record, exposed_families=()):
    required = {"schema_version", "study_id", "repository_id", "canonical_url", "provider_repository_id",
                "family_id", "source_license_spdx", "data_reuse_terms", "source_reference", "source_digest",
                "exposure_status", "exposure_evidence_refs", "reserved_role", "branch_reference",
                "branch_reference_observed_at", "tip_sha", "lineage_policy", "declared_languages",
                "scope_policy_hash", "study_mode"}
    if set(record) != required or record["schema_version"] != 2:
        raise ValueError("Exact schema-v2 registry fields required")
    for key in ("study_id", "repository_id", "family_id", "provider_repository_id", "source_reference", "branch_reference"):
        if not isinstance(record[key], str) or not record[key]:
            raise ValueError("Missing repository identity")
    if not record["canonical_url"].startswith("https://") or "@" in record["canonical_url"]:
        raise ValueError("Credential-free canonical HTTPS URL required")
    if record["study_mode"] not in MODES or record["lineage_policy"] != "COMPLETE_FIRST_PARENT":
        raise ValueError("Explicit supported study/lineage mode required")
    if record["reserved_role"] not in ("development", "held_out", "quarantine"):
        raise ValueError("Unknown family role")
    if record["exposure_status"] not in ("EXPOSED", "UNEXPOSED", "UNRESOLVED"):
        raise ValueError("Unknown exposure status")
    if record["reserved_role"] == "held_out" and (record["family_id"] in exposed_families or record["exposure_status"] != "UNEXPOSED"):
        raise ValueError("Exposed/unresolved families cannot be new held-outs")
    if record["reserved_role"] != "quarantine" and any(not isinstance(record[k], str) or record[k].strip().lower() in MISSING_WORDS for k in ("source_license_spdx", "data_reuse_terms")):
        raise ValueError("Source and data rights must be independently documented")
    if not record["declared_languages"] or len(set(record["declared_languages"])) != len(record["declared_languages"]):
        raise ValueError("Unique declared languages required")
    if set(record["declared_languages"]) - set(SUFFIXES.values()):
        raise ValueError("Language needs an explicit capability/scope extension")
    if record["scope_policy_hash"] != SCOPE_ID:
        raise ValueError("Unsupported scope policy")
    hash_id(record["source_digest"])
    revision(record["tip_sha"])
    utc(record["branch_reference_observed_at"])
    return digest(record)
