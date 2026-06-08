"""Manifest schema + runtime-adapter types. Implements docs/decisions/d_001."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

InputType = Literal["string", "number", "boolean", "object", "array"]
Memory = Literal["none", "session", "history"]

DEFAULT_ENTRYPOINTS = {
    "bash": "run.sh",
    "python": "main.py",
    "claude": "prompt.md",
    "custom": "Makefile",
}


class InputSpec(BaseModel):
    name: str
    type: InputType = "string"
    required: bool = False
    default: object | None = None


class OutputSpec(BaseModel):
    name: str
    type: InputType = "string"


class SecretSpec(BaseModel):
    name: str


class EnvSpec(BaseModel):
    name: str
    default: str | None = None


class Dependencies(BaseModel):
    system: list[str] = Field(default_factory=list)  # apt
    python: list[str] = Field(default_factory=list)  # pip (pinned)


class Requirements(BaseModel):
    secrets: list[SecretSpec] = Field(default_factory=list)
    environment: list[EnvSpec] = Field(default_factory=list)
    inputs: list[InputSpec] = Field(default_factory=list)


class Events(BaseModel):
    emits: list[str] = Field(default_factory=list)
    listens: list[str] = Field(default_factory=list)


class StorageSpec(BaseModel):
    path: str


class Capabilities(BaseModel):
    """What a runtime adapter can do — drives cost, determinism, and memory."""

    is_llm: bool
    memory: Memory
    default_entrypoint: str
    dep_kinds: list[str] = Field(default_factory=list)


class FunctionManifest(BaseModel):
    api_version: str = Field(default="functions/v1", alias="apiVersion")
    kind: Literal["function"] = "function"
    namespace: str
    name: str
    version: str = "0.0.0"
    description: str | None = None
    runtime: str
    entrypoint: str | None = None
    dependencies: Dependencies = Field(default_factory=Dependencies)
    requirements: Requirements = Field(default_factory=Requirements)
    outputs: list[OutputSpec] = Field(default_factory=list)
    exports: list[str] = Field(default_factory=list)  # opt-in env leaked downstream
    storage: list[StorageSpec] = Field(default_factory=list)
    events: Events = Field(default_factory=Events)
    i18n: str | None = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("version", "api_version", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return str(v) if v is not None else v

    @property
    def ref_id(self) -> str:
        return f"{self.namespace}/{self.name}@{self.version}"

    def resolved_entrypoint(self) -> str:
        return self.entrypoint or DEFAULT_ENTRYPOINTS.get(self.runtime, "run.sh")


class Step(BaseModel):
    id: str
    use: str
    with_: dict[str, object] = Field(default_factory=dict, alias="with")

    model_config = ConfigDict(populate_by_name=True)


class FlowEnd(BaseModel):
    signal: str = "END"


class Flow(BaseModel):
    mode: Literal["standalone", "streaming"] = "standalone"
    end: FlowEnd = Field(default_factory=FlowEnd)


class PipelineManifest(BaseModel):
    api_version: str = Field(default="functions/v1", alias="apiVersion")
    kind: Literal["pipeline"] = "pipeline"
    namespace: str
    name: str
    version: str = "0.0.0"
    description: str | None = None
    requirements: Requirements = Field(default_factory=Requirements)
    outputs: list[OutputSpec] = Field(default_factory=list)
    steps: list[Step]
    flow: Flow = Field(default_factory=Flow)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("version", "api_version", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return str(v) if v is not None else v

    @property
    def ref_id(self) -> str:
        return f"{self.namespace}/{self.name}@{self.version}"


Manifest = Union[FunctionManifest, PipelineManifest]
