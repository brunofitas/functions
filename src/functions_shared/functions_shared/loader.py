"""Load + validate a function/pipeline manifest from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import FunctionManifest, Manifest, PipelineManifest


class ManifestError(ValueError):
    pass


def parse_manifest(data: dict) -> Manifest:
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a mapping")
    kind = data.get("kind", "function")
    if kind == "function":
        return FunctionManifest(**data)
    if kind == "pipeline":
        return PipelineManifest(**data)
    raise ManifestError(f"unknown manifest kind: {kind!r}")


def load_manifest(path: str | Path) -> Manifest:
    p = Path(path)
    if not p.exists():
        raise ManifestError(f"manifest not found: {path}")
    return parse_manifest(yaml.safe_load(p.read_text()))
