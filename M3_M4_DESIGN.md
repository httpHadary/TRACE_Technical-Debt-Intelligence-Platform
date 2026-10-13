# M3/M4 data and architecture specification

Milestone 1 implements the dataset/evaluation interfaces, not neural training.
The schema is `module-forecast-v1`; feature order is recorded in `manifest.json`
and enforced by `forecasting.interfaces.ForecastDataset`.

## Inputs and causal availability

For an origin `(repository, stable_module_id, t)`, `sequence(origin_id)` returns:

- `values`: `[26, F]`, ordered oldest to current, with `SEQUENCE_FEATURES` order.
- `feature_mask`: `[26, F]`; false means unknown, not zero.
- `snapshot_mask`: `[26]`; false means absent module/snapshot or incompatible analyzer.
- `timestamps`: the exact 26 weekly cutoffs ending at `t`.

`graph_window(origin_id)` returns a list of 26 repository graph frames. Each
frame contains `cutoff`, ordered `node_ids`, `[N_t, F]` values and masks,
typed `(source_index, target_index, weight)` relations, `origin_node_index`
and `graph_available`. Node counts and order may change between frames. Join
through stable module IDs, never assume row index consistency between weeks.
Undirected co-change/contributor relations are expanded in both directions;
dependency direction is preserved. Birth/deletion creates missing sequence frames.

Fit per-feature imputation/scaling on **training frames only**, using observed
values. Concatenate numerical inputs with missingness indicators. Never use
label availability to construct node features or remove unlabelled neighbors.
Never include neighboring targets, future topology, endpoint membership,
future analyzer statuses or learned embeddings fitted on test labels.

All frames pass the same feature-cutoff checks as M1/M2. The interface compares
each frame's analyzer signature to the origin: incompatible frames have false
feature masks, no relation messages and `graph_available=false`. Partial build
extraction remains visible through coverage/status and must not be interpreted
as proof that unresolved dependencies are absent.

## M3: causal TCN

Input `[B, 26, F]` plus masks -> training-only numeric preprocessing -> concatenate
feature masks and snapshot availability -> `[B, channels, 26]` -> causal residual
TCN -> select current timestep -> debt regression and optional growth heads.

Initial experiment: 32 channels, kernel 3, dilations 1/2/4/8, two causal
convolutions per residual block, dropout 0.1. Left padding only; no centered
convolutions or batch normalization that mixes future sequence positions.
The receptive field covers all 26 weeks. These are predefined starting settings,
not claims of optimality. Hyperparameter choices use inner temporal validation,
never the exported outer test period.

## M4: relation-aware GraphSAGE -> causal TCN

At **each** historical cutoff `u`:

1. Form node input `X_u` from observed current metrics, coverage and masks.
2. Apply two 32-dimensional GraphSAGE layers separately by relation, using mean
   aggregation. Preserve incoming and outgoing dependency channels explicitly;
   retain co-change/contributor weights through weighted mean aggregation.
3. Combine relation outputs by concatenation followed by a linear projection,
   GELU and dropout. Keep relation-availability masks as inputs.
4. Extract the embedding for the origin's stable module ID. If absent or
   incompatible, emit a masked frame; do not insert a healthy zero embedding.
5. Stack these embeddings as `[B, 26, 32]`, append availability masks, and feed
   them through the same causal TCN contract as M3.

In parallel, process current origin metrics and their masks through a small
32-dimensional MLP. Concatenate the TCN's current representation with this
current-state embedding -> linear/GELU/dropout fusion -> prediction heads.

The initial heads are signed SQALE change (Huber loss) and growth logit (binary
cross-entropy). The growth label uses the manifest's predefined minutes threshold.
Missing labels are masked in losses; regression and classification use the same
eligible origins as M0–M2 for comparison. Loss weights are predefined or tuned
inside training validation. A finding-count head remains deferred until reliable
finding identity and arrival-label evidence exist.

## Evaluation and stop gates

Reuse `folds.json` cohorts without random row splits. Use label-end-time purging,
repository-held-out variants, and the same primary metrics/target definitions.
Only perform fit/transform operations on training data. Graph test inputs can
contain observed unlabeled nodes in the same held-out repository graph, but may
not enter supervised fitting. A training batch may reuse historical graphs;
it cannot access an origin's later frames.

Run metric-only TCN, source/build-only graph, co-change-only graph,
contributor-only graph, and complete graph ablations. Match eligible cohorts;
report any loss of coverage explicitly. Evaluate sensitivity to membership
movement and short-history modules. Check learning curves and variability over
repositories/windows before deciding neural data sufficiency.

Do not start M3/M4 training until representative real collection, lineage/label
review, enough purged evaluation windows, and sufficient growth events pass.
Do not claim GraphSAGE–TCN superiority until it improves over M0–M2 under these
shared conditions. Milestone 1 deliberately installs no neural dependencies.
