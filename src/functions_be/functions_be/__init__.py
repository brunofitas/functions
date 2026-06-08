"""functions — orchestrator (be_).

The execution engine, runtime adapters, function loader, env/secrets bus, and pipeline
runner. Sealed decisions: docs/decisions/{d_001,d_be_001,d_be_002,d_infra_001}.md
"""

from __future__ import annotations

from .adapters import (
    BashAdapter,
    ClaudeAdapter,
    CustomAdapter,
    PythonAdapter,
    RunContext,
    RuntimeAdapter,
    UnknownRuntimeError,
    build_registry,
    get_adapter,
)
from . import auth
from .api import RunManager, create_app
from .container import Container, DockerContainer, LocalContainer
from .control import RunControl
from .engine import Engine, StepError
from .env import DictSecretStore, EnvBus, load_env_file, mask
from .events import Event
from .loader import FunctionLoadError, LoadedFunction, load_function, resolve_local_ref
from .manager import ContainerManager, DockerError, Mounts
from .resolver import (
    ArchiveFetcher,
    IndexEntry,
    LibraryCache,
    LibraryIndex,
    ResolveError,
)
from .runner import run_pipeline
from .server import build_app, serve

__version__ = "0.0.1"

__all__ = [
    "ArchiveFetcher",
    "BashAdapter",
    "ClaudeAdapter",
    "Container",
    "ContainerManager",
    "CustomAdapter",
    "DictSecretStore",
    "DockerContainer",
    "DockerError",
    "Engine",
    "Mounts",
    "EnvBus",
    "Event",
    "FunctionLoadError",
    "IndexEntry",
    "LibraryCache",
    "LibraryIndex",
    "LoadedFunction",
    "LocalContainer",
    "PythonAdapter",
    "ResolveError",
    "RunContext",
    "RunControl",
    "RunManager",
    "RuntimeAdapter",
    "StepError",
    "UnknownRuntimeError",
    "__version__",
    "auth",
    "build_app",
    "build_registry",
    "create_app",
    "serve",
    "get_adapter",
    "load_env_file",
    "load_function",
    "mask",
    "resolve_local_ref",
    "run_pipeline",
]
