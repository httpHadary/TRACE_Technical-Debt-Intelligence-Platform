---
type: technical-academic-deepen
topic: pretrained AI and forecasting admission for TechDebt360
status: complete
created: 2026-10-13
updated: 2026-10-13
---

# Research notes and changes from the earlier design

**Choose a capability-aware pretrained hybrid as the architecture, while leaving the primary scientific contribution undecided until Experiments A and B.** This is the user's revised decision rule, not a finding that either arm outperforms the other. All referenced public sources were accessed on 2026-10-13; living source dates are undated unless the digest records a repository modification or publication date. No experimental or runtime outcome was produced. The metadata status marks completion of this planning artifact, not completion of the experiments.

## Consequential updates

1. **TTM eligibility expands.** Actual R3 weight-bearing branches include 52 → 16, 90 → 30, 180 → 60 and 512 → 96. A 512-context main config is not a family minimum. The weekly 52-point branch supplies a 13-step/91-day comparison; daily 30/60/90-day forecasts use different branches. This establishes declared branch compatibility, not local forecasting accuracy. [1]
2. **TTM adapter correctness is a real seam.** Current loader dispatch uses `-dec-` in a revision string; an immutable bare SHA can select the wrong class. Use the explicit decomposed class and record branch, config and runtime pins. Masked scaling does not prove filled-gap LOWESS robustness, and `mq_q50_type="mean"` must not become a statistical median claim. [2]
3. **Classifier inclusion becomes an experiment priority.** GraphCodeBERT and CodeBERT expose four Java type logits, generic checkpoint labels, and the author's multi-label schema and normalization recipe. They lack a calibrated clean label; weight-use permission is unresolved. They remain shortlisted without invented permission or local efficacy. [3]
4. **V2 is stronger than a vague “no history” conclusion.** Fresh read-only joins find 66,711 uniquely linked measures and Git revisions with exact-second clock agreement. However, 19,954 commits within measured spans have no measure; as-of state selection cannot simply choose the latest measured state. Analysis `DATE` is a naive historical timestamp matching the joined UTC Git times, not proof of scan execution time or historical branch availability. These are local artifact findings, not forecast results. [4]
5. **Exact-date pair counts are diagnostics, not cohort bounds.** The selected state at an exact horizon can reuse an earlier measurement only if it is the actual reachable source state with a compatible domain and complete target coverage. Interpolation or carry-forward across an unmeasured change is invalid. This design inference corrects the old emphasis on just ten raw 90-day repository/date pairs; it creates no new labels. [4]
6. **Public NPF is a separate target and domain.** Its declared 21/28/91-day all-issue effort, unknown license and modern source-only retrospective measurements do not certify 30/60/90-day maintainability forecasts. The toolbox supplies observation-step software, not another independent dataset. These are source-contract and bounded-sample findings, not effectiveness results. [5] [6]
7. **Repair task evidence is distinct.** Qwen and SonarSweep are generation models; their cards do not establish measured labor or verified fixes in this project. Learned-only confirmed issues require `ENGINEERING_CHECKED` evidence plus a separate independent `ACCEPTED`/`REJECTED`/`INCONCLUSIVE` verdict. An analyzer-target case additionally requires finding resolution for `EVIDENCE_VERIFIED`. These are proposed study contracts, not claims established by model cards. No positive repair outcome is assumed. [7]

## Source quality and uncertainty

Metadata, config and API checks verify publisher-exposed artifacts and declared contracts. Same-publisher corroboration is not independent effectiveness validation. Generic benchmark scores in the model document are publisher evidence only; no retrieved source establishes the proposed combination's TechDebt360 accuracy, latency, calibration or superiority. Local read-only sources establish existing implementation and retained artifacts, not public model efficacy. Independent model, data, architecture and experiment reviews identify the assumptions and required future tests.

The biggest remaining questions are runtime and dependency fit, weight licensing, actual eligible as-of historical cohorts, independent gold labels and test coverage, statistical precision, reviewer resources, and useful effect over matched baselines. Each has a prerequisite, experiment or stop condition in the five requested deliverables. A prerequisite failure cannot be counted as a negative accuracy result; an untested patch or acceptable tensor shape cannot be counted as scientific success.

