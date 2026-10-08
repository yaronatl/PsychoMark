"""Check local inline Markdown file links (not anchors or external URLs)."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "AGENTS.md",
    ROOT / "PRODUCT.md",
    ROOT / "DESIGN.md",
    *sorted((ROOT / "docs").rglob("*.md")),
    *sorted((ROOT / ".github").rglob("*.md")),
]


def main() -> int:
    failures = []
    for document in DOCUMENTS:
        # Ignore examples in fenced code blocks. Documentation uses inline links.
        content = re.sub(r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.S)
        for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", content):
            link = urlsplit(target.strip("<>"))
            if link.scheme or link.netloc or not link.path:
                continue
            destination = document.parent / unquote(link.path)
            if not destination.exists():
                failures.append(f"{document.relative_to(ROOT)}: missing {target}")
    for failure in failures:
        print(failure)
    print(
        f"Documentation: {len(DOCUMENTS)} files checked, {len(failures)} broken local file links."
    )
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
