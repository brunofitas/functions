import pytest

from functions_shared import ExpressionError, resolve

CTX = {
    "steps": {"login": {"outputs": {"account_id": "123", "tags": ["a", "b"]}}},
    "secrets": {"TOKEN": "s3cr3t"},
    "env": {"REGION": "eu-west-1"},
    "inputs": {"n": 5},
}


def test_lone_expression_preserves_type():
    assert resolve("${{ steps.login.outputs.account_id }}", CTX) == "123"
    assert resolve("${{ steps.login.outputs.tags }}", CTX) == ["a", "b"]
    assert resolve("${{ inputs.n }}", CTX) == 5


def test_embedded_expression_interpolates_to_string():
    assert resolve("acct-${{ steps.login.outputs.account_id }}-${{ env.REGION }}", CTX) == (
        "acct-123-eu-west-1"
    )


def test_recurses_into_dicts_and_lists():
    out = resolve({"a": ["${{ secrets.TOKEN }}", 1], "b": "x"}, CTX)
    assert out == {"a": ["s3cr3t", 1], "b": "x"}


def test_non_string_passthrough():
    assert resolve(42, CTX) == 42
    assert resolve(None, CTX) is None


def test_unresolvable_raises():
    with pytest.raises(ExpressionError):
        resolve("${{ steps.missing.outputs.x }}", CTX)
