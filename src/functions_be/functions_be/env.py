"""Environment bus & secrets (be_008, per d_be_001).

Least-privilege: a function only sees the secrets it declares. ``exports`` promotes
named outputs to the downstream env bus (opt-in leak). Secret values are masked in
streamed text.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol


class SecretStore(Protocol):
    def get(self, name: str) -> Optional[str]: ...

    def all(self) -> dict: ...


class DictSecretStore:
    def __init__(self, secrets: Optional[dict] = None):
        self._s = dict(secrets or {})

    def get(self, name: str) -> Optional[str]:
        return self._s.get(name)

    def all(self) -> dict:
        return dict(self._s)


def load_env_file(path: str | Path) -> dict:
    out: dict[str, str] = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


class EnvBus:
    def __init__(self, global_env: Optional[dict] = None, store: Optional[SecretStore] = None):
        self.global_env = dict(global_env or {})
        self.store: SecretStore = store or DictSecretStore()
        self.bus: dict[str, str] = {}  # running exports

    def step_env(self, fn) -> dict:
        """Effective env for a step: defaults < bus < global, + declared secrets only."""
        env: dict[str, str] = {}
        for spec in fn.requirements.environment:
            if spec.default is not None:
                env[spec.name] = spec.default
        env.update(self.bus)
        env.update(self.global_env)
        for spec in fn.requirements.secrets:  # least-privilege
            value = self.store.get(spec.name)
            if value is not None:
                env[spec.name] = value
        return env

    def apply_exports(self, fn, outputs: dict) -> None:
        for name in fn.exports:
            if name in outputs:
                self.bus[name] = str(outputs[name])

    def secret_values(self) -> dict:
        return self.store.all()


def mask(text: str, secrets) -> str:
    for value in secrets:
        if value:
            text = text.replace(str(value), "••••")
    return text
