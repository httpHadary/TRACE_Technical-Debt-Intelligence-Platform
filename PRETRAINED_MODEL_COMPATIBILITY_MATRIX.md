# Pretrained model compatibility — Phase 6.0

Checked 2026-10-19 using official metadata/configs and the existing local runtime.
No model/dependency was acquired or installed. Documented API capability,
checkpoint license evidence, local availability and execution admission are
separate. Full machine-readable identities, URLs, retrieval hashes and unknowns:
[`model_eligibility.json`](forecasting_research/phase6_0/model_eligibility.json).
Weight hashes for absent candidates are **publisher LFS metadata**, not locally
verified bytes. No technical-debt accuracy is claimed for any untested candidate.

| Candidate | Exact selected revision | Native input/output | License evidence | CPU/resource and decision |
| --- | --- | --- | --- | --- |
| Chronos-2 Small | `autogluon/chronos-2-small@ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a` | Config capacity 8192 past / 1024 future; unchanged adapter fixed at **90 complete daily past / 90 future**, native q10/q50/q90 | Pinned card and existing admission Apache-2.0; all three local checkpoint files rehashed | Existing pinned CPU environment; eligible for this synthetic run only. Actual resource/validity receipts published separately. |
| Granite TTM r2.1 daily | `ibm-granite/granite-timeseries-ttm-r2`, branch `512-96-ft-r2.1`, commit `3442406f106122f414a11f72b4ebfe4878bec89d` | Fixed512→96, daily frequency-prefix configuration; point `prediction_outputs`. Select native indices29/59/89; no recursive extension required. | Official card/API Apache-2.0 | Weight metadata3,440,416 bytes. CPU/laptop inference documented; RSS/runtime unmeasured. Conditional future candidate on a **512-day eligible context cohort**, not padded90. Not available/executed. |
| Granite short-context r2.1 | `90-30-ft-r2.1@6e5cb8ee51e0634a45637490f5db43148b2fa6be` | Fixed90→30 | Apache-2.0 card evidence | Direct60/90 experiment ineligible. Recursive forecasts would be a separately registered method; never relabel30 outputs as90. |
| Granite r3 main | `ibm-granite/granite-timeseries-ttm-r3@ea17cfd2e3edcaea21eb8dcecd18bf88971482fa` | Inspected main config512→30 with multi-quantile head/deciles; family routing and daily long-horizon API not established here | API/card Apache-2.0 | Deferred. Do not transfer r2 daily branch semantics or infer90-step support from a family name. |
| TimesFM2.5 | `google/timesfm-2.5-200m-pytorch@1d952420fba87f3c6dee4f240de0f1a0fbc790e3` | Up to16384 context; base patch128, continuous quantile head up to1024. Documented `forecast(horizon=90, inputs=[past])`; point plus deciles. Choose native q50 explicitly if comparing medians. No frequency indicator. | Pinned model API/card Apache-2.0; official repo explicitly keeps ≤2.5 weights Apache-2.0 | Weights925,181,104 bytes (~882.3MiB) alone; CPU framework/activations add memory. **2GiB compatibility UNKNOWN**, not inferred from weight size. No installation/download/probe this phase. |

## Integration constraints

The [official Granite r2 card](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2)
distinguishes r2 minutely/hourly models from r2.1 daily/weekly models. It discourages
upsampling/zero-prepending. Use the fixed branch/config, past-only scaling and
verified daily frequency token, not auto-selection fallback or random-init modes.
`distribution_output=student_t` with an MSE point checkpoint is **not proof of a
trained quantile API**. The selected r2.1 candidate has no verified native interval
contract; report interval metrics unavailable unless separately implemented and
validated. r3 quantile fields do not make its complete runtime verified.

The [selected daily config](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2/blob/3442406f106122f414a11f72b4ebfe4878bec89d/config.json)
and [short config](https://huggingface.co/ibm-granite/granite-timeseries-ttm-r2/blob/6e5cb8ee51e0634a45637490f5db43148b2fa6be/config.json)
establish exact lengths. IBM code metadata was recorded at
`3d92535ca4138648b9d1e2f3f1421b5dec4dc3aa`: Python≥3.11,<3.14,
Torch≥2.10,<2.12, Transformers[torch]≥4.57.6,<6, NumPy<3,
pandas≥2.3.3,<4, plus datasets/deprecated/scikit-learn and utilities. Compatible
version ranges alone do not constitute a tested dependency lock.

The [TimesFM2.5 card](https://huggingface.co/google/timesfm-2.5-200m-pytorch/blob/1d952420fba87f3c6dee4f240de0f1a0fbc790e3/README.md)
shows forecast shapes and options. Its sample enables crossing repair; a future
native-path audit must explicitly disable `fix_quantile_crossing`, retain raw
quantiles and reject invalid order. Do not silently normalize point/median
semantics. Pin package code separately from weights: recorded official code SHA
`e51928e27119cb17bebc005be2696b75e0a9e688` has pyproject version3.0.2,
Python≥3.10, NumPy≥1.26.4, huggingface_hub≥0.28.0, safetensors≥0.5.3 and
Torch≥2.0.0 extra. Its archived2.5 API needs a later isolated CPU/lock verification.
No GPU or `torch_compile` requirement is assumed for this project's CPU pilot.

The [current official repository](https://github.com/google-research/timesfm)
also lists TimesFM3.0, whose self-hosted weights have separate noncommercial terms.
It is not silently substituted for2.5. No3.0 revision, acquisition or rights
acceptance is registered. The selected2.5 model remains an independent future
benchmark, not an automatic project default.

## Chronos local proof

Weights SHA256 `492290ae82bb89f9769e3479ce90b3179de1f33e600c34daa0352531538b23cd`;
config `f2780468adc8b16322aa0b6e28b26476c9401ecf64ab53292b6d2b0d3f423722`.
Existing Python3.12.3 / chronos-forecasting2.3.2 / Torch2.11.0+cpu /
Transformers4.57.6 / NumPy2.4.4 / pandas3.0.2 is checked exactly before loading.
CPU float32, eval mode, seed42, deterministic Torch algorithms, batch1,
cross_learning=False, two intra-op/one inter-op threads. The wrapper calls the
unchanged adapter using a clearly synthetic typed bridge; it does not manufacture
historical observation identities or pass historical admission. UTC-naive ns
conversion remains confined to the original model edge.

Sparse/irregular histories are preserved and refused by this adapter, not filled.
A crossing anywhere invalidates the whole path, even if endpoints are ordered;
only that typed native error is recoverable. Unexpected runtime/software errors
abort. Raw values and clipped nonnegative stocks remain distinct. Longer contexts
require a future separately versioned adapter; native capacity is not an already
implemented longer-context experiment. Model licensing does not clear analyzer
output/data-use permissions, which remain unchanged.
