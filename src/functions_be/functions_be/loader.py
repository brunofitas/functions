"""Function loader + local reference resolution (be_004).

Loads a function directory (manifest + entrypoint). Remote refs (registry/github/url)
require the resolver/library cache (be_010); here we resolve only local refs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from functions_shared import FunctionManifest, Ref, load_manifest

MANIFEST_NAMES = ("function.yaml", "function.yml")


class FunctionLoadError(ValueError):
    pass


@dataclass
class LoadedFunction:
    manifest: FunctionManifest
    dir: Path


def load_function(path: str | Path) -> LoadedFunction:
    d = Path(path)
    if not d.is_dir():
        raise FunctionLoadError(f"not a function directory: {path}")
    manifest_path = next((d / n for n in MANIFEST_NAMES if (d / n).exists()), None)
    if manifest_path is None:
        raise FunctionLoadError(f"no function manifest in {path}")
    manifest = load_manifest(manifest_path)
    if not isinstance(manifest, FunctionManifest):
        raise FunctionLoadError(f"{manifest_path} is not a function manifest")
    return LoadedFunction(manifest=manifest, dir=d)


def resolve_local_ref(ref: Ref, base_dir: str | Path) -> Path:
    if ref.kind == "relative":
        return (Path(base_dir) / ref.path).resolve()
    if ref.kind == "absolute":
        return Path(ref.path)
    raise FunctionLoadError(f"non-local ref requires the resolver (be_010): {ref.raw}")