## Sources

| Ref | Supports | Primary source / publisher | Date and status |
|---|---|---|---|
| [1] | Short-context branch assets and configs | [IBM model refs](https://huggingface.co/api/models/ibm-granite/granite-timeseries-ttm-r3/refs), [pinned model catalogue](https://github.com/ibm-granite/granite-tsfm/blob/3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa/tsfm_public/resources/model_paths_config/ttm.yaml) | Checked branches modified 2026-07-02; assets inspected; loading and efficacy unverified |
| [2] | Loader, class, mask and output semantics | [IBM pinned loader](https://github.com/ibm-granite/granite-tsfm/blob/3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa/tsfm_public/toolkit/get_model.py), [pinned model implementation](https://github.com/ibm-granite/granite-tsfm/blob/3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa/tsfm_public/models/tinytimemixer/modeling_tinytimemixer.py) | Source analysis, not execution; exact code revision pinned |
| [3] | Java debt-type and preprocessing contracts; both checkpoint configs | [NamCyan Graph config](https://huggingface.co/NamCyan/graphcodebert-base-technical-debt-code-tesoro/blob/edb7d422be19fe6cc420e01eed154225bb4cdfd8/config.json), [NamCyan Code config](https://huggingface.co/NamCyan/codebert-base-technical-debt-code-tesoro/blob/849dd197ba21ba88651d400af95103c5bc30e21e/config.json), [Tesoro author schema](https://github.com/NamCyan/tesoro/blob/main/data/README.md), [author prediction code](https://github.com/NamCyan/tesoro/blob/main/training/cross_validation.py) | Checkpoints modified 2024-10-26; contracts checked; independent efficacy and weight-use permission unresolved |
| [4] | Dataset provenance and fresh local counts | [TDD maintainer](https://github.com/clowee/The-Technical-Debt-Dataset), [fresh local re-audit](digests/data-reaudit.md) | V2.0.1 release 2021-11-04; DB opened read-only on 2026-10-13; cohort eligibility not yet built |
| [5] | NPF declared targets, schema and license; bounded sample provenance | [MaramAllah raw card](https://huggingface.co/datasets/MaramAllah/NPFDataSet/raw/main/README.md), [public API](https://huggingface.co/api/datasets/MaramAllah/NPFDataSet), [fresh bounded-sample audit](digests/data-reaudit.md) | Uploaded 2026-09-15; card, API and bounded CSV checked; full quality unresolved |
| [6] | Observation-step toolbox behavior | [XAI toolkit source](https://github.com/XAI-toolkit/forecaster-toolbox/blob/master/model_training.py) | Living source; code inspected, not run |
| [7] | Generation task, weight and license declarations; separately proposed verification policy | [Qwen card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct), [SonarSweep card](https://huggingface.co/SonarSource/SonarSweep-java-gpt-oss-20b), [B3 study protocol](RESEARCH_EXPERIMENTS.md#b3-representative-java-repair-study) | Checkpoint modifications 2025-01-12 / 2025-12-15; publisher contracts, not local repair outcomes; B3 remains proposed |

The fresh [model re-verification digest](digests/model-reverification.md) records the inspected configs, APIs, modification dates and publisher claims underlying references 1–3 and 7. The [data re-audit](digests/data-reaudit.md) records read-only local evidence and public target/provenance findings underlying references 4–6. These digests support inspection claims; they do not substitute for experiments.

## Freshness

Recheck current checkpoint licenses, APIs, loaders and dependencies before execution and by 2026-11-13 under the BMAD one-month compatibility-review window. Revisit the candidate landscape and selection by 2027-01-13 under its three-month AI window. These dates are computed from the 2026-10-13 **retrieval review anchor**, not invented publication dates. Recount mutable local artifacts at the next execution phase regardless of calendar windows. Fixed historical data versions and source hashes retain their original provenance; the final allowed-cohort audit remains future work.
