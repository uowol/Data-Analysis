"""Kaggle competition/dataset browser for CLI and skill usage."""

import argparse
import glob
import json
import os
import subprocess
import sys
import zipfile

from kaggle.api.kaggle_api_extended import KaggleApi
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

_api = None


def get_api():
    global _api
    if _api is None:
        _api = KaggleApi()
        _api.authenticate()
    return _api


# -- Field definitions per browse type (label, dict_key, table_kwargs) --

COMPETITION_DETAIL_FIELDS = [
    ("Ref", "ref"),
    ("Title", "title"),
    ("Deadline", "deadline"),
    ("Reward", "reward"),
    ("Category", "category"),
    ("Teams", "team_count"),
    ("Tags", "tags"),
    ("URL", "url"),
]

DATASET_DETAIL_FIELDS = [
    ("Ref", "ref"),
    ("Title", "title"),
    ("Size", "size"),
    ("Downloads", "downloads"),
    ("Votes", "votes"),
    ("Usability", "usability"),
    ("Tags", "tags"),
    ("URL", "url"),
]

COMPETITION_TABLE_COLUMNS = [
    ("Title", {"max_width": 40}, "title"),
    ("Deadline", {}, "deadline"),
    ("Reward", {}, "reward"),
    ("Category", {}, "category"),
    ("Teams", {"justify": "right"}, "team_count"),
]

DATASET_TABLE_COLUMNS = [
    ("Title", {"max_width": 40}, "title"),
    ("Size", {"justify": "right"}, "size"),
    ("Downloads", {"justify": "right"}, "downloads"),
    ("Votes", {"justify": "right"}, "votes"),
    ("Usability", {"justify": "right"}, "usability"),
]


def _format_value(value):
    """Format a value for table/detail display."""
    if value is None:
        return "N/A"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "N/A"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def search_competitions(query="", sort_by="latestDeadline", limit=10):
    api = get_api()
    results = api.competitions_list(search=query, sort_by=sort_by, page_size=limit)
    return [
        {
            "ref": c.ref.replace("https://www.kaggle.com/competitions/", ""),
            "title": c.title,
            "deadline": str(c.deadline)[:10] if c.deadline else None,
            "reward": c.reward,
            "category": c.category,
            "team_count": c.team_count,
            "description": c.description or "",
            "tags": [t.name for t in (c.tags or [])],
            "url": c.ref,
        }
        for c in results.competitions[:limit]
    ]


def search_datasets(query="", sort_by="hottest", limit=10):
    api = get_api()
    results = api.dataset_list(search=query, sort_by=sort_by)
    return [
        {
            "ref": d.ref,
            "title": d.title,
            "size": _format_bytes(d.total_bytes),
            "size_bytes": d.total_bytes,
            "downloads": d.download_count,
            "votes": d.vote_count,
            "usability": d.usability_rating,
            "description": d.subtitle or "",
            "tags": [t.name for t in (d.tags or [])],
            "url": d.url,
        }
        for d in results[:limit]
    ]


def _format_bytes(b):
    if b is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f}{unit}"
        b /= 1024
    return f"{b:.1f}TB"


def print_table(items, browse_type):
    if not items:
        console.print("[yellow]No results found.[/yellow]")
        return

    columns = (
        COMPETITION_TABLE_COLUMNS
        if browse_type == "competition"
        else DATASET_TABLE_COLUMNS
    )

    table = Table(title=f"Kaggle {browse_type.title()} Results", show_lines=True)
    table.add_column("#", style="dim", width=3)
    for label, kwargs, _ in columns:
        table.add_column(label, **kwargs)

    for i, item in enumerate(items, 1):
        table.add_row(str(i), *[_format_value(item.get(key)) for _, _, key in columns])

    console.print(table)


def print_detail(item, browse_type):
    if browse_type == "competition":
        fields = COMPETITION_DETAIL_FIELDS
    else:
        fields = DATASET_DETAIL_FIELDS

    lines = [
        f"[bold]{label}:[/bold] {_format_value(item.get(key))}" for label, key in fields
    ]
    lines.append(f"\n{item.get('description', '')}")

    console.print(Panel("\n".join(lines), title=item["title"], expand=False))


def download_item(item, is_competition=False, dest=None):
    """Download a Kaggle dataset or competition data."""
    ref = item["ref"]
    if dest is None:
        # competition ref: "titanic", dataset ref: "owner/name"
        slug = ref.split("/")[-1]
        dest = f"kaggle_projects/{slug}/data"

    os.makedirs(dest, exist_ok=True)
    console.print(f"[bold]Downloading[/bold] {ref} → {dest}")

    if is_competition:
        cmd = ["kaggle", "competitions", "download", "-c", ref, "-p", dest]
    else:
        cmd = ["kaggle", "datasets", "download", ref, "-p", dest]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Download failed:[/red] {result.stderr.strip()}")
        sys.exit(1)

    # Extract zip files
    for zip_path in glob.glob(f"{dest}/*.zip"):
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest)
        os.remove(zip_path)

    console.print(f"[green]Downloaded and extracted to {dest}[/green]")

    # List downloaded files
    files = os.listdir(dest)
    for f in sorted(files):
        size = os.path.getsize(os.path.join(dest, f))
        console.print(f"  {f} ({_format_bytes(size)})")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Browse Kaggle competitions/datasets")
    parser.add_argument(
        "--type",
        choices=["competition", "dataset"],
        default="dataset",
        help="Type to browse (default: dataset)",
    )
    parser.add_argument("--search", default="", help="Search keyword")
    parser.add_argument(
        "--sort",
        default=None,
        help="Sort by (competition: latestDeadline, numberOfTeams, recentlyCreated | dataset: hottest, votes, updated, active)",
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Max results (default: 10)"
    )
    parser.add_argument(
        "--detail",
        type=int,
        default=None,
        help="Show detail for item at index (1-based)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON instead of table"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the selected item (requires --detail)",
    )
    parser.add_argument(
        "--download-path",
        default=None,
        help="Download destination (default: kaggle_projects/<ref>/data)",
    )
    args = parser.parse_args(argv)

    sort_by = args.sort
    if sort_by is None:
        sort_by = "latestDeadline" if args.type == "competition" else "hottest"

    if args.type == "competition":
        items = search_competitions(args.search, sort_by, args.limit)
    else:
        items = search_datasets(args.search, sort_by, args.limit)

    if args.download and args.detail is None:
        console.print("[red]--download requires --detail to select an item[/red]")
        sys.exit(1)

    if args.detail is not None:
        idx = args.detail - 1
        if 0 <= idx < len(items):
            if args.json:
                print(json.dumps(items[idx], ensure_ascii=False, indent=2))
            else:
                print_detail(items[idx], args.type)
            if args.download:
                download_item(
                    items[idx],
                    is_competition=(args.type == "competition"),
                    dest=args.download_path,
                )
        else:
            console.print(f"[red]Invalid index: {args.detail} (1-{len(items)})[/red]")
            sys.exit(1)
    elif args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print_table(items, args.type)


if __name__ == "__main__":
    main()
