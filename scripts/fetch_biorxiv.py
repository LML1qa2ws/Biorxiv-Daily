#!/usr/bin/env python3
"""
BioRxiv 每日文献抓取脚本
Daily BioRxiv paper fetching script with OpenClaw integration.

Usage:
    python scripts/fetch_biorxiv.py [--config config.yaml] [--date YYYY-MM-DD]
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import feedparser
import requests
import yaml
from dateutil import parser as dateparser


BIORXIV_RSS_BASE = "https://connect.biorxiv.org/biorxiv_xml.php?subject={subject}"
BIORXIV_API_BASE = "https://api.biorxiv.org/details/{server}/{start}/{end}/0/json"
MEDRXIV_RSS_BASE = "https://connect.medrxiv.org/medrxiv_xml.php?subject={subject}"

DEFAULT_MAX_RESULTS_PER_QUERY = 10
DEFAULT_MAX_ABSTRACT_LENGTH = 300


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_papers_via_api(server: str, start_date: str, end_date: str) -> list:
    """
    Fetch papers from BioRxiv/MedRxiv API for a date range.

    Args:
        server: 'biorxiv' or 'medrxiv'
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of paper dicts
    """
    url = BIORXIV_API_BASE.format(server=server, start=start_date, end=end_date)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("collection", [])
    except requests.RequestException as e:
        print(f"[WARNING] Failed to fetch from {server} API: {e}", file=sys.stderr)
        return []


def filter_papers_by_keywords(papers: list, queries: list) -> list:
    """
    Filter papers by keyword queries (case-insensitive, supports AND/OR logic).

    Args:
        papers: List of paper dicts from API
        queries: List of search query strings

    Returns:
        Filtered list of papers with matched queries attached
    """
    matched = []
    seen_dois = set()

    for paper in papers:
        title = paper.get("title", "").lower()
        abstract = paper.get("abstract", "").lower()
        text = title + " " + abstract

        matched_queries = []
        for query in queries:
            if _matches_query(text, query):
                matched_queries.append(query)

        if matched_queries and paper.get("doi") not in seen_dois:
            paper["matched_queries"] = matched_queries
            matched.append(paper)
            seen_dois.add(paper.get("doi"))

    return matched


def _matches_query(text: str, query: str) -> bool:
    """
    Check if text matches a query string.
    Supports AND logic (space-separated terms joined by AND).

    Args:
        text: Text to search in (lowercased)
        query: Query string, e.g. "machine learning AND genomics"

    Returns:
        True if text matches the query
    """
    query_lower = query.lower()
    if " and " in query_lower:
        parts = [p.strip() for p in query_lower.split(" and ")]
        return all(part in text for part in parts)
    if " or " in query_lower:
        parts = [p.strip() for p in query_lower.split(" or ")]
        return any(part in text for part in parts)
    return query_lower in text


def format_paper_markdown(paper: dict, index: int, max_abstract_length: int = DEFAULT_MAX_ABSTRACT_LENGTH) -> str:
    """Format a single paper as Markdown."""
    title = paper.get("title", "N/A")
    authors = paper.get("authors", "N/A")
    doi = paper.get("doi", "")
    date_str = paper.get("date", "")
    abstract = paper.get("abstract", "").strip()
    category = paper.get("category", "")
    server = paper.get("server", "biorxiv")
    matched = ", ".join(paper.get("matched_queries", []))

    url = f"https://doi.org/{doi}" if doi else ""

    # Truncate abstract to configured length
    if len(abstract) > max_abstract_length:
        abstract = abstract[:max_abstract_length].rstrip() + "..."

    lines = [
        f"### {index}. {title}",
        "",
        f"- **作者 / Authors**: {authors}",
        f"- **来源 / Source**: {server.upper()} | {category}",
        f"- **日期 / Date**: {date_str}",
        f"- **匹配关键词 / Matched queries**: {matched}",
    ]
    if url:
        lines.append(f"- **链接 / Link**: [{doi}]({url})")
    lines += [
        "",
        f"> {abstract}",
        "",
    ]
    return "\n".join(lines)


def generate_report(papers: list, report_date: str, config: dict) -> str:
    """Generate a Markdown daily report."""
    total = len(papers)
    lines = [
        f"# BioRxiv 每日文献速递 / Daily Literature Report",
        f"",
        f"**日期 / Date**: {report_date}",
        f"**文章总数 / Total papers**: {total}",
        f"",
        "---",
        "",
    ]

    if total == 0:
        lines.append("今日暂无匹配文献。/ No matching papers found today.")
        return "\n".join(lines)

    # Group by matched query
    by_query: dict = {}
    for paper in papers:
        for q in paper.get("matched_queries", []):
            by_query.setdefault(q, []).append(paper)

    max_results = config.get("max_results_per_query", DEFAULT_MAX_RESULTS_PER_QUERY)
    max_abstract = config.get("max_abstract_length", DEFAULT_MAX_ABSTRACT_LENGTH)

    for query, qpapers in by_query.items():
        lines += [
            f"## 🔍 关键词 / Query: `{query}`",
            "",
            f"共 {len(qpapers)} 篇 / {len(qpapers)} paper(s)",
            "",
        ]
        for i, paper in enumerate(qpapers[:max_results], start=1):
            lines.append(format_paper_markdown(paper, i, max_abstract_length=max_abstract))

    lines += [
        "---",
        "",
        f"*由 [BioRxiv 每日推送](https://github.com/LML1qa2ws/Biorxiv-) 自动生成 / "
        f"Auto-generated by BioRxiv Daily Push*",
        "",
    ]
    return "\n".join(lines)


def save_report(content: str, report_date: str, reports_dir: str) -> str:
    """Save Markdown report to file."""
    Path(reports_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{report_date}.md"
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[INFO] Report saved to {filepath}")
    return filepath


def notify_openclaw(report_content: str, report_date: str, openclaw_config: dict) -> bool:
    """
    Notify OpenClaw with the daily report.

    This calls the OpenClaw API endpoint if configured.
    Credentials are read from environment variables:
        OPENCLAW_API_URL   - OpenClaw API base URL
        OPENCLAW_API_KEY   - OpenClaw API key

    Args:
        report_content: Markdown content of the report
        report_date: Date string for the report
        openclaw_config: OpenClaw section from config.yaml

    Returns:
        True if notification succeeded or is disabled, False on error
    """
    if not openclaw_config.get("enabled", False):
        print("[INFO] OpenClaw push is disabled in config.")
        return True

    api_url = os.environ.get("OPENCLAW_API_URL", "").rstrip("/")
    api_key = os.environ.get("OPENCLAW_API_KEY", "")

    if not api_url or not api_key:
        print(
            "[WARNING] OPENCLAW_API_URL or OPENCLAW_API_KEY not set. "
            "Skipping OpenClaw push.",
            file=sys.stderr,
        )
        # Missing credentials are treated as a soft failure so the workflow
        # does not fail when OpenClaw secrets have not been configured yet.
        return True

    skill = openclaw_config.get("skill", "literature-daily-report")
    channels = openclaw_config.get("channels", [])

    payload = {
        "skill": skill,
        "date": report_date,
        "content": report_content,
        "channels": channels,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{api_url}/api/push",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        print(f"[INFO] OpenClaw push successful: {response.status_code}")
        return True
    except requests.RequestException as e:
        print(f"[ERROR] OpenClaw push failed: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fetch daily BioRxiv papers and push via OpenClaw."
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration YAML file (default: config.yaml)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Report date in YYYY-MM-DD format (default: today)",
    )
    args = parser.parse_args()

    # Resolve config path relative to repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    config_path = repo_root / args.config

    config = load_config(str(config_path))

    report_date = args.date or date.today().isoformat()
    # Fetch from yesterday to today to capture newly posted papers
    yesterday = (date.fromisoformat(report_date) - timedelta(days=1)).isoformat()

    sources = config.get("sources", ["biorxiv"])
    queries = config.get("search_queries", [])
    reports_dir = repo_root / config.get("output", {}).get("reports_dir", "reports")

    all_papers = []
    for source in sources:
        print(f"[INFO] Fetching from {source} ({yesterday} to {report_date})...")
        papers = fetch_papers_via_api(source, yesterday, report_date)
        for p in papers:
            p["server"] = source
        all_papers.extend(papers)

    print(f"[INFO] Total papers fetched: {len(all_papers)}")

    matched_papers = filter_papers_by_keywords(all_papers, queries)
    print(f"[INFO] Matched papers after filtering: {len(matched_papers)}")

    report_content = generate_report(matched_papers, report_date, config)

    if config.get("output", {}).get("save_markdown", True):
        save_report(report_content, report_date, str(reports_dir))

    openclaw_cfg = config.get("openclaw", {})
    success = notify_openclaw(report_content, report_date, openclaw_cfg)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
