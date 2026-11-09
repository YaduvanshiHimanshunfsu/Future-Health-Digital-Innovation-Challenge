"""Run the whole of Samvid with one command, and watch what it does.

    python Run_Samvid.py                 start everything, prepare demo data, show live activity
    python Run_Samvid.py --status        show what's running, then exit
    python Run_Samvid.py --stop          stop everything, keeping the data
    python Run_Samvid.py --reset         stop everything and delete all data (asks first)
    python Run_Samvid.py --check         start, then run the end-to-end smoke check

Other options: --no-build, --no-seed, --keep-running, --verbose, --open, --show-password.
Ctrl+C stops the live view and then stops the services, unless --keep-running is given.

Needs Docker Desktop, plus uv for the demo data. Everything runs on this machine only, and all data
is synthetic. Updated at the end of every phase: see PHASES below.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INFRA = ROOT / "infra"
ENV_FILE = INFRA / ".env"
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    str(ENV_FILE),
    "-f",
    str(INFRA / "docker-compose.yml"),
]
# By address: on Windows, "localhost" tries IPv6 first and adds about 2 s to every connection.
WEB, API, KEYCLOAK = "http://localhost:3000", "http://127.0.0.1:8000", "http://localhost:8080"

# What each phase delivered. Updated whenever a phase is finished.
PHASES = [
    ("1", "Foundation: secure API, database, audit trail, local stack", "done"),
    ("2", "Risk engine, encryption, lab reports, country packs, synthetic data", "done"),
    ("3", "Consent, couple check, family invitations, access log, emergency access", "done"),
    ("UI", "Web app from the Stitch design, in English and Hindi, wired to the backend", "done"),
    (
        "UI+",
        "Motion library, chart kit, reading levels, listen, couple and pregnancy visuals",
        "done",
    ),
    ("4", "Explanations by Gemini or local Ollama, checked, with templates as the fallback", "done"),
    ("5", "Care pathway, booking, measurement, dashboards", "in progress"),
    ("6", "Evaluation, hardening, submission", "planned"),
]

DEMO_ACCOUNTS = [
    ("demo-fatima", "A carrier. Link with demo-khalid on the Partner page, then try Ask Samvid"),
    ("demo-khalid", "Shares a finding with demo-fatima"),
    ("demo-x-carrier", "An X-linked result, with its own picture, and the Options page"),
    ("demo-uncertain", "An uncertain finding, with no number"),
    ("demo-no-report", "No report yet, which is never shown as a result"),
    ("demo-priya", "The India pack, in Hindi"),
    ("demo-counsellor", "Takes cases from the queue, with time-left rings and a priority chart"),
    ("demo-doctor", "Emergency access to a case"),
    ("demo-auditor", "Reviews emergency access"),
    ("demo-coordinator", "Programme metrics and equity, aggregates only (synthetic)"),
]

COLOURS = {
    "web": "\033[38;5;33m",
    "api": "\033[38;5;35m",
    "worker": "\033[38;5;135m",
    "beat": "\033[38;5;141m",
    "keycloak": "\033[38;5;214m",
    "openfga": "\033[38;5;37m",
    "postgres": "\033[38;5;245m",
    "redis": "\033[38;5;245m",
    "launcher": "\033[38;5;111m",
}
RESET, BOLD, DIM, RED, GREEN, YELLOW = (
    "\033[0m",
    "\033[1m",
    "\033[2m",
    "\033[31m",
    "\033[32m",
    "\033[33m",
)
APP_SERVICES = ["web", "api", "worker", "beat", "openfga", "keycloak"]
QUIET_ROUTES = {"/health", "/ready"}
ROUTINE_TASKS = ("samvid.apply_authz_outbox", "samvid.reconcile_authz", "samvid.ping")


def say(text: str = "") -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def note(text: str, colour: str = COLOURS["launcher"]) -> None:
    say(f"{DIM}{datetime.now():%H:%M:%S}{RESET} {colour}{'samvid':<9}{RESET} {text}")


def fail(text: str) -> int:
    note(f"{RED}{text}{RESET}")
    return 1


def run(command: list[str], *, quiet: bool = False, cwd: Path = ROOT) -> int:
    if quiet:
        # Fixed commands from this file only, never user input.
        done = subprocess.run(  # noqa: S603
            command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if done.returncode != 0:
            say(done.stdout[-2000:] + done.stderr[-2000:])
        return done.returncode
    return subprocess.run(command, cwd=cwd, check=False).returncode  # noqa: S603


def banner() -> None:
    say()
    say(
        f"{BOLD}  Samvid{RESET}  {DIM}understanding genetic carrier results, privately. A prototype with synthetic data.{RESET}"
    )
    say()
    for phase, what, state in PHASES:
        colour = GREEN if state == "done" else YELLOW if state == "in progress" else DIM
        say(f"  {colour}{state:<12}{RESET} Phase {phase:<3} {what}")
    say()


# --- Preflight ------------------------------------------------------------------------------------


def docker_ready() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True, check=False).returncode == 0  # noqa: S607


def ensure_docker() -> bool:
    if docker_ready():
        return True
    desktop = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")
    if os.name == "nt" and desktop.exists():
        note("Docker isn't running. Starting Docker Desktop...")
        subprocess.Popen([str(desktop)])  # noqa: S603
        for _ in range(60):
            time.sleep(3)
            if docker_ready():
                note("Docker is ready.")
                return True
    return False


def ensure_env() -> None:
    # Creates infra/.env on a first run, and fills in settings added since. Never changes a value.
    run([sys.executable, str(ROOT / "scripts" / "generate_env.py")], quiet=True)


def read_env() -> dict[str, str]:
    lines = ENV_FILE.read_text("utf-8").splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def port_shadowed(port: int) -> bool:
    """Docker listens on IPv4 only. Something on IPv6 would answer "localhost" in its place."""
    try:
        with socket.create_connection(("::1", port), timeout=0.5):
            return True
    except OSError:
        return False


def get(url: str, timeout: float = 3.0) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - local only
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except (OSError, ValueError):
        return 0


# --- Starting -------------------------------------------------------------------------------------


def start(build: bool) -> bool:
    note("Starting the database, sign-in, authorisation, backend, workers and web app...")
    note(f"{DIM}The first build takes a few minutes. Later starts take under a minute.{RESET}")
    command = [*COMPOSE, "up", "-d", "--wait"]
    if build:
        command.insert(len(COMPOSE) + 2, "--build")
    if run(command) != 0:
        return False
    for name, url in (
        ("web app", f"{WEB}/en"),
        ("API", f"{API}/v1/ready"),
        ("sign-in", "http://127.0.0.1:8080/realms/samvid"),
    ):
        status = get(url)
        note(
            f"{name:<9} {GREEN + 'ready' + RESET if 200 <= status < 400 else RED + f'status {status}' + RESET}  {url}"
        )
    if port_shadowed(3000):
        note(
            f"{YELLOW}Something else is answering on [::1]:3000, probably an old `next start`. "
            f"Browsers may reach it instead of the app. Stop it, then reload.{RESET}"
        )
    return True


def setting(name: str, default: str = "") -> str:
    """Your environment first, then infra/.env, the same order Docker Compose uses."""
    return os.environ.get(name) or read_env().get(name, "") or default


def models() -> None:
    """Says which model will answer, and why not, before anyone asks a question. Prints no key."""
    providers = [
        p.strip() for p in setting("LLM_PROVIDER", "gemini,ollama").split(",") if p.strip()
    ]
    note(f"AI models, tried in this order: {', '.join(providers)}, then the reviewed templates")
    for provider in providers:
        if provider == "gemini":
            key = setting("GEMINI_API_KEY")
            if not key:
                note(f"  gemini    {YELLOW}no GEMINI_API_KEY set, so it's skipped{RESET}")
                continue
            request = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1",
                headers={"x-goog-api-key": key},
            )
            try:
                with urllib.request.urlopen(request, timeout=8) as response:  # noqa: S310 - fixed https URL
                    code = int(response.status)
            except urllib.error.HTTPError as exc:
                code = int(exc.code)
            except OSError:
                code = 0
            if code == 200:
                note(
                    f"  gemini    {GREEN}key accepted{RESET}, model {setting('GEMINI_MODEL', 'gemini-2.5-flash')}"
                )
            elif code in (400, 401, 403):
                note(
                    f"  gemini    {RED}Google rejected the key (status {code}){RESET}. "
                    "Make one at aistudio.google.com/apikey (it starts with AIza). Until then the next model answers."
                )
            else:
                note(f"  gemini    {YELLOW}not reachable from here (status {code}){RESET}")
        elif provider == "ollama":
            tag = setting("OLLAMA_MODEL", "qwen2.5:3b")
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:11434/api/tags", timeout=3
                ) as response:  # noqa: S310 - local only
                    names = [m.get("name") for m in json.load(response).get("models", [])]
            except (OSError, ValueError):
                note(
                    f"  ollama    {YELLOW}not running on this machine. Start the Ollama app.{RESET}"
                )
                continue
            if tag in names:
                note(f"  ollama    {GREEN}ready{RESET}, model {tag}, on this machine only")
            else:
                note(
                    f"  ollama    {YELLOW}running, but {tag} isn't pulled. Run: ollama pull {tag}{RESET}"
                )
        elif provider != "template":
            note(f"  {provider:<9} configured in infra/.env")


def seed(show_password: bool) -> None:
    uv = shutil.which("uv")
    if uv is None:
        note(
            f"{YELLOW}uv isn't installed, so no demo accounts were created. See docs/runbook_local_stack.md.{RESET}"
        )
        return
    backend = ROOT / "backend"
    if not (backend / "synthetic" / "out" / "ae-abu-dhabi" / "personas" / "fatima.json").exists():
        note("Generating the synthetic population...")
        run(
            [uv, "run", "--project", str(backend), "python", "-m", "synthetic.generate"],
            quiet=True,
            cwd=backend,
        )
    note("Creating demo accounts and their synthetic lab reports...")
    if (
        run(
            [
                uv,
                "run",
                "--project",
                str(backend),
                "python",
                str(ROOT / "scripts" / "seed_demo.py"),
            ],
            quiet=True,
            cwd=backend,
        )
        != 0
    ):
        note(f"{YELLOW}Demo accounts couldn't be created. The app still runs.{RESET}")
        return
    note("Adding synthetic programme activity, so the metrics dashboard has something to show...")
    if run([*COMPOSE, "exec", "-T", "api", "python", "-m", "app.ops.seed_metrics"], quiet=True) != 0:
        note(f"{YELLOW}The synthetic metrics couldn't be added. The dashboard will show mostly '<10'.{RESET}")
    password = read_env().get("DEMO_PASSWORD", "")
    say()
    say(f'  {BOLD}Open {WEB}{RESET} and choose "Start privately". Demo accounts:')
    for name, what in DEMO_ACCOUNTS:
        say(f"    {COLOURS['web']}{name:<17}{RESET} {what}")
    shown = (
        password if show_password else "DEMO_PASSWORD in infra/.env (or run with --show-password)"
    )
    say(f"  Password for all of them: {shown}")
    say(f"  {DIM}API docs: {API}/docs    Sign-in admin: {KEYCLOAK}{RESET}")
    say()


# --- Live view ------------------------------------------------------------------------------------


def describe(service: str, line: str, verbose: bool) -> str | None:
    """Turns one log line into something a person can read, or None to hide it."""
    try:
        entry = json.loads(line)
    except ValueError:
        entry = None
    if not isinstance(entry, dict):
        if service in {"keycloak", "postgres", "redis", "openfga"} and not verbose:
            return line if any(word in line for word in ("ERROR", "FATAL", "WARN")) else None
        return line.strip() or None

    level, msg = entry.get("level", "INFO"), entry.get("msg", "")
    ctx = entry.get("ctx") or {}
    colour = RED if level in {"ERROR", "CRITICAL"} else YELLOW if level == "WARNING" else ""
    if msg == "request" and service == "api":
        if ctx.get("route") in QUIET_ROUTES and not verbose:
            return None
        status = ctx.get("status")
        tone = (
            RED
            if isinstance(status, int) and status >= 500
            else YELLOW
            if isinstance(status, int) and status >= 400
            else ""
        )
        return f"{tone}{ctx.get('method')} /v1{ctx.get('route')} -> {status}{RESET}  {DIM}{ctx.get('duration_ms')} ms{RESET}"
    if service == "web":
        if msg == "page":
            who = "signed in" if ctx.get("signed_in") else "visitor"
            return f"{ctx.get('method')} {ctx.get('path')}  {DIM}{who}{'  token renewed' if ctx.get('renewed') else ''}{RESET}"
        if msg == "api_call":
            status = ctx.get("status")
            tone = RED if isinstance(status, int) and status >= 500 else ""
            return f"{tone}browser -> {ctx.get('method')} {ctx.get('path')} -> {status}{RESET}  {DIM}{ctx.get('duration_ms')} ms{RESET}"
        details = " ".join(f"{k}={v}" for k, v in ctx.items())
        return f"{BOLD}{msg.replace('_', ' ')}{RESET} {DIM}{details}{RESET}"
    if service in {"worker", "beat"} and any(task in msg for task in ROUTINE_TASKS) and not verbose:
        return (
            None
            if "succeeded" in msg or "received" in msg or "Sending" in msg
            else f"{colour}{msg}{RESET}"
        )
    details = " ".join(f"{k}={v}" for k, v in ctx.items())
    return f"{colour}{msg}{RESET} {DIM}{details}{RESET}".strip()


def follow(verbose: bool) -> None:
    services = APP_SERVICES + (["postgres", "redis"] if verbose else [])
    note(
        f"Live activity. {DIM}Health checks and routine background jobs are hidden; --verbose shows them.{RESET}"
    )
    note(f"{DIM}Press Ctrl+C to stop.{RESET}")
    say()
    process = subprocess.Popen(  # noqa: S603
        [*COMPOSE, "logs", "-f", "--tail", "0", "--no-color", *services],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None  # noqa: S101 - set by PIPE above
    try:
        for raw in process.stdout:
            name, _, rest = raw.partition("|")
            service = name.strip().rsplit("-", 1)[0]
            shown = describe(service, rest.strip(), verbose)
            if shown:
                colour = COLOURS.get(service, "")
                say(f"{DIM}{datetime.now():%H:%M:%S}{RESET} {colour}{service:<9}{RESET} {shown}")
    finally:
        process.terminate()


# --- Commands -------------------------------------------------------------------------------------


def status() -> int:
    run([*COMPOSE, "ps", "--format", "table {{.Service}}\t{{.Status}}"])
    return 0


def main() -> int:
    if os.name == "nt":
        os.system("")  # noqa: S605, S607 - turns on colour in the Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Run the whole of Samvid with one command.")
    parser.add_argument("--status", action="store_true", help="show what's running, then exit")
    parser.add_argument("--stop", action="store_true", help="stop everything, keeping the data")
    parser.add_argument("--reset", action="store_true", help="stop everything and delete all data")
    parser.add_argument(
        "--check", action="store_true", help="run the end-to-end smoke check after starting"
    )
    parser.add_argument("--no-build", action="store_true", help="don't rebuild the images")
    parser.add_argument("--no-seed", action="store_true", help="don't create demo accounts")
    parser.add_argument(
        "--keep-running", action="store_true", help="leave everything running after Ctrl+C"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="show every log line, including infrastructure"
    )
    parser.add_argument("--open", action="store_true", help="open the web app in a browser")
    parser.add_argument("--show-password", action="store_true", help="print the demo password")
    args = parser.parse_args()

    banner()
    if not ensure_docker():
        return fail("Docker isn't available. Install or start Docker Desktop, then run this again.")
    ensure_env()

    if args.status:
        models()
        return status()
    if args.stop:
        note("Stopping everything. Your data is kept.")
        return run([*COMPOSE, "stop"])
    if args.reset:
        answer = input(
            "This deletes every database, account and demo record. Type 'delete' to go on: "
        )
        if answer.strip() != "delete":
            return fail("Nothing was deleted.")
        return run([*COMPOSE, "down", "-v"])

    if not start(build=not args.no_build):
        return fail(
            "Something didn't start. The messages above say which. Try --verbose, or see docs/runbook_local_stack.md."
        )
    models()
    if not args.no_seed:
        seed(args.show_password)
    if args.check:
        uv = shutil.which("uv")
        if uv:
            note("Running the end-to-end smoke check...")
            run(
                [
                    uv,
                    "run",
                    "--project",
                    str(ROOT / "backend"),
                    "python",
                    str(ROOT / "scripts" / "smoke_stack.py"),
                ],
                cwd=ROOT / "backend",
            )
    if args.open:
        webbrowser.open(f"{WEB}/en")

    try:
        follow(args.verbose)
    except KeyboardInterrupt:
        say()
    if args.keep_running:
        note("Left running. Stop later with: python Run_Samvid.py --stop")
        return 0
    note(
        "Stopping everything. Your data is kept. Start again with: python Run_Samvid.py --no-build"
    )
    return run([*COMPOSE, "stop"], quiet=True)


if __name__ == "__main__":
    sys.exit(main())
