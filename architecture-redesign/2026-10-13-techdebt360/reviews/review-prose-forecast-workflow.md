# Forecast/workflow editorial repair

Date: 2026-10-13. Read both complete current documents before editing and reread both after repair. Scope: `FORECASTING_RESEARCH_PLAN.md` and `END_TO_END_WORKFLOW.md` only, plus this review note. No implementation, configuration changes, installs or experiment execution.

- Separated joined ordinary words, numbers and units throughout the forecasting protocol, stage table and recovery prose. Preserved counts, thresholds, model constraints, API/schema/state identifiers, target names, links and Mermaid flow.
- Clarified existing quantile notation and spaced the metric formula. The common comparison remains central 80% from quantiles 0.1/0.9, with a proposed 75–85% coverage gate. A 90% deployment interval remains a separate validation-only calibration result; the workflow now explicitly references that distinction and requires the displayed level to match it.
- Semantic reread confirmed the native-step grid rule remains intact: 13 weekly steps equal 91 days; exact90 is not rounded to 12/13 weekly steps; irregular next-k observations remain a separate target. Input imputation does not create labels, model admission remains conditional, and no runtime/accuracy claim was added.
- Preserved immutable provenance, conservative missingness/lineage, isolated patch verification, approval binding, external CE recovery and capability revocation semantics. Existing source/configuration and other design documents were not edited.

Result: prose repair complete; no new semantic finding in the edited passages.
