import pytest

from functions_shared import FunctionManifest, ManifestError, PipelineManifest, load_manifest
from functions_shared.loader import parse_manifest

FUNCTION_YAML = """
apiVersion: functions/v1
kind: function
namespace: aws
name: login
version: 0.1.0
runtime: claude
dependencies:
  system: [awscli]
requirements:
  secrets: [{ name: AWS_ACCESS_KEY_ID }]
  inputs: [{ name: role_arn, type: string }]
outputs: [{ name: account_id, type: string }]
exports: [AWS_PROFILE]
"""

PIPELINE_YAML = """
kind: pipeline
namespace: acme
name: deploy
version: 1.0.0
steps:
  - id: login
    use: aws/login@0.1.0
    with: { role_arn: "${{ secrets.DEPLOY_ROLE }}" }
flow: { mode: streaming }
"""


def test_load_function_manifest(tmp_path):
    p = tmp_path / "function.yaml"
    p.write_text(FUNCTION_YAML)
    m = load_manifest(p)
    assert isinstance(m, FunctionManifest)
    assert m.runtime == "claude"
    assert m.dependencies.system == ["awscli"]
    assert m.exports == ["AWS_PROFILE"]


def test_load_pipeline_manifest(tmp_path):
    p = tmp_path / "pipeline.yaml"
    p.write_text(PIPELINE_YAML)
    m = load_manifest(p)
    assert isinstance(m, PipelineManifest)
    assert m.flow.mode == "streaming"
    assert m.steps[0].with_["role_arn"] == "${{ secrets.DEPLOY_ROLE }}"


def test_parse_manifest_defaults_to_function():
    m = parse_manifest({"namespace": "n", "name": "f", "runtime": "bash"})
    assert isinstance(m, FunctionManifest)


def test_unknown_kind_raises():
    with pytest.raises(ManifestError, match="unknown manifest kind"):
        parse_manifest({"kind": "widget", "namespace": "n", "name": "f"})


def test_non_mapping_raises():
    with pytest.raises(ManifestError, match="must be a mapping"):
        parse_manifest(["not", "a", "dict"])


def test_missing_file_raises(tmp_path):
    with pytest.raises(ManifestError, match="not found"):
        load_manifest(tmp_path / "nope.yaml")
