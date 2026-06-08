import pytest

from functions_shared import RefParseError, parse_ref


def test_registry_with_and_without_version():
    r = parse_ref("aws/login@0.1.0")
    assert (r.kind, r.namespace, r.name, r.version) == ("registry", "aws", "login", "0.1.0")
    assert r.pinned
    assert parse_ref("aws/login").version is None


def test_relative_and_absolute():
    assert parse_ref("./functions/x").kind == "relative"
    assert parse_ref("../x").kind == "relative"
    a = parse_ref("/abs/path/fn")
    assert a.kind == "absolute" and a.path == "/abs/path/fn"
    assert not a.pinned


def test_github_full_and_minimal():
    r = parse_ref("github:owner/repo/sub/dir@main")
    assert (r.owner, r.repo, r.subdir, r.gitref) == ("owner", "repo", "sub/dir", "main")
    assert r.pinned
    m = parse_ref("github:owner/repo")
    assert m.subdir is None and m.gitref is None


def test_url():
    r = parse_ref("https://example.com/fn.tar.gz")
    assert r.kind == "url" and r.url.endswith(".tar.gz") and r.pinned


@pytest.mark.parametrize("bad", ["", "   ", "not a ref!", "github:onlyowner"])
def test_invalid_refs_raise(bad):
    with pytest.raises(RefParseError):
        parse_ref(bad)
