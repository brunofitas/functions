"""Reference resolver, library cache & index (be_010).

Resolves any reference to a local function directory. Local refs pass through; remote
refs (github/url) are fetched into the library cache ``.lib/cache/...`` (idempotent).
A searchable index scans the cache for installed functions.
"""

from __future__ import annotations

import hashlib
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from functions_shared import Ref, load_manifest, parse_ref

from .loader import resolve_local_ref

DEFAULT_CACHE = Path(".lib/cache")
MANIFEST_NAMES = ("function.yaml", "function.yml")


class ResolveError(ValueError):
    pass


class Fetcher(Protocol):
    def fetch(self, ref: Ref, dest: Path) -> None: ...


def _strip_extract(tar_path: Path, dest: Path, subdir: Optional[str] = None) -> None:
    """Extract a .tar.gz, dropping the top-level dir (like --strip-components=1)."""
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            parts = member.name.split("/", 1)
            if len(parts) < 2 or not parts[1]:
                continue
            rel = parts[1]
            if subdir:
                prefix = subdir.strip("/") + "/"
                if not rel.startswith(prefix):
                    continue
                rel = rel[len(prefix) :]
            if not rel:
                continue
            target = dest / rel
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted = tar.extractfile(member)
                if extracted is not None:
                    target.write_bytes(extracted.read())


class ArchiveFetcher:
    """Fetch + extract a tarball for github/url refs."""

    def archive_url(self, ref: Ref) -> str:
        if ref.kind == "url":
            return ref.url
        if ref.kind == "github":
            gitref = ref.gitref or "HEAD"
            return f"https://codeload.github.com/{ref.owner}/{ref.repo}/tar.gz/{gitref}"
        raise ResolveError(f"cannot build archive url for {ref.kind} ref")

    def fetch(self, ref: Ref, dest: Path) -> None:
        url = self.archive_url(ref)
        subdir = ref.subdir if ref.kind == "github" else None
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            with urllib.request.urlopen(url) as resp:  # noqa: S310
                tmp.write(resp.read())
            tmp_path = Path(tmp.name)
        try:
            _strip_extract(tmp_path, dest, subdir)
        finally:
            tmp_path.unlink(missing_ok=True)


class LibraryCache:
    def __init__(self, root: str | Path = DEFAULT_CACHE, fetcher: Optional[Fetcher] = None):
        self.root = Path(root)
        self.fetcher = fetcher or ArchiveFetcher()

    def path_for(self, ref: Ref) -> Path:
        if ref.kind == "registry":
            return self.root / ref.namespace / f"{ref.name}@{ref.version or 'latest'}"
        if ref.kind == "github":
            tail = f"{ref.repo}@{ref.gitref or 'HEAD'}"
            return self.root / "github" / ref.owner / tail
        if ref.kind == "url":
            digest = hashlib.sha1(ref.url.encode()).hexdigest()[:12]  # noqa: S324
            return self.root / "url" / digest
        raise ResolveError(f"no cache path for local ref: {ref.raw}")

    def is_installed(self, ref: Ref) -> bool:
        dest = self.path_for(ref)
        return dest.is_dir() and any((dest / n).exists() for n in MANIFEST_NAMES)

    def install(self, ref: Ref) -> Path:
        if ref.kind in ("relative", "absolute"):
            raise ResolveError("local refs are not installed; use resolve()")
        dest = self.path_for(ref)
        if self.is_installed(ref):
            return dest
        if ref.kind == "registry":
            raise ResolveError(
                f"registry ref {ref.raw!r} not installed; install from github/disk/url first"
            )
        self.fetcher.fetch(ref, dest)
        return dest

    def resolve(self, ref_or_str, base_dir: str | Path = ".") -> Path:
        ref = ref_or_str if isinstance(ref_or_str, Ref) else parse_ref(ref_or_str)
        if ref.kind in ("relative", "absolute"):
            return resolve_local_ref(ref, base_dir)
        return self.install(ref)


@dataclass
class IndexEntry:
    namespace: str
    name: str
    version: str
    runtime: str
    dir: Path

    @property
    def ref_id(self) -> str:
        return f"{self.namespace}/{self.name}@{self.version}"


class LibraryIndex:
    def __init__(self, root: str | Path = DEFAULT_CACHE):
        self.root = Path(root)

    def entries(self) -> list[IndexEntry]:
        found: list[IndexEntry] = []
        if not self.root.exists():
            return found
        for name in MANIFEST_NAMES:
            for manifest_path in self.root.rglob(name):
                try:
                    m = load_manifest(manifest_path)
                except Exception:
                    continue
                if getattr(m, "kind", None) != "function":
                    continue
                found.append(
                    IndexEntry(m.namespace, m.name, m.version, m.runtime, manifest_path.parent)
                )
        return found

    def search(self, query: str = "", runtime: Optional[str] = None) -> list[IndexEntry]:
        q = query.lower()
        out = []
        for entry in self.entries():
            if q and q not in f"{entry.namespace}/{entry.name}".lower():
                continue
            if runtime and entry.runtime != runtime:
                continue
            out.append(entry)
        return out
