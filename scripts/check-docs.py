"""Check local public Markdown links, image references and code fences."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1]
errors = []
checked = 0

for document in sorted(root.rglob("*.md")):
    if ".git" in document.parts:
        continue
    source = document.read_text()
    if len(re.findall(r"^\s*```", source, re.MULTILINE)) % 2:
        errors.append(f"{document.relative_to(root)}: unbalanced code fence")
    references = re.findall(r"\]\(([^\s)]+)(?:\s+[^)]*)?\)", source)
    references += re.findall(r'(?:src|href)="([^"]+)"', source)
    for reference in references:
        url = urlsplit(reference.strip("<>"))
        if url.scheme or url.netloc:
            continue
        target = (document.parent / unquote(url.path)).resolve() if url.path else document
        if not target.exists():
            errors.append(f"{document.relative_to(root)}: missing {reference}")
            continue
        if url.fragment and target.suffix == ".md":
            headings = re.findall(r"^#{1,6}\s+(.+)$", target.read_text(), re.MULTILINE)
            anchors = {re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings}
            if unquote(url.fragment) not in anchors:
                errors.append(f"{document.relative_to(root)}: missing anchor {reference}")
        checked += 1

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Documentation OK: {checked} local references and balanced fences.")
