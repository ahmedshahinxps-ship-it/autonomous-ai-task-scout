#!/usr/bin/env python3
"""Compare current read-only leads with the prior GitHub Actions report artifact.

This does NOT claim tasks or establish that an opportunity is funded, available,
AI-permitted, or payable to any bank. 'New' means new to the saved shortlist.
"""
import argparse
import html
import io
import json
import os
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from urllib.parse import urlparse

MAX_BYTES = 6_000_000

class SafeArtifactRedirect(HTTPRedirectHandler):
    """Never forward GitHub bearer credentials to Azure blob download hosts."""
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        new_request = super().redirect_request(request, fp, code, msg, headers, newurl)
        if new_request is not None and urlparse(newurl).hostname != "api.github.com":
            for dictionary in (new_request.headers, new_request.unredirected_hdrs):
                for key in list(dictionary):
                    if key.lower() == "authorization":
                        del dictionary[key]
        return new_request


def fetch_json(url, token):
    req = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "AutonomousTaskScout/0.5",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=20) as response:
        chunk = response.read(MAX_BYTES + 1)
    if len(chunk) > MAX_BYTES:
        raise ValueError("GitHub response too large")
    return json.loads(chunk)

def prior_report(repository, token, current_run):
    if not token or not repository or "/" not in repository:
        raise ValueError("GitHub Actions API credentials unavailable")
    artifacts = fetch_json(
        "https://api.github.com/repos/" + repository
        + "/actions/artifacts?name=daily-opportunity-report&per_page=30", token,
    ).get("artifacts", [])
    for artifact in artifacts:
        if artifact.get("expired") or artifact.get("workflow_run", {}).get("id") == current_run:
            continue
        url = artifact.get("archive_download_url", "")
        if not url.startswith("https://api.github.com/"):
            continue
        req = Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "User-Agent": "AutonomousTaskScout/0.5",
        })
        with build_opener(SafeArtifactRedirect()).open(req, timeout=25) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Artifact ZIP over limit")
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if "opportunities.json" not in archive.namelist():
                continue
            if archive.getinfo("opportunities.json").file_size > MAX_BYTES:
                raise ValueError("Prior JSON over limit")
            data = json.loads(archive.read("opportunities.json"))
        if not isinstance(data.get("candidates"), list):
            continue
        return data, artifact.get("workflow_run", {}).get("id")
    return None, None

def compare(current, previous, previous_run_id=None, status="compared"):
    candidates = current.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("Current report is missing candidate list")
    old = set()
    if previous is not None:
        old = {str(x.get("url")) for x in previous.get("candidates", [])
               if isinstance(x, dict) and x.get("url")}
    new = []
    if previous is not None and status == "compared":
        seen = set()
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            url = str(candidate.get("url") or "")
            if url and url not in old and url not in seen:
                new.append({
                    "title": str(candidate.get("title") or "")[:180],
                    "url": url,
                    "source": str(candidate.get("source") or "")[:80],
                    "reward_usd": candidate.get("reward_usd"),
                    "score": candidate.get("score"),
                    "payment_state": candidate.get("payment_state", "unknown"),
                })
                seen.add(url)
    return {
        "comparison_status": status,
        "previous_run_id": previous_run_id,
        "current_shortlist_count": len(candidates),
        "newly_shortlisted_count": len(new),
        "newly_shortlisted": new[:40],
        "notice": (
            "New means not in the previous saved shortlist, NOT necessarily newly posted. "
            "Listings are not verified as funded, accepted, AI-compatible or payable. "
            "No tasks were claimed or submitted."
        ),
    }

def html_report(result):
    escape = lambda value: html.escape(str(value), quote=True)
    rows = []
    for item in result["newly_shortlisted"]:
        url = item["url"]
        if not url.startswith("https://"):
            continue
        rows.append(
            "<article><h3>" + escape(item["title"]) + "</h3><p>Listed reward: $"
            + escape(item["reward_usd"]) + " · Source: " + escape(item["source"])
            + " · Fit: " + escape(item["score"]) + "/100</p><a href=\""
            + escape(url) + "\" rel=\"noopener noreferrer\" target=\"_blank\">Original listing</a></article>"
        )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>New task leads</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>body{font:16px system-ui;background:#f6f7fa;color:#1d2939}'
        'main{max-width:800px;margin:36px auto;padding:12px}article{background:white;'
        'border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}a{color:#2357bc}</style>'
        '<main><h1>Newly shortlisted task leads</h1><p>Comparison: '
        + escape(result["comparison_status"]) + ' · ' + str(result["newly_shortlisted_count"])
        + ' new to shortlist</p><p><strong>Unverified leads, not earnings or approved jobs.</strong> '
        'No submissions or payments.</p>' + "".join(rows) + "</main></html>"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="output/opportunities.json")
    parser.add_argument("--output", default="output")
    parser.add_argument("--previous", help="Offline test: existing previous report")
    args = parser.parse_args()
    current = json.loads(Path(args.input).read_text(encoding="utf-8"))
    previous, run, status = None, None, "baseline"
    if args.previous:
        previous = json.loads(Path(args.previous).read_text(encoding="utf-8"))
        status = "compared"
    else:
        try:
            previous, run = prior_report(
                os.environ.get("GITHUB_REPOSITORY", ""),
                os.environ.get("GITHUB_TOKEN", ""),
                int(os.environ.get("GITHUB_RUN_ID", "0")),
            )
            status = "compared" if previous is not None else "baseline"
        except (HTTPError, URLError, TimeoutError, ValueError, OSError, zipfile.BadZipFile, KeyError) as exc:
            if isinstance(exc, HTTPError):
                print("Prior report HTTP", exc.code, "host", urlparse(exc.url).hostname)
            status = "unavailable"
            print("Prior artifact unavailable (" + type(exc).__name__ + "), no false new leads reported.")
    result = compare(current, previous, run, status)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "new_leads.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "new_leads.html").write_text(html_report(result), encoding="utf-8")
    print("Prior-comparison:", status, "new shortlist entries:", result["newly_shortlisted_count"])

if __name__ == "__main__":
    main()
