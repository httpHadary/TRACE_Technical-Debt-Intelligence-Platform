"""Pinned CPU Chronos-2 Small adapter. No labels, training or benchmark loop."""
from datetime import timedelta
import math
from pathlib import Path

from contracts import read_json
from .contracts import utc_iso, utc_timestamp
from .io import file_sha256
from .prediction_input import PredictionInput

MODEL_ID = "autogluon/chronos-2-small"
REVISION = "ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a"
WEIGHT_SHA256 = "492290ae82bb89f9769e3479ce90b3179de1f33e600c34daa0352531538b23cd"
CONFIG_SHA256 = "f2780468adc8b16322aa0b6e28b26476c9401ecf64ab53292b6d2b0d3f423722"
QUANTILES = (0.1, 0.5, 0.9)


def verify_checkpoint(root):
    root = Path(root).resolve()
    admission = read_json(root / "checkpoint_admission.json")
    if (admission["model_id"], admission["revision"], admission["license"]) != (MODEL_ID, REVISION, "Apache-2.0"):
        raise ValueError("Only registered immutable Apache-2.0 Chronos checkpoint admitted")
    for name, expected in admission["artifacts"].items():
        if name not in ("config.json", "README.md", "model.safetensors") or file_sha256(root / name) != expected:
            raise ValueError("Checkpoint artifact hash mismatch")
    if admission["artifacts"].get("model.safetensors") != WEIGHT_SHA256:
        raise ValueError("Pinned weight SHA-256 required")
    if set(admission["artifacts"]) != {"config.json","README.md","model.safetensors"} or admission["artifacts"]["config.json"] != CONFIG_SHA256:
        raise ValueError("Pinned configuration and complete checkpoint inventory required")
    config = read_json(root / "config.json")
    chrono = config["chronos_config"]
    if (config["architectures"] != ["Chronos2Model"] or config["chronos_pipeline_class"] != "Chronos2Pipeline"
            or chrono["context_length"] < 90 or chrono["output_patch_size"] * chrono["max_output_patches"] < 90
            or not set(QUANTILES) <= set(chrono["quantiles"])):
        raise ValueError("Checkpoint cannot support registered context/horizon/quantiles")
    return admission


class ChronosSmallAdapter:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    @classmethod
    def load_cpu(cls, checkpoint):
        verify_checkpoint(checkpoint)
        import torch
        from chronos import Chronos2Pipeline
        if torch.version.cuda is not None:
            raise ValueError("Phase 4.1 requires a CPU-only Torch build")
        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        torch.manual_seed(42)
        torch.use_deterministic_algorithms(True)
        pipeline = Chronos2Pipeline.from_pretrained(str(Path(checkpoint).resolve()), device_map="cpu",
            dtype=torch.float32, local_files_only=True, use_safetensors=True, trust_remote_code=False)
        pipeline.model.eval()
        if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in pipeline.model.parameters()):
            raise ValueError("CPU float32 model required")
        return cls(pipeline)

    def predict_path(self, request):
        """One admitted 90-point/90-step series, no cross-learning or covariates.

        h=30/60/90 endpoints are indices 29/59/89 of the saved daily path.
        Median is explicitly native q50. Values retain input target units.
        """
        if not isinstance(request, PredictionInput) or request.track != "core90" or request.horizon_days != 90:
            raise ValueError("Admitted core90 maximum-horizon request required")
        payload = request.model_payload()
        if len(payload["past_values"]) != 90 or any(v is None for v in payload["past_values"]):
            raise ValueError("Complete 90-point past context required")
        import pandas as pd
        # Chronos 2.3.2 normalize_df views timestamps as int64: timezone-aware
        # Series.to_numpy() is object dtype. Use UTC-naive ns ONLY at this edge,
        # preserving UTC wall times, and restore explicit UTC on every output.
        model_times = pd.to_datetime(payload["timestamps"], utc=True).tz_localize(None).as_unit("ns")
        frame = pd.DataFrame({"item_id": ["series"]*90, "timestamp": model_times,
                              "debt_minutes": payload["past_values"]})
        result = self.pipeline.predict_df(frame, prediction_length=90, quantile_levels=list(QUANTILES),
            id_column="item_id", timestamp_column="timestamp", target="debt_minutes", context_length=90,
            batch_size=1, cross_learning=False, validate_inputs=True, freq="D")
        required = {"item_id", "timestamp", "target_name", "predictions", "0.1", "0.5", "0.9"}
        if set(result.columns) != required or len(result) != 90:
            raise ValueError("Unexpected univariate Chronos output shape/columns")
        path = []
        origin = utc_timestamp(request.origin_utc)
        for step, row in enumerate(result.to_dict("records"), 1):
            stamp = origin + timedelta(days=step)
            model_stamp = pd.Timestamp(row["timestamp"])
            returned_stamp = model_stamp.tz_localize("UTC") if model_stamp.tzinfo is None else model_stamp.tz_convert("UTC")
            if (row["item_id"] != "series" or row["target_name"] != "debt_minutes"
                    or utc_timestamp(returned_stamp) != stamp):
                raise ValueError("Chronos output identity/daily timestamp mismatch")
            native = [float(row[str(q)]) for q in QUANTILES]
            if not all(math.isfinite(v) for v in native) or not math.isfinite(float(row["predictions"])):
                raise ValueError("Nonfinite Chronos output")
            if not native[0] <= native[1] <= native[2]:
                raise ValueError("Native quantile crossing; do not manufacture sorted quantiles")
            path.append({"step_days": step, "timestamp": utc_iso(stamp),
                **{f"raw_q{int(q*100)}": v for q, v in zip(QUANTILES, native)},
                **{f"q{int(q*100)}": max(0.0, v) for q, v in zip(QUANTILES, native)}})
        return path
