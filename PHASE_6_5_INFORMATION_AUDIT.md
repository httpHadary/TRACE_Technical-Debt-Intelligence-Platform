# Adaptive Persistence: what is missing from the information set?

Starting commit: `26dea4942d934d1f3325096ed1ca452b39bf3ba8`.
This audit precedes Phase 6.5 fitting. Existing results are read-only evidence.

Phase 6.2's largest reported 90-day gain came from an anchored trend baseline.
Phase 6.3 had an unsafe selector fallback; the isolated Phase 6.4 repair explicitly
returns persistence when safety or validation evidence is insufficient. That repair
is complete; another threshold search is not the principal scientific need.
Phase 6.4 R1 main-test gains of 2.81/7.89/7.34% did not recur in R2, which selected
persistence. R1 unseen-mechanism error rose 10.39/20.34% at 60/90 days. Direction
confidence and feature-neighbor distance did not identify a changed future mapping.
Main nominal 80% coverage near 79–82% did not prevent hidden-future stress coverage
of 42–63%. Five OOD cells also lacked sufficient large-increase support. These are
published observations, not newly rerun old experiments.

## Evidence-ranked explanations

| Explanation | Evidence | What would falsify or narrow it? |
| --- | --- | --- |
| A similar past can lead to a different future relationship | Phase 6.4 reversal-family losses and identical-history branch control | New origin-known observations that distinguish branches and improve matched independent forecasts |
| Persistent stock is often the absolute-loss optimal action | Frozen baseline advantage; finite-distribution median identity | Demonstrate a nonzero conditional median on new admitted information, then independent gains |
| Familiar-generator validation is not transport validation | Main versus unseen results; different R1/R2 admission | Repository/mechanism-held-out development selection and independent temporal testing |
| High-confidence direction is not calibrated future knowledge | Direction scores coexist with low movement recall and OOD losses | Probability reliability and forecasting-risk evidence in the intended deployment domain |
| Calibration shift and conditional errors explain poor coverage | Main versus hidden-future coverage | Matched delayed-label online calibration with width/score constraints, rather than post-test widening |
| Real Git/process information may help | Prior contracts and related literature only | New rights-cleared as-of data, history-versus-process ablations and repository-held-out tests |

The final row is a hypothesis. Public source visibility, recent activity, author
counts, declared plans and future refactoring realization are not interchangeable.
The project has no admitted independent real cohort for this new question. The
old exposed Java tests cannot certify a newly selected method.

## Decision-theoretic information limit

For absolute loss, an optimal point action is a conditional median. Persistence
is optimal whenever current stock is a conditional median; at least 50% probability
mass at no change is sufficient but not necessary. A useful risk signal can improve
a probability forecast without changing that median or improving point MAE.
This distinction follows the scoring-functional analysis in
[Gneiting (2011)](https://www.bundesbank.de/resource/blob/635562/7d3de0f3fc003e5b4864828143f268cf/mL/2012-06-01-eltville-11-gneiting-paper-data.pdf).

For identical inputs with balanced endpoints c−a, c, c+a (0<a<=c), c minimizes the
sum of absolute losses. For paired endpoint laws reflected about c, changing an
action in one direction cannot strictly improve absolute loss in both worlds.
These are restricted mathematical examples, not a theorem that all technical-debt
changes are unpredictable. A past-only model cannot distinguish two worlds with
identical input distributions and opposite outcome relationships without labels,
additional signals or defensible structural assumptions.

The survey by [Gama et al. (2014), author copy](https://www.liaad.up.pt/area/jgama/reviewCD_methods.pdf)
provides the concept-drift context. A feature-distance check alone is insufficient
when the conditional future relationship changes without an input shift.

## Research direction

Evaluate information groups and their availability before adding model complexity:
debt history; complete past activity; versioned origin-known intent; reliable
measurement/scope/domain context. Separate detecting a change already observed
from forecasting a change not yet observed. Use delayed realized labels to monitor
risk after deployment, with the delay enforced separately for every horizon.
Do not claim this can prevent the first invisible regime change.

A just-in-time study examined product/process metrics at commit granularity:
[Bernardi et al. (2022), publisher abstract](https://doi.org/10.1016/j.jss.2022.111481).
Its setting motivates possible inputs; it does not validate calendar-horizon skill
or license any data here. Only the accessible abstract/metadata was reviewed;
publisher full-text retrieval returned 403. No study data was acquired.

[Adaptive conformal inference, Gibbs and Candès (2021)](https://arxiv.org/abs/2106.00170v3)
is an online feedback method. Its long-run coverage objective is distinct from
point forecast skill and per-case coverage. It cannot be imported as an immediate
shift guarantee for frozen residual intervals or unavailable future outcomes.

The next experiment is an information-intervention engineering control, not another
claim to discover real software behavior from a synthetic leaderboard. Any positive
signal result is conditional on the deliberately constructed synthetic relationship.
