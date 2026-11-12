"""Searches every service's logs for personal or genetic data (Phase 6.3, V6.3.3).

    python scripts/scan_logs.py              # the running stack's logs
    python scripts/scan_logs.py --since 2h   # only recent lines

Run it after a full demo or browser run, so the logs hold real traffic. It looks for marker values:
- national ID formats (the UAE "784-" pattern and the India demo pattern),
- gene symbols from the packs, as whole words,
- the synthetic personas' names,
- bearer tokens, JWTs, invitation tokens in paths, email addresses, and AI Studio API keys.

Gene symbols in Keycloak's or OpenFGA's own startup lines would be noise, so only the services that
handle health data are scanned for genes: api, worker, beat and web. Every service is scanned for IDs,
tokens and emails. Exit code 1 if anything is found, with each hit's service and pattern, never the
value itself, so the report can't leak what it found.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - runs docker with fixed arguments
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "infra" / "docker-compose.yml")]
HEALTH_SERVICES = {"api", "worker", "beat", "web"}

EVERYWHERE = {
    "UAE national ID": re.compile(r"\b784-\d{4}-\d{7}-\d\b"),
    "India demo ID": re.compile(r"\b\d{2}-\d{4}-\d{4}-\d{4}\b"),
    "bearer token": re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "invitation token in a path": re.compile(r"/i/[A-Za-z0-9_-]{20,}"),
    "email address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    # A settings error prints the values it was given. Those are SecretStr fields, but pydantic
    # reports the raw input it was handed, before any of it was wrapped, so a crash at startup can
    # put the AI key in a container log. Both AI Studio key shapes.
    "Google API key": re.compile(r"\b(AIza[0-9A-Za-z_\-]{30,45}|AQ\.[0-9A-Za-z_\-]{20,})"),
}
NAMES = ["Fatima", "Khalid", "Priya", "Rohan"]
# Keycloak's own admin and service accounts appear by design and aren't people.
ALLOWED_EMAILS = re.compile(r"@(example\.(com|org)|samvid\.local|keycloak\.org)\b")


def genes() -> list[str]:
    found: set[str] = set()
    for panel in (ROOT / "backend" / "packs").glob("*/panel.yaml"):
        found |= set(re.findall(r"^\s{2,4}([A-Z][A-Z0-9]{2,9}):", panel.read_text("utf-8"), re.M))
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="such as 30m or 2h")
    args = parser.parse_args()
    if args.since and not re.fullmatch(r"\d{1,4}[smh]", args.since):
        sys.stderr.write("--since takes a number and s, m or h, such as 30m.\n")
        return 2
    command = [*COMPOSE, "logs", "--no-color"] + (["--since", args.since] if args.since else [])
    # Fixed arguments, plus a --since value checked just above.
    output = subprocess.run(  # noqa: S603  # nosec B603
        command, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )
    if output.returncode != 0:
        sys.stderr.write("Couldn't read the logs. Is the stack running?\n")
        return 2

    gene_patterns = {f"gene {g}": re.compile(rf"\b{g}\b") for g in genes()}
    name_patterns = {f"name {n}": re.compile(rf"\b{n}\b") for n in NAMES}
    hits: Counter[tuple[str, str]] = Counter()
    lines = output.stdout.splitlines()
    for line in lines:
        service = (
            line.split("|", 1)[0].strip().removeprefix("samvid-").rsplit("-", 1)[0]
            if "|" in line
            else "?"
        )
        for label, pattern in EVERYWHERE.items():
            for match in pattern.finditer(line):
                if label == "email address" and ALLOWED_EMAILS.search(match.group(0)):
                    continue
                hits[(service, label)] += 1
        if service in HEALTH_SERVICES:
            for label, pattern in {**gene_patterns, **name_patterns}.items():
                if pattern.search(line):
                    hits[(service, label)] += 1

    sys.stdout.write(
        f"Scanned {len(lines)} log lines for {len(gene_patterns)} gene symbols, {len(NAMES)} names, IDs, tokens and emails.\n"
    )
    if not hits:
        sys.stdout.write("Nothing found.\n")
        return 0
    for (service, label), count in sorted(hits.items()):
        sys.stdout.write(f"FOUND  {service:<10} {label:<28} {count} line(s)\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
