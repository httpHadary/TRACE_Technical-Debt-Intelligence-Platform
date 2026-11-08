# Final semantic citation and model-contract review

Reviewed 2026-10-13: `PRETRAINED_MODEL_RESEARCH.md`, `RESEARCH_SUMMARY.md`, source digests, `MODEL_EVALUATION_PLAN.md`, `FORECASTING_RESEARCH_PLAN.md` and final architecture contracts. Review-only output; no other file changed.

**Verdict: primary model conclusions are defensible; one high consistency blocker requires correction before handoff.** No unsupported accuracy winner or guaranteed deployment-hardware claim found. Most caveats are appropriately explicit. Three medium/low presentation or citation issues remain below.

## H1 — Patch verification status differs between architecture and evaluation

`OPTIMAL_SYSTEM_ARCHITECTURE.md`, Remediation verification, says “Compile failure or a failed required test is FAILED.” `MODEL_EVALUATION_PLAN.md`, Remediation outcome, makes **baseline failure PARTIALLY_VERIFIED**, reserving FAILED for confirmed regression. Architecture also permits EVIDENCE_VERIFIED when all checks pass without explicitly requiring the targeted finding to be resolved with identity support, while evaluation requires that condition. An unchanged, behavior-preserving patch can satisfy the architecture status but fail the study endpoint.

**Required fix:** define one shared minimum policy: baseline inability or missing required evidence → PARTIALLY_VERIFIED; candidate regression/failed required check against a valid passing baseline → FAILED; EVIDENCE_VERIFIED requires supported target resolution, exact identity, complete minimum checks, no prohibited introduced findings and no suppression/deletion trick. Keep human approval separate, including approval of partial export without upgrading verification. Update the architecture language or link it directly to this binding shared status definition. This is a handoff blocker, not an implementation request.

## M1 — Summary citation [8] does not directly establish the CE/export assertion

