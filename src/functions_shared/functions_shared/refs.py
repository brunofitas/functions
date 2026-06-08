"""Reference-string grammar (d_001 §2): registry / relative / absolute / github / url."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

RefKind = Literal["registry", "relative", "absolute", "github", "url"]

_REGISTRY = re.compile(r"^(?P<ns>[a-z0-9_-]+)/(?P<name>[a-z0-9_-]+)(@(?P<ver>[\w.\-]+))?$")
_GITHUB = re.compile(
    r"^github:(?P<owner>[^/]+)/(?P<repo>[^/@]+)(/(?P<sub>[^@]+))?(@(?P<ref>[\w./\-]+))?$"
)


class RefParseError(ValueError):
    pass


@dataclass(frozen=True)
class Ref:
    kind: RefKind
    raw: str
    namespace: str | None = None
    name: str | None = None
    version: str | None = None
    owner: str | None = None
    repo: str | None = None
    subdir: str | None = None
    gitref: str | None = None
    path: str | None = None
    url: str | None = None

    @property
    def pinned(self) -> bool:
        """Registry/github/url refs are reproducible; relative/absolute are not."""
        return self.kind in ("registry", "github", "url")


def parse_ref(s: str) -> Ref:
    s = s.strip()
    if not s:
        raise RefParseError("empty reference")
    if s.startswith(("./", "../")):
        return Ref(kind="relative", raw=s, path=s)
    if s.startswith("/"):
        return Ref(kind="absolute", raw=s, path=s)
    if s.startswith("github:"):
        m = _GITHUB.match(s)
        if not m:
            raise RefParseError(f"invalid github ref: {s}")
        return Ref(
            kind="github",
            raw=s,
            owner=m["owner"],
            repo=m["repo"],
            subdir=m["sub"],
            gitref=m["ref"],
        )
    if s.startswith(("http://", "https://")):
        return Ref(kind="url", raw=s, url=s)
    m = _REGISTRY.match(s)
    if m:
        return Ref(kind="registry", raw=s, namespace=m["ns"], name=m["name"], version=m["ver"])
    raise RefParseError(f"unrecognized reference: {s}")
