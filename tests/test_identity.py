import pytest

from backend.importer.http import SourceClient, SourceDocument
from backend.importer.identity import SourceIdentityPolicy, SourceIdentityError, configured_identity
from backend.importer.details import collect_course_references, DetailImportError


def document(target, caption="Fiktiver Kurs"):
    return SourceDocument(
        f'<table><tr><td class="plan5a"><a href="{target}">{caption}</a></td></tr>' +
        "<tr><td>DEMO</td></tr>" * 7 + "</table>", "https://example.invalid/plan")


def test_identity_ignores_session_path_and_query_order():
    policy = SourceIdentityPolicy("record", "demo")
    with SourceClient("https://example.invalid/start") as client:
        key = policy.key_for(client, "/detail?record=12&session=first")
        assert key == policy.key_for(client, "/changed?session=second&record=12")
        assert key != policy.key_for(client, "/detail?record=13")
        assert key != SourceIdentityPolicy("record", "other").key_for(client, "/detail?record=12")
    with SourceClient("https://other.invalid/start") as client:
        assert key != policy.key_for(client, "/detail?record=12")
    assert "record" not in repr(policy) and "demo" not in repr(policy)


@pytest.mark.parametrize("target", [
    "/detail", "/detail?record=", "/detail?record=0", "/detail?record=01",
    "/detail?record=-1", "/detail?record=abc", "/detail?record=1&record=1",
    "/detail?record=" + "9" * 33, "https://other.invalid/detail?record=1",
])
def test_ambiguous_or_invalid_identity_fails_without_url(target):
    with SourceClient("https://example.invalid/start") as client:
        with pytest.raises(SourceIdentityError) as error:
            SourceIdentityPolicy("record", "demo").key_for(client, target)
    assert "record" not in str(error.value)
    assert "example.invalid" not in str(error.value)


def test_configuration_requires_both_values():
    assert configured_identity("", "") is None
    assert configured_identity("record", "demo") is not None
    for parameter, namespace in [("record", ""), ("", "demo"), ("bad space", "demo"),
                                 ("record", "bad/namespace")]:
        with pytest.raises(SourceIdentityError):
            configured_identity(parameter, namespace)


def test_collector_uses_identity_and_rejects_conflicts_without_fallback():
    policy = SourceIdentityPolicy("record", "demo")
    with SourceClient("https://example.invalid/start") as client:
        docs = (document("/detail?record=12&session=a"), document("/detail?record=12&session=b"))
        assert len(collect_course_references(client, docs)) == 2
        refs = collect_course_references(client, docs, identity_policy=policy)
        assert len(refs) == 1 and refs[0].block_count == 2
        assert refs[0].identity_scope == "configured"
        changed = collect_course_references(client, (document("/detail?record=12", "Neuer Titel"),),
                                            identity_policy=policy)
        assert refs[0].key == changed[0].key
        with pytest.raises(DetailImportError):
            collect_course_references(client, (docs[0], document("/detail?record=12", "Konflikt")),
                                      identity_policy=policy)
        with pytest.raises(DetailImportError):
            collect_course_references(client, (document("/detail?session=a"),), identity_policy=policy)