The [Java docs](https://docs.sonarsource.com/sonarqube-server/analyzing-source-code/languages/java) directly support bytecode requirements for projects with more than one Java file. The cited [migration TRANSFER notes](https://github.com/SonarSource/sonar-migration-tool/blob/main/docs/TRANSFER.md) describe issue-history replay, closed/fixed omissions and synthetic historical aggregate reconstruction. They support caution about historical reconstruction, but do **not** directly establish that a CE success cannot certify pagination, revision and exact export binding in this collector.

**Fix:** split finding 6 into the sourced bytecode/reconstruction facts and a clearly identified architectural inference: “therefore this design validates and archives exact exports.” For the collector-specific CE/revision/export assertion, cite the local audit and exact `sonar_evidence.py`/collector evidence rather than implying the migration document specifies this collector contract. The conclusion remains sensible; attribution should be narrower.

## M2 — Joined prose persists in research summary

`RESEARCH_SUMMARY.md` still contains `means13weeks/91days`, `accessed2026-10-13`, `V2.0.1release2021-11-04`, `recheckby...`, and many merged words in its source appendix/staleness section. The two architecture docs were repaired, but these summary words obscure source dates and confidence boundaries.

**Fix:** restore spaces in natural prose/table cells, preserving exact identifiers, URLs, SHA values and dates. Model research opening also says “a expensive”; fix to “an expensive.” These are readability fixes, not research revisions.

## L1 — Publication correction should cite the actual metadata evidence

The Tesoro TOSEM publication correction is supported: publisher-deposited [Crossref metadata](https://api.crossref.org/works/10.1145/3801745) returns title *Detection of Technical Debt in Java Source Code*, publisher ACM and online/publication date **2026-03-13**. The DOI landing page failed in this independent pass; publication status is nevertheless corroborated by the metadata that the digest records.

**Fix:** add the direct metadata link beside the DOI in the correction paragraph, so the cited accessible source matches the evidence actually read. Do not revert to the arXiv under-review note.

## Verified semantic checks

- **Tesoro:** all three exact configs are multi-label four-output models; generic labels and inconsistent two-entry label2id are explicitly disclosed. Upstream schema/recipe supports four types and normalized functions; no explicit no-debt label is asserted. Benchmarks remain publisher averages, not local transfer guarantees.
- **Diff/issue/defect specialists:** davidgaofc mapping is attributed to its card, cleaning to its Space; karths absent config semantics/licenses and 20-versus-17 collection distinction are preserved; ModernBERT's 0/1 meaning remains unresolved. No inappropriate cross-task accuracy comparison found.
- **Generation/retrieval:** Qwen's 32k config versus optional YaRN 128k, CodeRank's retrieval/prefix/pooling, CodeAid's 14.77B merged generation task and SonarSweep's exact BF16/48GB+ requirement are correctly distinguished. Derived raw weight and quantized payload sizes remain estimates with overhead exclusions. No base gpt-oss quantized requirement is misapplied to SonarSweep.
- **Forecasts:** independently reread all six current configs/API revisions and license metadata. Context/patch/quantile facts and Moirai CC-BY-NC-4.0 match the research. Current Amazon/IBM/Salesforce/Google/Datadog manifests support the stated Python/torch/Transformers conflicts, including TTM torch >=2.10,<2.12 and Uni2TS torch <2.5. Package declarations are explicitly not a proven runtime matrix.
- **Datasets/publications:** summary's NPF 13-week/91-day and unknown-license facts match its card/digest. Zenodo 4534110 publication date is explicitly 2020-08-08, distinct from record creation 2021-02-11. InferFix's ACM metadata gives 2023-11-30 and its primary abstract supports static analyzer + retriever + generator. DLRepay's cited publisher page supports SATD comment/code repayment and March 2024 issue date. Neither establishes TechDebt360 efficacy or novelty.

## Cross-document consistency beyond H1

Exact90 versus approx91, origin/endpoint IDs, immutable TargetContract hashes, abstention and absence of interpolated ground truth are consistent across the architecture and forecasting/evaluation plans. Common 0.1/0.5/0.9 comparisons give an 80% interval; calibrated 90% intervals remain a distinct fitted layer. Architecture's live grant/expiry/revocation checks add operational specificity to the evaluation plan's invalidation rules without contradicting them. Partial human acceptance is separate from scientific verified outcomes.

Scope limitation: primary claims and load-bearing model/summary assertions were checked against this run's retrieved evidence, with targeted live rereads. This is not an exhaustive re-fetch of every linked README or an independent model/dataset experiment. No model was loaded and no scientific outcome was measured. H1 is the only substantive blocker found in this final pass.

## Post-fix independent resolution — 2026-10-13

Re-read current documents after root corrections. **H1 resolved:** solution Remediation verification and spine AD-10 now agree with MODEL_EVALUATION_PLAN: failed baseline/missing required evidence → PARTIALLY_VERIFIED; candidate required-check failure against passing baseline or confirmed regression → FAILED; EVIDENCE_VERIFIED requires supported targeted finding resolution, full minimum checks, no prohibited introduced findings and no hiding tricks. Partial human approval still cannot upgrade scientific status.

**M1 resolved:** summary finding 6 now separates sourced Java-bytecode/historical-reconstruction facts from collector-local CE/export evidence and the archive recommendation as a design inference. **M2 resolved in checked passages:** summary prose, source appendix and staleness dates now have proper spaces. **L1 resolved:** model-research publication correction directly links publisher-deposited Crossref metadata beside the DOI.

Also confirmed the trust/domain refinements: AD-11 and solution deployment explicitly treat build scripts/plugins/tests as untrusted, keep fetch/scanner/administrator secrets out of those phases, separate dependency broker and trusted scanner/export phases, and prohibit candidate changes to test commands, verification policy and analyzer scope/suppressions. AD-4 and solution canonical contracts namespace imported approximate domains with known metadata, explicit null/unknown fields and missing-field flags, without inventing complete own-domain settings. Imported analysis remains IMPORTED_PUBLIC rather than VERIFIED.

**Current verdict: no remaining blocker from this citation/contract lens.** Prior findings remain above as review history; this section supersedes their open status. Runtime/scientific/license gates remain deliberate future conditions, not completed implementation proof.
