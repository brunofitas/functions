"""Function sandbox & permission posture (be_003).

claude steps run non-interactively, bounded by the Docker sandbox. Provenance/signing
is deferred to the marketplace milestone.
"""

from __future__ import annotations

PERMISSION_MODE = "bypassPermissions"  # only ever inside the container
WRITABLE_MOUNTS = ("/work", "/lib")


def claude_permission_args() -> list[str]:
    return ["--permission-mode", PERMISSION_MODE]


def trust_summary() -> str:
    return (
        "Functions run inside the Docker sandbox with writable mounts "
        f"{', '.join(WRITABLE_MOUNTS)}; no host access beyond mounts. "
        "Provenance/signing is deferred to the marketplace."
    )
