"""Reuse strict legacy IO, with streaming hashes and a small bundle boundary."""
import hashlib
from pathlib import Path

from contracts import read_json, source_path, write_json

from . import MVP_SCHEMA_VERSION

SERIALIZER = "legacy_sorted_compact_json_utf8_v1"


def file_sha256(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def artifact_path(root, relative):
    source_path(relative)
    root = Path(root).resolve()
    path = root / relative
    # Symlinks are excluded even when their target happens to be inside the root.
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise ValueError("Symlink artifact forbidden")
    if not path.resolve().is_relative_to(root):
        raise ValueError("Artifact escapes bundle")
    return path


def publish_manifest(root, artifacts, metadata):
    root = Path(root).resolve()
    if not isinstance(metadata, dict):
        raise ValueError("Manifest metadata must be an object")
    if (root / "manifest.json").exists():
        raise ValueError("Existing manifest cannot be overwritten")
    if not artifacts or len(artifacts) != len(set(artifacts)) or "manifest.json" in artifacts:
        raise ValueError("Unique non-manifest artifacts required")
    hashes = {name: file_sha256(artifact_path(root, name)) for name in artifacts}
    record = {"mvp_schema_version": MVP_SCHEMA_VERSION, "status": "COMPLETE",
              "serializer": SERIALIZER,
              "artifacts": hashes, "metadata": metadata}
    write_json(root / "manifest.json", record)
    return record


def verify_bundle(root):
    root = Path(root).resolve()
    manifest = read_json(artifact_path(root, "manifest.json"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be an object")
    if type(manifest.get("mvp_schema_version")) is not int or manifest["mvp_schema_version"] != MVP_SCHEMA_VERSION:
        raise ValueError("Unsupported MVP schema")
    if manifest.get("serializer") != SERIALIZER or not isinstance(manifest.get("metadata"), dict):
        raise ValueError("Unsupported serializer or metadata")
    if manifest.get("status") != "COMPLETE" or not isinstance(manifest.get("artifacts"), dict) or not manifest["artifacts"]:
        raise ValueError("Bundle is not COMPLETE with artifacts")
    for name, expected in manifest["artifacts"].items():
        if name == "manifest.json" or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("Invalid artifact hash record")
        if file_sha256(artifact_path(root, name)) != expected:
            raise ValueError(f"Artifact hash mismatch: {name}")
    return manifest
