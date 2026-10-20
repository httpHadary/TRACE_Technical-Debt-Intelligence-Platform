# Adaptive Persistence improvement

Synthetic-only successor authorized after Phase6.3. Read
`PHASE_6_4_PREREGISTRATION.md` before executing. No real-data or pretrained route.

From the repository root with the existing NumPy environment:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /home/hp/tst/td_pipeline_module_level/td_pipeline/.venv-forecast/bin/python \
  -m forecasting_research.phase6_4 prepare \
  /home/hp/tst/research/forecasting_mvp/phase6_4/YYYY-MM-DD/new-study
```

Inspect registration and run permitted deterministic tests before replacing
`prepare` with `run` once. Paths and attempts are exclusive. The new selector
always retains zero adjustment when no candidate qualifies. The archived Phase6.3
selector is unchanged and must not be imported for new selection.

`Predictor.predict(Request, horizon, method, config)` receives past values and
timestamps only. Models store synthetic training-neighbor features/deltas; those
large private model artifacts are not published. Model states cannot be interpreted
as admission for future data or release of any restricted analyzer outputs.
