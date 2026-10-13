"""Shared data/evaluation boundaries for later M3/M4 and matched F1/F2 comparisons."""
from datetime import timedelta
from pathlib import Path

import numpy as np

from contracts import read_csv
from .dataset import KEYS, verify_dataset
from .schema import SEQUENCE_FEATURES, assert_available, finite, iso, timestamp


class ForecastDataset:
    def __init__(self, path):
        self.path = Path(path)
        self.manifest = verify_dataset(path)
        self.states = read_csv(self.path / "module_weekly_state.csv", key="observation_id")[1]
        self.states_by_id = {r["observation_id"]: r for r in self.states}
        self.graphs = read_csv(self.path / "module_graph_features.csv", key="observation_id")[1]
        self.graphs_by_id = {r["observation_id"]: r for r in self.graphs}
        self.edges = read_csv(self.path / "module_edges_weekly.csv")[1]
        self.arrays = dict(np.load(self.path / "module_sequences.npz", allow_pickle=False))
        self.sequence_indices = {str(v): i for i, v in enumerate(self.arrays["observation_ids"])}
        if set(self.sequence_indices) != set(self.states_by_id) or len(self.sequence_indices) != len(self.states):
            raise ValueError("Sequences and origins differ")
        if tuple(self.arrays["feature_names"]) != SEQUENCE_FEATURES:
            raise ValueError("Sequence feature schema mismatch")
        expected = (len(self.states), self.manifest["sequence_weeks"], len(SEQUENCE_FEATURES))
        if self.arrays["values"].shape != expected or self.arrays["feature_mask"].shape != expected:
            raise ValueError("Invalid sequence shapes")
        if self.arrays["snapshot_mask"].shape != expected[:2] or self.arrays["timestamps"].shape != expected[:2]:
            raise ValueError("Invalid sequence availability shapes")
        if self.arrays["feature_mask"].dtype != bool or self.arrays["snapshot_mask"].dtype != bool:
            raise ValueError("Boolean availability masks required")
        if np.any(self.arrays["feature_mask"] & ~self.arrays["snapshot_mask"][:, :, None]):
            raise ValueError("Observed feature in absent snapshot")
        if not np.isfinite(self.arrays["values"]).all():
            raise ValueError("Nonfinite sequence storage")
        for row in self.states:
            times = self.arrays["timestamps"][self.sequence_indices[row["observation_id"]]]
            expected_times = [iso(timestamp(row["prediction_timestamp"]) - timedelta(weeks=i))
                              for i in reversed(range(self.manifest["sequence_weeks"]))]
            if list(times) != expected_times:
                raise ValueError("Noncausal/nonweekly sequence cutoffs")

    def sequence(self, observation_id):
        index = self.sequence_indices[observation_id]
        return {key: self.arrays[key][index].copy() for key in ("values", "feature_mask", "snapshot_mask", "timestamps")}

    def graph_window(self, observation_id):
        """Entire repository graphs as of each historical week, with stable node order.

        No neighboring targets are returned. Undirected relations are expanded to
        two messages; dependency source -> target remains directed.
        """
        origin = self.states_by_id[observation_id]
        result = []
        for date in self.sequence(observation_id)["timestamps"]:
            nodes = sorted([r for r in self.states if r["repository_id"] == origin["repository_id"]
                            and r["prediction_timestamp"] == date], key=lambda r: r["stable_module_id"])
            signatures = {r["analyzer_signature"] for r in nodes}
            if len(signatures) > 1:
                raise ValueError("Inconsistent analyzer metadata within graph frame")
            compatible_frame = not signatures or signatures == {origin["analyzer_signature"]}
            node_index = {r["stable_module_id"]: i for i, r in enumerate(nodes)}
            values = np.zeros((len(nodes), len(SEQUENCE_FEATURES)))
            mask = np.zeros_like(values, dtype=bool)
            for i, node in enumerate(nodes):
                graph = self.graphs_by_id[node["observation_id"]]
                if graph["analyzer_signature"] != node["analyzer_signature"]:
                    raise ValueError("Graph analyzer identity differs from state")
                assert_available(origin["prediction_timestamp"], [node["max_feature_timestamp"], graph["max_feature_timestamp"]])
                for j, feature in enumerate(SEQUENCE_FEATURES):
                    value = finite(node.get(feature, graph.get(feature)))
                    if value is not None and compatible_frame:
                        values[i, j], mask[i, j] = value, True
            relations = {}
            for edge in self.edges:
                if edge["repository_id"] != origin["repository_id"] or edge["prediction_timestamp"] != date:
                    continue
                assert_available(origin["prediction_timestamp"], [edge["max_feature_timestamp"]])
                if edge["source"] not in node_index or edge["target"] not in node_index:
                    raise ValueError("Graph edge references unavailable node")
                a, b = node_index[edge["source"]], node_index[edge["target"]]
                weight = finite(edge["weight"])
                if weight is None or weight < 0:
                    raise ValueError("Invalid graph edge weight")
                if not compatible_frame:
                    continue
                relations.setdefault(edge["edge_type"], []).append((a, b, weight))
                if edge["directed"] == "0":
                    relations[edge["edge_type"]].append((b, a, weight))
            result.append({"cutoff": str(date), "node_ids": list(node_index), "values": values,
                           "feature_mask": mask, "relations": relations,
                           "origin_node_index": node_index.get(origin["stable_module_id"]),
                           "graph_available": bool(nodes) and compatible_frame,
                           "compatibility_status": "COMPATIBLE" if compatible_frame else "INCOMPATIBLE_ANALYZER"})
        return result


