"""Structured I/O transport — JSON files + env mirror (d_001 §4)."""

from __future__ import annotations

import json
from pathlib import Path

FN_INPUTS = "FN_INPUTS"  # path to the inputs JSON file
FN_OUTPUTS = "FN_OUTPUTS"  # path the function writes its outputs JSON to
INPUT_PREFIX = "INPUT_"  # scalar inputs mirrored as INPUT_<NAME>


def input_env_mirror(inputs: dict) -> dict[str, str]:
    """Scalar inputs as INPUT_<NAME> env vars. Non-scalars travel via the JSON file only."""
    env: dict[str, str] = {}
    for key, value in inputs.items():
        if isinstance(value, bool):
            env[f"{INPUT_PREFIX}{key.upper()}"] = "true" if value else "false"
        elif isinstance(value, (str, int, float)):
            env[f"{INPUT_PREFIX}{key.upper()}"] = str(value)
    return env


def write_inputs(path: str | Path, inputs: dict) -> None:
    Path(path).write_text(json.dumps(inputs))


def read_outputs(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {}
    text = p.read_text().strip()
    return json.loads(text) if text else {}
