"""Metadata-only family isolation and strict context/label interval purging."""
from datetime import timedelta
from .contracts import utc, horizon_endpoint


def validate_cohorts(registrations, exposed_families=()):
    from .registry import validate_registration
    families, urls, providers = {}, {}, {}
    for record in registrations:
        validate_registration(record, exposed_families)
        family, role = record["family_id"], record["reserved_role"]
        if family in families and families[family] != role:
            raise ValueError("Family crosses cohort roles")
        for value, seen in ((record["canonical_url"].rstrip("/").removesuffix(".git").lower(), urls),
                            (record["provider_repository_id"], providers)):
            if value in seen and seen[value] != family:
                raise ValueError("Unresolved alias/family identity")
            seen[value] = family
        families[family] = role
    return families


def purged_training_ids(origins, validation_boundary):
    first_input = utc(validation_boundary) - timedelta(days=90)
    identities = [o["forecast_id"] for o in origins]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate forecast identity")
    return sorted(o["forecast_id"] for o in origins
                  if utc(horizon_endpoint(o["origin_utc"], o["horizon_days"])) < first_input)
