"""Check this fixture's committed history, links, and optional Git Gallery compatibility."""
import argparse
import base64
import json
import posixpath
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/FrankB45/csc325-capstone-test-minimal"
API = "https://api.github.com/repos/FrankB45/csc325-capstone-test-minimal"

def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.scripts += tag == "script"
        if "id" in values:
            self.ids.add(values["id"])
        for name in ("href", "src"):
            if name in values:
                self.links.append(values[name])

def snapshot(sha):
    entries = []
    for record in git("ls-tree", "-rz", "--full-tree", sha).split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        entries.append({"path": path.decode(), "mode": mode, "type": kind, "sha": blob})
    return entries

def check(backend=None):
    commits = git("rev-list", "--reverse", "HEAD").decode().splitlines()
    assert len(commits) == 20, f"Expected 20 commits; found {len(commits)}."
    deps = None
    if backend:
        sys.path.insert(0, str(Path(backend).resolve()))
        import requests
        from git_gallery_app.services import dependencies as deps
    page_checks = 0
    for number, sha in enumerate(commits, 1):
        entries = snapshot(sha)
        files = {entry["path"]: entry["sha"] for entry in entries}
        pages = {path for path in files if path.endswith(".html")}
        expected = {"index.html"}
        if number >= 6 and number not in (12, 13):
            expected.add("about.html")
        if number >= 10:
            expected.add("events.html")
        assert pages == expected, (number, pages, expected)
        parsed = {}
        for path in pages:
            parser = Links()
            parser.feed(git("show", f"{sha}:{path}").decode())
            assert parser.scripts == 0, (number, path, "Unexpected script")
            parsed[path] = parser
        for path, parser in parsed.items():
            for link in parser.links:
                parts = urlsplit(link)
                assert not parts.scheme and not parts.netloc, (number, path, link)
                target = posixpath.normpath(posixpath.join(posixpath.dirname(path), parts.path)) if parts.path else path
                assert target in files, (number, path, link, "Missing local resource")
                if parts.fragment and target in parsed:
                    assert parts.fragment in parsed[target].ids, (number, path, link, "Missing anchor")
        if deps:
            tree = git("rev-parse", f"{sha}^{{tree}}").decode().strip()
            def fake_get(url, **kwargs):
                if url == f"{API}/git/trees/{tree}":
                    payload = {"sha": tree, "truncated": False, "tree": entries}
                elif url.startswith(f"{API}/git/blobs/"):
                    blob = url.rsplit("/", 1)[-1]
                    content = git("cat-file", "blob", blob)
                    payload = {"sha": blob, "encoding": "base64", "size": len(content),
                               "content": base64.b64encode(content).decode()}
                else:
                    raise AssertionError("Unexpected network request: " + url)
                response = requests.Response()
                response.status_code = 200
                response.url = url
                response._content = json.dumps(payload).encode()
                response._content_consumed = True
                response.headers["Content-Length"] = str(len(response._content))
                return response
            with patch("requests.get", side_effect=fake_get):
                result = deps.check_repository_dependencies(URL, tree_sha=tree)
                assert result["dependency_status"] == "passed", (number, result)
                for page in pages:
                    budget = {"content_bytes": 0, "download_bytes": 0, "limit_reason": ""}
                    result = deps._check_static_homepage_profile(
                        "FrankB45", "csc325-capstone-test-minimal", files, page,
                        git("show", f"{sha}:{page}").decode(), tree, budget,
                    )
                    assert result and result["dependency_status"] == "passed", (number, page, result)
                    page_checks += 1
    print(json.dumps({"commits": len(commits), "links": "passed",
                      "compatibility": "passed" if deps else "not run; supply --backend",
                      "page_compatibility_checks": page_checks}, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", type=Path, help="Path to the capstone backend; use its virtualenv Python.")
    args = parser.parse_args()
    check(args.backend)

