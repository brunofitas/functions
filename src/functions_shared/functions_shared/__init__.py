"""functions — shared contract (implemented per docs/decisions/d_001).

The spine both the orchestrator (functions_be) and the GUI (functions_fe) build on:
manifest schema, runtime-adapter types, reference grammar, strict output validation,
the JSON-file/env I/O convention, and wiring-expression resolution.
"""

from __future__ import annotations

from .expr import ExpressionError, resolve
from .io import (
    FN_INPUTS,
    FN_OUTPUTS,
    INPUT_PREFIX,
    input_env_mirror,
    read_outputs,
    write_inputs,
)
from .loader import ManifestError, load_manifest, parse_manifest
from .models import (
    Capabilities,
    Dependencies,
    EnvSpec,
    Events,
    Flow,
    FunctionManifest,
    InputSpec,
    Manifest,
    OutputSpec,
    PipelineManifest,
    Requirements,
    SecretSpec,
    Step,
    StorageSpec,
)
from .refs import Ref, RefParseError, parse_ref
from .validation import OutputValidationError, validate_outputs

__version__ = "0.0.1"

__all__ = [
    "Capabilities",
    "Dependencies",
    "EnvSpec",
    "Events",
    "ExpressionError",
    "FN_INPUTS",
    "FN_OUTPUTS",
    "Flow",
    "FunctionManifest",
    "INPUT_PREFIX",
    "InputSpec",
    "Manifest",
    "ManifestError",
    "OutputSpec",
    "OutputValidationError",
    "PipelineManifest",
    "Ref",
    "RefParseError",
    "Requirements",
    "SecretSpec",
    "Step",
    "StorageSpec",
    "__version__",
    "input_env_mirror",
    "load_manifest",
    "parse_manifest",
    "parse_ref",
    "read_outputs",
    "resolve",
    "validate_outputs",
    "write_inputs",
]
