#!/usr/bin/env python3
"""Generate a list of doc URLs for lychee link checking.

Reads the docs.json navigation from the build output and outputs one
http://localhost:3000/{path} URL per line. Used by the CI link check
workflow to ensure lychee checks all doc pages, not just the homepage.
"""

import json
import sys
from pathlib import Path


def extract_pages_from_pages_array(items: list) -> set[str]:
    """Recursively extract page paths from a pages array."""
    result: set[str] = set()

    for item in items:
        if isinstance(item, str):
            result.add(item)
        elif isinstance(item, dict):
            if "pages" in item:
                result.update(extract_pages_from_pages_array(item["pages"]))

    return result


def extract_all_pages(docs: dict) -> set[str]:
    """Extract all page paths from docs.json navigation structure."""
    pages: set[str] = set()
    navigation = docs.get("navigation", {})
    products = navigation.get("products", [])

    for product in products:
        if isinstance(product, dict):
            if "pages" in product:
                pages.update(extract_pages_from_pages_array(product["pages"]))

            if "tabs" in product:
                for tab in product["tabs"]:
                    if isinstance(tab, dict):
                        if "pages" in tab:
                            pages.update(extract_pages_from_pages_array(tab["pages"]))
                        elif "groups" in tab:
                            for group in tab["groups"]:
                                if isinstance(group, dict) and "pages" in group:
                                    pages.update(
                                        extract_pages_from_pages_array(group["pages"])
                                    )

            if "dropdowns" in product:
                for dropdown in product["dropdowns"]:
                    if isinstance(dropdown, dict) and "tabs" in dropdown:
                        for tab in dropdown["tabs"]:
                            if isinstance(tab, dict) and "pages" in tab:
                                pages.update(
                                    extract_pages_from_pages_array(tab["pages"])
                                )

            if "groups" in product:
                for group in product["groups"]:
                    if isinstance(group, dict) and "pages" in group:
                        pages.update(extract_pages_from_pages_array(group["pages"]))

    return pages


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: generate_lychee_urls.py <docs.json> [base_url] [output_file]",
            file=sys.stderr,
        )
        return 2

    docs_path = Path(sys.argv[1])
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000"
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    if not docs_path.exists():
        print(f"Error: docs.json not found at {docs_path}", file=sys.stderr)
        return 2

    with open(docs_path) as f:
        docs = json.load(f)

    urls = []
    for path in sorted(extract_all_pages(docs)):
        url_path = "" if path == "index" else path
        url = f"{base_url.rstrip('/')}/{url_path}" if url_path else f"{base_url.rstrip('/')}/"
        urls.append(url)

    output = "\n".join(urls)
    if output_path:
        output_path.write_text(output)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
