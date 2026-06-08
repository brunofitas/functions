import pytest

from functions_shared import OutputValidationError, validate_outputs
from functions_shared.models import OutputSpec


def _out(name, type_):
    return OutputSpec(name=name, type=type_)


def test_passes_when_all_present_and_typed():
    declared = [_out("account_id", "string"), _out("count", "number"), _out("ok", "boolean")]
    validate_outputs(declared, {"account_id": "123", "count": 3, "ok": True})


def test_missing_output_raises():
    with pytest.raises(OutputValidationError, match="missing"):
        validate_outputs([_out("account_id", "string")], {})


def test_type_mismatch_raises():
    with pytest.raises(OutputValidationError, match="expected string"):
        validate_outputs([_out("x", "string")], {"x": 5})


def test_number_rejects_boolean():
    with pytest.raises(OutputValidationError, match="expected number, got boolean"):
        validate_outputs([_out("n", "number")], {"n": True})


def test_boolean_rejects_non_bool():
    with pytest.raises(OutputValidationError, match="expected boolean"):
        validate_outputs([_out("b", "boolean")], {"b": 1})


def test_object_and_array_types():
    validate_outputs([_out("o", "object"), _out("a", "array")], {"o": {"k": 1}, "a": [1, 2]})
    with pytest.raises(OutputValidationError):
        validate_outputs([_out("a", "array")], {"a": "nope"})


def test_number_accepts_int_and_float():
    validate_outputs([_out("n", "number")], {"n": 1})
    validate_outputs([_out("n", "number")], {"n": 1.5})
