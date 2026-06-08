from functions_shared import input_env_mirror, read_outputs, write_inputs
from functions_shared.io import FN_INPUTS, FN_OUTPUTS, INPUT_PREFIX


def test_env_constants():
    assert (FN_INPUTS, FN_OUTPUTS, INPUT_PREFIX) == ("FN_INPUTS", "FN_OUTPUTS", "INPUT_")


def test_input_env_mirror_scalars_and_bools():
    env = input_env_mirror({"role_arn": "arn:x", "count": 3, "ratio": 1.5, "ok": True, "no": False})
    assert env["INPUT_ROLE_ARN"] == "arn:x"
    assert env["INPUT_COUNT"] == "3"
    assert env["INPUT_RATIO"] == "1.5"
    assert env["INPUT_OK"] == "true"
    assert env["INPUT_NO"] == "false"


def test_input_env_mirror_skips_non_scalars():
    env = input_env_mirror({"obj": {"a": 1}, "arr": [1, 2], "s": "x"})
    assert "INPUT_OBJ" not in env and "INPUT_ARR" not in env
    assert env["INPUT_S"] == "x"


def test_write_and_read_roundtrip(tmp_path):
    p = tmp_path / "out.json"
    write_inputs(p, {"a": 1, "b": {"c": 2}})
    assert read_outputs(p) == {"a": 1, "b": {"c": 2}}


def test_read_outputs_missing_and_empty(tmp_path):
    assert read_outputs(tmp_path / "nope.json") == {}
    empty = tmp_path / "empty.json"
    empty.write_text("   ")
    assert read_outputs(empty) == {}
