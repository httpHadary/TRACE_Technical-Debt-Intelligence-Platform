"""Immutable schema2 bundles using existing read-only hash/path helpers."""
from pathlib import Path
import json
import os
import shutil
import tempfile
from forecasting_mvp.io import artifact_path, file_sha256
from .contracts import canonical


def publish(root, artifacts, metadata):
    root = Path(root).absolute()
    if root.exists() or root.is_symlink() or not artifacts or "manifest.json" in artifacts:
        raise ValueError("A new output directory and non-manifest artifacts required")
    root.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".schema2-", dir=root.parent))
    try:
        for name, content in sorted(artifacts.items()):
            path = artifact_path(temporary, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            data = content if isinstance(content, bytes) else canonical(content) + b"\n"
            with path.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        package = Path(__file__).parent
        code_hashes = {str(p.relative_to(package.parent)): file_sha256(p) for p in sorted(package.rglob("*.py"))}
        for name in ("forecasting_mvp/io.py", "contracts.py"):
            code_hashes[name] = file_sha256(package.parent / name)
        manifest = {"schema_version": 2, "status": "COMPLETE", "serializer": "canonical_json_utf8_v2",
                    "artifacts": {n: file_sha256(temporary / n) for n in sorted(artifacts)}, "metadata": metadata}
        manifest["code_hashes"] = code_hashes
        (temporary / "manifest.json").write_bytes(canonical(manifest) + b"\n")
        # Never replace an existing directory, including an incomplete previous attempt.
        os.rename(temporary, root)
        return manifest
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def verify(root):
    manifest = json.loads(artifact_path(root, "manifest.json").read_text())
    if (manifest.get("schema_version") != 2 or manifest.get("status") != "COMPLETE"
            or manifest.get("serializer") != "canonical_json_utf8_v2" or not manifest.get("artifacts")):
        raise ValueError("Invalid schema2 COMPLETE manifest")
    for name, expected in manifest["artifacts"].items():
        if name == "manifest.json" or file_sha256(artifact_path(root, name)) != expected:
            raise ValueError("Artifact integrity failure")
    return manifest
