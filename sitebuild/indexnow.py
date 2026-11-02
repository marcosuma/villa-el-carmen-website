"""Tell IndexNow search engines (Bing and the others that share it) which pages changed.

Run by .github/workflows/indexnow.yml after a push to main: it waits until Vercel serves
the committed version of each changed page, then submits those URLs in one request.
Usage: python -m sitebuild.indexnow --all | --changed-files FILE (use - for stdin)
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from urllib.parse import urlparse

from sitebuild import ROOT
from sitebuild.build import output_path
from sitebuild.content import load_site
from sitebuild.models import SiteConfig
from sitebuild.seo import page_url

ENDPOINT = "https://api.indexnow.org/indexnow"
USER_AGENT = "elcarmenpuglia-indexnow/1.0"
ACCEPTED_STATUSES = {200, 202}
STATUS_MEANINGS = {
    400: "invalid format",
    403: "key not valid (key file missing or different)",
    422: "URLs don't belong to the host or the key doesn't match",
    429: "too many requests",
}

Fetch = Callable[[str], bytes]
Post = Callable[[str, bytes], int]
Sleep = Callable[[float], None]


class IndexNowError(Exception):
    pass


def page_files(site: SiteConfig, root: Path = ROOT) -> dict[str, Path]:
    return {page_url(site, language): output_path(language, root) for language in site.languages}


def changed_page_urls(
    changed_paths: Iterable[str], pages: Mapping[str, Path], root: Path = ROOT
) -> list[str]:
    changed = {Path(path.strip()).as_posix() for path in changed_paths if path.strip()}
    return [url for url, file in pages.items() if file.relative_to(root).as_posix() in changed]


def wait_until_live(
    pages: Mapping[str, Path],
    fetch: Fetch,
    sleep: Sleep = time.sleep,
    timeout_seconds: float = 600,
    interval_seconds: float = 15,
) -> list[str]:
    """Poll until each URL serves the committed file; return the URLs still stale at timeout."""
    pending = dict(pages)
    waited = 0.0
    while True:
        for url, file in list(pending.items()):
            try:
                if fetch(url) == file.read_bytes():
                    del pending[url]
            except (urllib.error.URLError, TimeoutError):
                pass
        if not pending or waited >= timeout_seconds:
            return list(pending)
        sleep(interval_seconds)
        waited += interval_seconds


def build_payload(site: SiteConfig, urls: list[str]) -> dict:
    return {
        "host": urlparse(site.base_url).netloc,
        "key": site.indexnow_key,
        "keyLocation": f"{site.base_url}/{site.indexnow_key}.txt",
        "urlList": urls,
    }


def submit(payload: dict, post: Post) -> int:
    status = post(ENDPOINT, json.dumps(payload).encode("utf-8"))
    if status not in ACCEPTED_STATUSES:
        meaning = STATUS_MEANINGS.get(status, "unexpected response")
        raise IndexNowError(f"IndexNow replied {status}: {meaning}")
    return status


def http_fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def http_post(url: str, body: bytes) -> int:
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def read_changed_paths(source: str) -> list[str]:
    if source == "-":
        return sys.stdin.read().splitlines()
    return Path(source).read_text(encoding="utf-8").splitlines()


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--all", action="store_true", help="submit every language page")
    which.add_argument("--changed-files", metavar="FILE", help="git diff --name-only output")
    parser.add_argument("--timeout", type=float, default=600, help="seconds to wait for deploy")
    parser.add_argument("--dry-run", action="store_true", help="print the request, don't send")
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    fetch: Fetch = http_fetch,
    post: Post = http_post,
    sleep: Sleep = time.sleep,
    root: Path = ROOT,
) -> int:
    args = parse_args(argv)
    site = load_site()
    pages = page_files(site, root)
    if args.all:
        urls = list(pages)
    else:
        urls = changed_page_urls(read_changed_paths(args.changed_files), pages, root)
    if not urls:
        print("No page changed: nothing to submit.")
        return 0

    payload = build_payload(site, urls)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    stale = wait_until_live({url: pages[url] for url in urls}, fetch, sleep, args.timeout)
    if stale:
        print(f"Not live after {args.timeout:.0f}s, nothing submitted: {', '.join(stale)}")
        return 1
    try:
        status = submit(payload, post)
    except IndexNowError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Submitted {len(urls)} URL(s) to IndexNow (HTTP {status}): {', '.join(urls)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
