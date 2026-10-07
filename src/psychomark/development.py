"""Development helpers; no trust in a browser-supplied forwarded host."""

import hashlib
import os
import re
from pathlib import Path


def codespaces_origin(port: int) -> str | None:
    if os.environ.get("CODESPACES") != "true":
        return None
    name = os.environ.get("CODESPACE_NAME", "")
    domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name):
        return None
    if (
        not domain
        or len(domain) > 253
        or not all(
            re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label) and len(label) <= 63
            for label in domain.split(".")
        )
    ):
        return None
    return f"https://{name}-{port}.{domain}"


def source_revision(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if (
            path.is_file()
            and path.suffix in {".py", ".js", ".css", ".html", ".svg"}
            and "__pycache__" not in path.parts
        ):
            try:
                data = path.read_bytes()
            except FileNotFoundError:
                continue
            digest.update(str(path.relative_to(root)).encode())
            digest.update(data)
    return digest.hexdigest()