def aggregate_file_predictions(membership, file_predictions, module_origins):
    """F2: sum file delta forecasts over ONLY prediction-time module membership.

    Prediction identity = (repository_id, stable_file_id, prediction_timestamp).
    Requires a complete forecast population. Growth probabilities require a later
    calibrated aggregation model; summing file probabilities is invalid.
    """
    forecasts = {}
    for row in file_predictions:
        key = tuple(row[k] for k in ("repository_id", "stable_file_id", "prediction_timestamp"))
        if key in forecasts:
            raise ValueError("Duplicate file prediction")
        assert_available(row["prediction_timestamp"], [row["max_feature_timestamp"]])
        value = finite(row["predicted_debt_delta_minutes"])
        if value is None:
            raise ValueError("Missing file forecast")
        forecasts[key] = value
    result = []
    for origin in module_origins:
        members = [r for r in membership if all(r[k] == origin[k] for k in KEYS)]
        keys = [tuple(r[k] for k in ("repository_id", "stable_file_id", "prediction_timestamp")) for r in members]
        if not members or len(keys) != len(set(keys)) or any(k not in forecasts for k in keys):
            raise ValueError("Incomplete/duplicate prediction-time file population")
        result.append({**{k: origin[k] for k in KEYS}, "predicted_debt_delta_minutes": sum(forecasts[k] for k in keys),
                       "max_feature_timestamp": origin["prediction_timestamp"]})
    return result


def align_external_predictions(cohort, predictions):
    """F1/F2 or M3/M4 must match an exported fold cohort exactly, without row dropping."""
    expected = {r["observation_id"]: r for r in cohort}
    actual = {}
    for row in predictions:
        if row["observation_id"] in actual:
            raise ValueError("Duplicate external prediction")
        actual[row["observation_id"]] = row
    if set(expected) != set(actual):
        raise ValueError("External predictions differ from matched evaluation cohort")
    for oid, origin in expected.items():
        row = actual[oid]
        if any(row[k] != origin[k] for k in KEYS):
            raise ValueError("External scientific identity mismatch")
        assert_available(origin["prediction_timestamp"], [row["max_feature_timestamp"]])
        if finite(row["predicted_debt_delta_minutes"]) is None:
            raise ValueError("Missing external prediction")
    return [actual[r["observation_id"]] for r in cohort]
