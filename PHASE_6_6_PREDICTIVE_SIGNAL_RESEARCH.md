# Candidate signals and the limits of the supporting evidence

This is bounded research using primary papers, institutional author abstracts,
official documentation and existing project reports. It is not a systematic review
replication, model comparison or permission to acquire any study dataset. Sources
and reviewed sections are recorded in examples/phase6_6/research_sources.json.

## What the literature supports

[Ajibode et al.2024](https://arxiv.org/html/2406.12026v1) reviewed14 primary studies
and identified limited debt-type coverage. This supports careful task definition
and evidence review; it does not establish a universally superior predictor.

[Robredo et al., v2 June2025](https://arxiv.org/html/2408.08095v2) explicitly uses
Technical Debt Dataset v2. Its serialized temporal/product-metric setting motivates
history and product-state ablations, but cannot supply an automatically fresh
independent cohort here. Its own discussion notes sparse analyses and interpolation.
This project must retain actual observation times/missingness and exact-day targets.
The paper's ARIMA+LM description forecasts covariates rather than assuming actual
future product metrics are known. We did not reproduce its results or acquire data.
The review covered specified methods/context sections, not a complete artifact audit.

[Bernardi et al.2022](https://doi.org/10.1016/j.jss.2022.111481), reviewed through the
previously captured primary publisher abstract, motivates product/process metrics
at commit granularity. A commit-level task is distinct from calendar-horizon stock
forecasting. It supplies a hypothesis for new activity ablations, not validated skill
for TechDebt360 or a license grant.

[Maldonado et al.2017, institutional abstract](https://research.tue.nl/en/publications/an-empirical-study-on-the-removal-of-self-admitted-technical-debt/)
studies SATD removal in five projects and associates removal with bug fixes/features.
This motivates testing planned versus realized maintenance. Comment/SATD removal
is not equivalent to reducing native maintainability remediation minutes. The
initial author-PDF URL returned404; the institutional abstract was accessible.

## Candidate priority and required falsification

| Priority | Information family | Plausible predictive value | What would disqualify it? |
| --- | --- | --- | --- |
| P0 | Measurement domain and compatible product state | Separate software changes from analyzer/scope changes; optional size/complexity covariates | Missing rule/profile/scope/version identity, future product values, incompatible native metrics |
| P1 | Actual observed debt history | Endpoint-direction frequency and signed magnitude under persistence | Gain exists only on exposed cohorts, replicated carried states or interpolated history |
| P1 | Complete past activity | Event-risk/absolute-change information, possibly weak directional information | No incremental held-out gain; incomplete windows or current-tip assumptions |
| P2 | Versioned directional intent | Some origin-known plans may anticipate additions/remediation | Requires final issue/PR outcomes; cancellations reverse relation; unavailable historical versions |
| P3 | Reconciled churn and semantic past changes | Incremental magnitude/direction information beyond activity | Basename collisions, future fixing/refactoring evidence or incomplete binary/merge handling |

The machine matrix specifies proposed features, proofs, confounders, falsification
and evidence IDs for each family. All are NOT_VALIDATED_ON_INDEPENDENT_REAL_DATA.
Priority is a research/availability judgment, not measured feature importance.

The smallest useful next feature comparison is F0 debt history against F0+F1
activity/product state, on identical admitted origins. Existing F2 churn stays
disabled. Do not require high-cost text/semantic features before proving a smaller
study; introduce directional intent only when its versions and rights exist.

## Historical availability is an independent evidence problem

[Git's official commit documentation](https://git-scm.com/docs/git-commit) permits
supplied author/committer dates. A commit hash authenticates particular object bytes;
a date alone does not prove branch publication or origin-time observability.
Use complete reachable cutoff lineage plus independently evidenced availability,
or declare a retrospective reconstruction with its narrower claim.

[GitHub's official Events API documentation](https://docs.github.com/en/rest/activity/events)
states a limited300-event/30-day window and latency. A current API call cannot be
assumed to reconstruct a complete old activity or planning stream. Do not fetch
such streams in this phase. Owner archives or a separately approved prospective
capture with immutable record versions are stronger acquisition candidates.

A plan created before origin may contain a future deadline. That deadline is
legitimately known as a PLAN if its original version was available, but neither
execution nor its debt effect is known. Final issue text, merged status, resolution
time and mined future refactoring/fixing labels are prohibited substitutes.

## Remaining scientific uncertainty

No reviewed external result establishes a rights-cleared, fixed-domain,
previously unexposed30/60/90-day cohort for this project. The search was bounded;
it is not proof that no suitable source exists anywhere. The reviewed papers do
not establish a causal effect of an origin-known feature on the target here.

The Phase6.5 signed-intent signal was engineered to be predictive. That result
cannot nominate a real feature or justify deployment. Identical observed inputs
can have different conditional future laws; detecting already-realized change is
not the same as forecasting an unseen one. Feedback-based monitoring can limit
repeated mistakes only after horizon labels genuinely arrive.
