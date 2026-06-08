import io
import tarfile

import pytest

from functions_be.resolver import (
    ArchiveFetcher,
    LibraryCache,
    LibraryIndex,
    ResolveError,
    _strip_extract,
)
from functions_shared import Ref, parse_ref

FN_YAML = "kind: function\nnamespace: aws\nname: login\nversion: 0.1.0\nruntime: claude\n"


class FakeFetcher:
    def __init__(self):
        self.calls = 0

    def fetch(self, ref, dest):
        self.calls += 1
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "function.yaml").write_text(FN_YAML)


def _make_targz(path, members: dict[str, str]):
    with tarfile.open(path, "w:gz") as tar:
        for name, content in members.items():
            data = content.encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


def test_archive_url():
    f = ArchiveFetcher()
    assert f.archive_url(parse_ref("github:owner/repo@main")).endswith("/owner/repo/tar.gz/main")
    assert f.archive_url(parse_ref("github:owner/repo")).endswith("/tar.gz/HEAD")
    assert f.archive_url(Ref(kind="url", raw="u", url="https://x/y.tar.gz")) == "https://x/y.tar.gz"
    with pytest.raises(ResolveError):
        f.archive_url(parse_ref("aws/login@1"))


def test_strip_extract_top_level(tmp_path):
    tar = tmp_path / "a.tar.gz"
    _make_targz(tar, {"repo-main/function.yaml": FN_YAML, "repo-main/run.sh": "echo hi"})
    dest = tmp_path / "out"
    _strip_extract(tar, dest)
    assert (dest / "function.yaml").exists() and (dest / "run.sh").exists()


def test_strip_extract_subdir(tmp_path):
    tar = tmp_path / "b.tar.gz"
    _make_targz(tar, {"repo-main/sub/function.yaml": FN_YAML, "repo-main/other.txt": "x"})
    dest = tmp_path / "out"
    _strip_extract(tar, dest, subdir="sub")
    assert (dest / "function.yaml").exists()
    assert not (dest / "other.txt").exists()


def test_archive_fetcher_fetch_via_file_url(tmp_path):
    tar = tmp_path / "pkg.tar.gz"
    _make_targz(tar, {"pkg-1/function.yaml": FN_YAML})
    ref = Ref(kind="url", raw=tar.as_uri(), url=tar.as_uri())
    dest = tmp_path / "installed"
    ArchiveFetcher().fetch(ref, dest)
    assert (dest / "function.yaml").exists()


def test_cache_path_layout(tmp_path):
    cache = LibraryCache(tmp_path)
    assert cache.path_for(parse_ref("aws/login@0.1.0")).name == "login@0.1.0"
    assert "github" in str(cache.path_for(parse_ref("github:o/r@main")))
    assert "url" in str(cache.path_for(Ref(kind="url", raw="u", url="https://x/y")))
    with pytest.raises(ResolveError):
        cache.path_for(parse_ref("./local"))


def test_install_idempotent_and_resolve(tmp_path):
    fetcher = FakeFetcher()
    cache = LibraryCache(tmp_path, fetcher=fetcher)
    ref = parse_ref("github:owner/repo@main")
    d1 = cache.install(ref)
    d2 = cache.install(ref)  # cached — no second fetch
    assert d1 == d2 and fetcher.calls == 1
    assert cache.is_installed(ref)
    # resolve dispatches: github via fetcher, local via passthrough
    assert cache.resolve("github:owner/repo@main") == d1
    assert cache.resolve("/abs/fn").as_posix() == "/abs/fn"


def test_install_rejects_local_and_registry(tmp_path):
    cache = LibraryCache(tmp_path, fetcher=FakeFetcher())
    with pytest.raises(ResolveError):
        cache.install(parse_ref("./x"))
    with pytest.raises(ResolveError, match="not installed"):
        cache.install(parse_ref("aws/login@0.1.0"))


def test_index_search_and_filter(tmp_path):
    (tmp_path / "aws" / "login@0.1.0").mkdir(parents=True)
    (tmp_path / "aws" / "login@0.1.0" / "function.yaml").write_text(FN_YAML)
    (tmp_path / "gcp" / "auth@1.0").mkdir(parents=True)
    (tmp_path / "gcp" / "auth@1.0" / "function.yaml").write_text(
        "kind: function\nnamespace: gcp\nname: auth\nversion: 1.0\nruntime: bash\n"
    )
    index = LibraryIndex(tmp_path)
    assert len(index.entries()) == 2
    assert [e.ref_id for e in index.search("login")] == ["aws/login@0.1.0"]
    assert [e.runtime for e in index.search(runtime="bash")] == ["bash"]
    assert index.search("nope") == []


def test_index_empty_root(tmp_path):
    assert LibraryIndex(tmp_path / "nope").entries() == []
