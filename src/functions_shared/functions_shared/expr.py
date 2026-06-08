"""Wiring expressions — ``${{ steps.x.outputs.y }}`` resolution (d_001 §1)."""

from __future__ import annotations

import re
from typing import Any

_EXPR = re.compile(r"\$\{\{\s*(?P<body>[^}]+?)\s*\}\}")


class ExpressionError(ValueError):
    pass


def resolve(value: Any, context: dict) -> Any:
    """Resolve ``${{ ... }}`` in *value* against *context*.

    A lone expression preserves the resolved value's type; an embedded expression is
    interpolated into the surrounding string. Recurses into dicts and lists.
    """
    if isinstance(value, str):
        whole = _EXPR.fullmatch(value.strip())
        if whole:
            return _lookup(whole["body"].strip(), context)
        return _EXPR.sub(lambda m: str(_lookup(m["body"].strip(), context)), value)
    if isinstance(value, dict):
        return {k: resolve(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, context) for v in value]
    return value


def _lookup(path: str, context: dict) -> Any:
    cur: Any = context
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise ExpressionError(f"cannot resolve expression: {path!r}")
    return cur
