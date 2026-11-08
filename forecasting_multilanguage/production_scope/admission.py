"""Versioned strict admission. Legacy state/time/domain checks retained explicitly.

Constructor is isolated to preserve frozen v2 byte-for-byte; shared algorithms
remain in the original contracts and Git modules. No scan or live API path.
"""
from ..contracts import utc
from ..admission import PastStore as LegacyPastStore


class PastStore(LegacyPastStore):
    """Admitted observations only; no label-store parameter or future-value query."""
    def __init__(self, registration, domain, lineage, observations, coverage_proofs):
        from .registry import validate_registration
        validate_registration(registration)
        from .scope import ScopedGit
        if not isinstance(lineage, ScopedGit) or lineage.repository_id != registration["repository_id"]:
            raise ValueError("New-study scoped lineage required")
        if not isinstance(coverage_proofs, dict):
            raise ValueError("Verified archive coverage proofs required")
        if domain["status"] != "COMPLETE":
            raise ValueError("Incomplete analyzer domain is not strict evidence")
        from ..contracts import analyzer_domain
        if analyzer_domain(domain["manifest"]) != domain:
            raise ValueError("Analyzer domain identity mismatch")
        manifest = domain["manifest"]
        if manifest["metric_mode"] != "STANDARD" or manifest["metric_semantics"] != "native_sqale_index_minutes_v1":
            raise ValueError("First study admits native Standard maintainability minutes only")
        requirements = {"java": {"java_compiled"}, "cs": {"dotnet_begin_build_end"},
                        "cpp": {"cfamily_compilation_database"}}
        for language in registration["declared_languages"]:
            if language in requirements and manifest["build_mode"] not in requirements[language]:
                raise ValueError("Compiled language requires its registered build-aware analyzer mode")
        if manifest["scope_policy_sha256"] != registration["scope_policy_hash"]:
            raise ValueError("Scope mismatch")
        if set(registration["declared_languages"]) - {p["language"] for p in manifest["plugins"]}:
            raise ValueError("Missing declared language analyzer")
        if lineage.tip != registration["tip_sha"] or lineage.observed_at != registration["branch_reference_observed_at"]:
            raise ValueError("Lineage is not bound to registration")
        if registration["reserved_role"] == "quarantine":
            raise ValueError("Quarantined source cannot enter strict study")
        self.registration, self.domain, self.lineage = registration, domain, lineage
        self.mode = registration["study_mode"]
        self.observations = []
        identities, native_ids, states = set(), set(), {}
        for obs in observations:
            from .archive import verify_coverage
            if obs.observation_id not in coverage_proofs:
                raise ValueError("Missing exact-file coverage proof")
            verify_coverage(lineage, obs, coverage_proofs[obs.observation_id])
            key = (obs.commit_sha, obs.domain_id, obs.scope_id)
            if (obs.repository_id != registration["repository_id"] or obs.family_id != registration["family_id"]
                    or obs.domain_id != domain["domain_id"] or obs.scope_id != registration["scope_policy_hash"]
                    or obs.commit_sha not in lineage.by_sha or obs.source_tree_sha != lineage.by_sha[obs.commit_sha].tree
                    or utc(obs.state_utc) != utc(lineage.by_sha[obs.commit_sha].timestamp)):
                raise ValueError("Observation code/domain/repository identity mismatch")
            if obs.observation_id in identities or obs.analysis_id in native_ids:
                raise ValueError("Duplicate observation/native analysis identity")
            values = {k: (v.value, v.status, v.unit) for k, v in obs.measures.items()}
            if key in states and states[key] != (values, obs.languages):
                raise ValueError("Contradictory same-state measurements")
            if any(obs.languages.get(k, 0) <= 0 for k in registration["declared_languages"]):
                raise ValueError("Declared language missing from measured coverage")
            if {k for k, value in obs.languages.items() if value > 0} != set(registration["declared_languages"]):
                raise ValueError("Measured language scope differs from declared production scope")
            if tuple(sorted(obs.production_paths)) != lineage.production_paths(obs.commit_sha):
                raise ValueError("Archived inventory differs from exact Git production scope")
            from .scope import classify
            if {classify(registration["repository_id"], p)[1] for p in obs.production_paths} != set(registration["declared_languages"]):
                raise ValueError("Declared language set differs from actual production inventory")
            if "sqale_index" not in obs.measures or obs.measures["sqale_index"].unit != "estimated_remediation_minutes":
                raise ValueError("Native minute measure required")
            from ..registry import language_family
            from .scope import policy
            if language_family(obs.languages) != policy(registration["repository_id"])["target"]:
                raise ValueError("Native NCLOC does not confirm the registered language stratum")
            identities.add(obs.observation_id)
            native_ids.add(obs.analysis_id)
            states[key] = (values, dict(obs.languages))
            self.observations.append(obs)
        self.observations.sort(key=lambda o: (utc(o.state_utc), o.analysis_id))
