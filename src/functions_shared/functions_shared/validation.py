"""Output validation — ALWAYS STRICT (d_001 §5)."""

from __future__ import annotations

from .models import OutputSpec

_TYPE_CHECKS: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


class OutputValidationError(ValueError):
    pass


def validate_outputs(declared: list[OutputSpec], produced: dict) -> None:
    """Raise if any declared output is missing or mistyped. No tolerance (d_001 §5)."""
    for spec in declared:
        if spec.name not in produced:
            raise OutputValidationError(f"missing declared output: {spec.name!r}")
        value = produced[spec.name]
        # bool is a subclass of int — guard number/boolean against each other.
        if spec.type == "number" and isinstance(value, bool):
            raise OutputValidationError(f"output {spec.name!r}: expected number, got boolean")
        if spec.type == "boolean" and not isinstance(value, bool):
            raise OutputValidationError(
                f"output {spec.name!r}: expected boolean, got {type(value).__name__}"
            )
        if not isinstance(value, _TYPE_CHECKS[spec.type]):
            raise OutputValidationError(
                f"output {spec.name!r}: expected {spec.type}, got {type(value).__name__}"
            )
