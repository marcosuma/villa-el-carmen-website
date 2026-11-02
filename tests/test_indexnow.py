import json
import urllib.error

import pytest

from sitebuild import ROOT
from sitebuild.indexnow import (
    IndexNowError,
    build_payload,
    changed_page_urls,
    main,
    page_files,
    submit,
    wait_until_live,
)

HOME = "https://elcarmenpuglia.com/"
ITALIAN = "https://elcarmenpuglia.com/it/"


def test_page_files_map_every_language_url_to_its_committed_file(site):
    pages = page_files(site)

    assert pages[HOME] == ROOT / "index.html"
    assert pages[ITALIAN] == ROOT / "it" / "index.html"
    assert len(pages) == len(site.languages)


def test_changed_page_urls_keeps_only_pages_from_the_diff(site):
    diff = ["it/index.html", "src/content/it.json", "sitemap.xml", "", "index.html"]

    assert changed_page_urls(diff, page_files(site)) == [HOME, ITALIAN]


def test_changed_page_urls_is_empty_when_no_page_changed(site):
    assert changed_page_urls(["README.md", "docs/seo.md"], page_files(site)) == []


def test_wait_until_live_polls_until_the_new_version_is_served(tmp_path):
    page = tmp_path / "index.html"
    page.write_bytes(b"new")
    served = iter([b"old", b"old", b"new"])
    naps = []

    stale = wait_until_live({HOME: page}, lambda _: next(served), naps.append, 600, 15)

    assert stale == []
    assert naps == [15, 15]


def test_wait_until_live_survives_network_errors(tmp_path):
    page = tmp_path / "index.html"
    page.write_bytes(b"new")
    calls = []

    def flaky(url):
        calls.append(url)
        if len(calls) == 1:
            raise urllib.error.URLError("reset")
        return b"new"

    assert wait_until_live({HOME: page}, flaky, lambda _: None, 600, 15) == []


def test_wait_until_live_gives_up_at_the_timeout(tmp_path):
    page = tmp_path / "index.html"
    page.write_bytes(b"new")

    stale = wait_until_live({HOME: page}, lambda _: b"old", lambda _: None, 30, 15)

    assert stale == [HOME]


def test_build_payload_points_to_the_key_file(site):
    payload = build_payload(site, [HOME])

    assert payload == {
        "host": "elcarmenpuglia.com",
        "key": site.indexnow_key,
        "keyLocation": f"https://elcarmenpuglia.com/{site.indexnow_key}.txt",
        "urlList": [HOME],
    }


@pytest.mark.parametrize("status", [200, 202])
def test_submit_accepts_ok_and_pending_validation(status):
    assert submit({"urlList": [HOME]}, lambda url, body: status) == status


def test_submit_explains_a_rejected_key():
    with pytest.raises(IndexNowError, match="403: key not valid"):
        submit({"urlList": [HOME]}, lambda url, body: 403)


def test_submit_posts_json_to_the_shared_endpoint():
    sent = []

    submit({"urlList": [HOME]}, lambda url, body: sent.append((url, body)) or 200)

    assert sent[0][0] == "https://api.indexnow.org/indexnow"
    assert json.loads(sent[0][1]) == {"urlList": [HOME]}


def committed(url):
    path = "index.html" if url == HOME else url.removeprefix(HOME) + "index.html"
    return (ROOT / path).read_bytes()


def test_main_submits_only_the_changed_pages_once_they_are_live(tmp_path, capsys):
    diff = tmp_path / "diff.txt"
    diff.write_text("it/index.html\nREADME.md\n", encoding="utf-8")
    posted = []

    exit_code = main(
        ["--changed-files", str(diff)],
        fetch=committed,
        post=lambda url, body: posted.append(json.loads(body)) or 200,
        sleep=lambda _: None,
    )

    assert exit_code == 0
    assert posted[0]["urlList"] == [ITALIAN]
    assert "Submitted 1 URL(s)" in capsys.readouterr().out


def test_main_does_nothing_when_no_page_changed(tmp_path):
    diff = tmp_path / "diff.txt"
    diff.write_text("docs/seo.md\n", encoding="utf-8")

    def must_not_post(url, body):
        raise AssertionError("nothing should be submitted")

    assert main(["--changed-files", str(diff)], fetch=committed, post=must_not_post) == 0


def test_main_fails_without_submitting_when_the_deploy_never_goes_live():
    def must_not_post(url, body):
        raise AssertionError("stale pages must not be submitted")

    exit_code = main(
        ["--all", "--timeout", "30"],
        fetch=lambda url: b"old",
        post=must_not_post,
        sleep=lambda _: None,
    )

    assert exit_code == 1


def test_main_dry_run_prints_the_request_for_every_page(capsys):
    assert main(["--all", "--dry-run"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert len(payload["urlList"]) == 5
