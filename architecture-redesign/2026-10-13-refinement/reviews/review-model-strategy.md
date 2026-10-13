# Model strategy review and repairs

Reviewed 2026-10-13: [PRETRAINED_MODEL_STRATEGY.md](../PRETRAINED_MODEL_STRATEGY.md), against the freshly verified [model digest](../digests/model-reverification.md). Scope: technology contracts and editorial clarity. Repairs were applied only to the newly authored strategy document. This review record is the only other artifact written by this pass. No original source, application, configuration or other root document changed. No model load, scan, inference, training or runtime compatibility test ran.

## Factual repairs applied

| Location | Original gap | Repair and consequence |
|---|---|---|
| Exact contracts; classifier semantics | Four outputs and semantic labels were compressed together, concealing inconsistent checkpoint metadata and the mapping's provenance. | Explicit logits/sigmoid `(B, 4)` shapes; generic `LABEL_0`–`LABEL_3`; inconsistent two-entry `label2id`; upstream order DESIGN, IMPLEMENTATION, DEFECT, TEST; independent sigmoid and author logit > 0 threshold. Mapping and calibration still require execution checks. |
| Exact contracts; resource facts | CodeAid 40–48 GB / 12–16 GB and Qwen 20–24 GB / 8–12 GB deployment envelopes were unsupported by the verified digest. | Removed those ranges. Retained source-backed raw parameter payload estimates and Sonar's explicit publisher 48 GB+ BF16 VRAM / 100 GB storage requirement. No estimate is now presented as a tested host minimum. |
| CodeAid row | Generated smell text obscured the public structured training schema and vocabulary conflict. | Listed main/dependency inputs, `couplingSmells` fields, and card Excessive Dependencies versus dataset Middle Man mismatch. Exact prompt serialization and decoding remain unresolved. |
| Generator contracts | Explanation/unified-diff output looked like an established pretrained model contract. | Distinguished generated tokens/text from proposed application explanation/patch formats that must be validated. Qwen's default 32,768 context remains distinct from a YaRN variant. |
| Forecast tensors | Native model structures and adapter normalization were not clearly separated. | Added proposed adapter `(B, H)` point / `(B, H, Q)` quantile contract; TimesFM mean plus deciles and TTM quantile-axis conversion are explicit. Native return structures require shape checks. |
| TTM branch table | “Grid points” could imply that padding or unknown snapshots satisfy native observed-context admission. | Requires actual context at each origin; preserves weekly 52→16→13, daily 90→30, 180→60 and 512→96→90. Reused unchanged-state points must be identified and assessed separately. Complete origins need context plus real evaluation observations. |
| TTM loader | Bare-SHA dispatch and default mapping were present but difficult to interpret. | Preserved explicit decomposed class plus immutable SHA. Explained `-dec-` dispatch hazard, `prefer_known_mappings=True` longer-branch behavior and direct-selection option. Example is labeled a proposed contract, not a completed load test. |
| TTM masks and outputs | Past-mask defaults, axis order and gap sensitivity lacked enough detail for a runner. | Added `(B, L, K)` values/masks, false masks for zero-filled missing values, all-observed default when mask absent, one-channel/null-exogenous checked configs, `(B, H, K)` points and inspected `(B, Q, H, K)` quantiles. LOWESS gap robustness remains unverified. |
| TTM 0.5 semantics | A compressed warning could be read as a claim about a verified median or calibration. | Explicitly retained `mq_q50_type="mean"`; forbids assuming a calibrated statistical median or renaming the slot. Coverage, crossing and point semantics require measurement. |
| Admission and promotion | “Research admission” required resolved execution licensing, conflicting with the document's promise to keep unresolved classifiers in the research agenda. | Separated planning admission, execution admission and product validation. Unknown licensing remains a weight-execution/adoption condition; it is not a poor-performance result or blanket rejection. |

Supporting primary links are embedded in the repaired strategy and digest. All eleven exact requested IDs, original immutable checkpoint revisions and four TTM task revisions remain present. Controls are temporary comparison candidates; the provisional four-model stack remains one classifier, one embedding model, one generator and one forecaster.

## Editorial repairs applied

Joined prose words, quantities and abbreviations were rewritten throughout the introduction, role table, eleven-checkpoint table, environment lock, TTM policy and promotion sections. Examples include `All11requested`, `retainonewinner`, `licenseunresolved` and numerical metric strings that merged F1 with values. Added consistent spaces around quantities, arrows and punctuation, and expanded ambiguous compressed labels. Code identifiers, checkpoint IDs, revision hashes, URLs and literal query prefixes were preserved.

Dense contract prose was moved into dedicated classifier, forecast tensor and TTM paragraphs. Readers can now distinguish source-backed model behavior, proposed adapter behavior, estimates and future execution checks without reconstructing compressed text.

## Unverified concerns retained

- Tesoro and TechDebtClassifier weight licenses remain unresolved. Public code/Space licenses do not settle them.
- No exact checkpoint was loaded. Tensor integrity, native output shapes, tokenizers, remote code, precision, package compatibility and resource measurements remain execution work.
- Tesoro label semantics rely on the author dataset schema, not a checkpoint-specific semantic mapping file. Reported random-fold averages do not establish local or project-disjoint efficacy.
- CodeAid's card/schema vocabulary discrepancy and exact inference serialization remain unresolved. Sonar generation-quality benchmarks do not demonstrate existing-code detection or safe local repair.
- TTM short-context branches are real artifacts but have no retrieved weekly/daily software-debt accuracy evidence. Immutable class dispatch, prediction cropping, missing-mask/decomposition behavior and 0.5 point semantics still need tests.
- Current model artifacts and package manifests can be pinned, but no tested environment lock exists. All payload estimates exclude runtime overhead.
- Experiments A/B must establish local task value and comparative cost before primary selection. No permanent ensemble or unmeasured efficacy is implied by this strategy.

## Text-only verification

Checked that all 11 requested exact IDs remain present, representative joined-prose defects are absent, and the unsupported deployment-memory ranges were removed. This is artifact inspection, not model/runtime validation.
