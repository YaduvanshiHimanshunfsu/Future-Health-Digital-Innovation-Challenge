"""Run the whole of Samvid with one command, from a fresh clone.

    python Run_Samvid.py                 set up if needed, start everything, show live activity
    python Run_Samvid.py --setup         walk through the first-run setup again
    python Run_Samvid.py --status        show what's running and which AI model answers
    python Run_Samvid.py --stop          stop everything, keeping the data
    python Run_Samvid.py --reset         stop everything and delete all data (asks first)
    python Run_Samvid.py --check         start, then the end-to-end smoke check
    python Run_Samvid.py --verify        start, then every stack check: smoke, load, log scan
    python Run_Samvid.py --eval          run the safety evaluations, per language
    python Run_Samvid.py --security      run every scanner and save the outputs

Other options: --no-build, --no-seed, --keep-running, --verbose, --open, --show-password, --yes,
--no-colour.

On a first run this checks what's installed, offers to install what's missing, asks for a Gemini API
key if you have one, builds the whole project, and prints where to go. Everything runs on this
machine, and all data is synthetic. Each run is also written to logs/, with secrets removed.

Updated at the end of every phase: see PHASES below.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
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
from typing import TextIO

# ruff targets 3.12 for the backend, but this file runs on whatever Python someone has, so
# the check stays and gives them a message instead of a crash.
if sys.version_info < (3, 9):  # noqa: UP036
    sys.stderr.write(
        "Samvid's launcher needs Python 3.9 or newer, and you have "
        f"{sys.version_info.major}.{sys.version_info.minor}.\n"
        "Install a current Python from https://www.python.org/downloads/, then run this again.\n"
    )
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent
INFRA = ROOT / "infra"
ENV_FILE = INFRA / ".env"
LOG_DIR = ROOT / "logs"
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

PROJECT = "Samvid"
DEVANAGARI = "\u0938\u0902\u0935\u093f\u0926\u094d"  # संविद् — Sanskrit for knowledge and consent
TAGLINE = "Understanding genetic carrier results, privately."
TEAM = "Vigyan_Viveka_Vijaya"
CHALLENGE = "Future Health Digital Innovation Challenge 2026 \u00b7 Fertility Challenge 03"
# Add your names here, as you want them shown. Left empty on purpose: nobody's name is guessed.
MEMBERS: list[str] = []

ABOUT = [
    "Carrier screening tells people they carry a gene change, in words most of us misread:",
    '"carrier" is heard as "ill", and "nothing shared" as "no risk at all". Samvid explains the',
    "result in plain language, keeps every sharing decision with the person, and hands anything",
    "clinical or distressing to a qualified human being.",
]
UNIQUE = [
    ("Numbers come from code", "a tested engine, never an AI"),
    ("An AI only explains", "every draft is checked, or a reviewed one is used"),
    ("Hard questions reach people", "health, pregnancy, pressure, distress"),
    ("Uncertain means no number", "a VUS gets words and a counsellor"),
    ("Consent is the data model", "two independent checks, either can refuse"),
    ("Works with no AI at all", "reviewed text answers if no model is reachable"),
    ("Global by design", "a new country is settings, not code"),
]
NEVER = "It never diagnoses, never says whether to marry or conceive, and never contacts relatives."

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
    (
        "4",
        "Explanations by Gemini or local Ollama, checked, with templates as the fallback",
        "done",
    ),
    ("5", "Care pathway, booking, FHIR referrals, centres, understanding checks, metrics", "done"),
    (
        "6",
        "Evaluation, security scans, submission documents (needs people for the rest)",
        "in progress",
    ),
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

PLACES = [
    ("The web app", f"{WEB}/en", "start here"),
    ("A person's care steps", f"{WEB}/en/app/journey", "sign in first"),
    ("Check understanding", f"{WEB}/en/app/check", "sign in first"),
    ("Counsellor queue", f"{WEB}/en/counsellor", "demo-counsellor"),
    ("Programme metrics", f"{WEB}/en/admin", "demo-coordinator"),
    ("Centre finder", f"{WEB}/en/centres", "no account needed"),
    ("API documentation", f"{API}/docs", "every endpoint"),
    ("Sign-in administration", KEYCLOAK, "Keycloak"),
]

SERVICE_COLOURS = {
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
APP_SERVICES = ["web", "api", "worker", "beat", "openfga", "keycloak"]
QUIET_ROUTES = {"/health", "/ready"}
ROUTINE_TASKS = ("samvid.apply_authz_outbox", "samvid.reconcile_authz", "samvid.ping")
GEMINI_PROBE = "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1"
GEMINI_KEY_SHAPE = re.compile(r"^AIza[0-9A-Za-z_\-]{30,45}$")

# Named so no f-string has to hold a backslash: that needs Python 3.12, and this file runs on
# whatever Python someone already has.
TICK, CROSS, WARN_MARK, ARROW, DOT = "\u2714", "\u2718", "\u26a0", "\u2192", "\u00b7"
BOX_H, BOX_V = "\u2500", "\u2502"
BOX_TL, BOX_TR, BOX_BL, BOX_BR = "\u250c", "\u2510", "\u2514", "\u2518"


# --- Terminal --------------------------------------------------------------------------------------

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
# Values that must never reach the log file, however they got here.
_SECRETS: set[str] = set()
_LOG: TextIO | None = None
_COLOUR = True
_WIDE = True
_STEP = 0
_STEPS_TOTAL = 0


def _style(code: str) -> str:
    return code if _COLOUR else ""


def colour(name: str) -> str:
    return _style(SERVICE_COLOURS.get(name, ""))


def reset() -> str:
    return _style("\033[0m")


def bold() -> str:
    return _style("\033[1m")


def dim() -> str:
    return _style("\033[2m")


def red() -> str:
    return _style("\033[31m")


def green() -> str:
    return _style("\033[32m")


def yellow() -> str:
    return _style("\033[33m")


def glyph(fancy: str, plain: str) -> str:
    return fancy if _WIDE else plain


def say(text: str = "") -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()
    if _LOG is not None:
        line = _ANSI.sub("", text)
        for secret in _SECRETS:
            if secret:
                line = line.replace(secret, "<redacted>")
        _LOG.write(line + "\n")
        _LOG.flush()


def note(text: str, tone: str = "") -> None:
    stamp = f"{dim()}{datetime.now():%H:%M:%S}{reset()}"
    say(f"{stamp} {colour('launcher')}{'samvid':<9}{reset()} {tone}{text}{reset() if tone else ''}")


def ok(text: str) -> None:
    note(f"{green()}{glyph(TICK, 'OK')}{reset()} {text}")


def warn(text: str) -> None:
    note(f"{yellow()}{glyph(WARN_MARK, '!')}{reset()} {text}")


def bad(text: str) -> None:
    note(f"{red()}{glyph(CROSS, 'X')}{reset()} {text}")


def fail(text: str) -> int:
    bad(text)
    return 1


def visible(text: str) -> int:
    """How wide a line really is: colour codes take no space on screen."""
    return len(_ANSI.sub("", text))


def panel(title: str, lines: list[str], width: int = 96) -> None:
    """A titled box that sizes itself to its content. Colour codes don't count towards the width."""
    if not _WIDE:
        say("")
        say(f"== {title} ==")
        for line in lines:
            say(f"  {line}")
        say()
        return
    needed = max([visible(title) + 4, *(visible(line) + 2 for line in lines)])
    inner = min(needed, width)
    say()
    say(
        f"{colour('launcher')}{BOX_TL}{BOX_H} {bold()}{title}{reset()}{colour('launcher')} "
        f"{BOX_H * max(0, inner - 3 - len(_ANSI.sub('', title)))}{BOX_TR}{reset()}"
    )
    for line in lines:
        if visible(line) > inner - 2:
            # Colour goes, so the border stays true. An intact box reads better than a ragged one.
            line = _ANSI.sub("", line)[: inner - 3] + "\u2026"
        pad = max(0, inner - 1 - visible(line))
        say(
            f"{colour('launcher')}{BOX_V}{reset()} {line}{' ' * pad}{colour('launcher')}{BOX_V}{reset()}"
        )
    say(f"{colour('launcher')}{BOX_BL}{BOX_H * inner}{BOX_BR}{reset()}")
    say()


def step(title: str) -> None:
    global _STEP
    _STEP += 1
    counter = f"Step {_STEP} of {_STEPS_TOTAL}" if _STEPS_TOTAL else f"Step {_STEP}"
    bar = glyph(BOX_H, "-")
    say()
    say(
        f"{colour('launcher')}{bar * 3} {bold()}{counter}{reset()}{colour('launcher')} {DOT} "
        f"{title} {bar * max(3, 80 - len(title))}{reset()}"
    )


def ask(question: str, default: str = "y", auto: bool = False) -> bool:
    """A yes-or-no question. Returns the default when nobody can answer, or with --yes."""
    options = "[Y/n]" if default == "y" else "[y/N]"
    if auto or not sys.stdin.isatty():
        say(f"  {question} {options} {dim()}{default} (not asked){reset()}")
        return default == "y"
    try:
        answer = input(f"  {question} {options} ").strip().lower()
    except EOFError:
        answer = ""
    if _LOG is not None:
        _LOG.write(f"  {question} -> {answer or default}\n")
    return (answer or default).startswith("y")


def open_log() -> None:
    global _LOG
    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"samvid-{datetime.now():%Y%m%d-%H%M%S}.log"
    _LOG = path.open("w", encoding="utf-8")
    _LOG.write(f"Samvid launcher, {datetime.now():%Y-%m-%d %H:%M:%S}\n")
    _LOG.write(f"Python {sys.version.split()[0]} on {sys.platform}\n")
    _LOG.write("Secrets are replaced with <redacted>.\n\n")
    # Keep the last 20 runs, so a long demo week doesn't fill the folder.
    for old in sorted(LOG_DIR.glob("samvid-*.log"))[:-20]:
        old.unlink(missing_ok=True)


def run(command: list[str], *, quiet: bool = False, cwd: Path = ROOT) -> int:
    """Runs a fixed command from this file. `quiet` captures output and logs it."""
    if quiet:
        done = subprocess.run(  # noqa: S603
            command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        tail = (done.stdout + done.stderr).strip()
        if _LOG is not None and tail:
            _LOG.write(f"$ {' '.join(command)}\n{tail[-4000:]}\n")
        if done.returncode != 0:
            say(tail[-2000:])
        return done.returncode
    if _LOG is not None:
        _LOG.write(f"$ {' '.join(command)}\n")
    return subprocess.run(command, cwd=cwd, check=False).returncode  # noqa: S603


# --- Welcome ---------------------------------------------------------------------------------------


def welcome(brief: bool) -> None:
    say()
    title = f"{bold()}{PROJECT}{reset()}  {DEVANAGARI}"
    say(f"  {title}   {dim()}{TAGLINE}{reset()}")
    say(f"  {dim()}Team {TEAM}  {DOT}  {CHALLENGE}{reset()}")
    if MEMBERS:
        say(f"  {dim()}Members: {', '.join(MEMBERS)}{reset()}")
    say()
    if brief:
        done = sum(1 for _, _, state in PHASES if state == "done")
        say(
            f"  {dim()}{done} of {len(PHASES)} phases done. A prototype on synthetic data.{reset()}"
        )
        say()
        return

    panel("What this is", [*ABOUT, "", f"{yellow()}{NEVER}{reset()}"])
    panel(
        "What makes it different",
        [f"{bold()}{name}{reset()}{dim()} {DOT} {what}{reset()}" for name, what in UNIQUE],
    )
    say(f"  {bold()}Where the build stands{reset()}")
    for phase, what, state in PHASES:
        tone = green() if state == "done" else yellow() if state == "in progress" else dim()
        say(f"    {tone}{state:<12}{reset()} Phase {phase:<4} {dim()}{what}{reset()}")
    say()
    say(f"  {dim()}All data here is invented. No real person, result or family is in it.{reset()}")
    say()


# --- Prerequisites ---------------------------------------------------------------------------------


def docker_ready() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(["docker", "info"], capture_output=True, check=False).returncode == 0  # noqa: S607


def start_docker_desktop() -> bool:
    """Starts Docker Desktop if it's installed but not running, then waits for it."""
    places = [
        Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"),
        Path("/Applications/Docker.app"),
    ]
    found = next((p for p in places if p.exists()), None)
    if found is None:
        return False
    note("Docker isn't running. Starting Docker Desktop, which takes up to a minute...")
    opener = ["open", str(found)] if sys.platform == "darwin" else [str(found)]
    subprocess.Popen(opener)  # noqa: S603
    for _ in range(40):
        time.sleep(3)
        if docker_ready():
            ok("Docker is ready.")
            return True
    return False


def install_uv(auto: bool) -> bool:
    if not ask("Install uv now, with pip?", "y", auto):
        return False
    note("Installing uv...")
    if run([sys.executable, "-m", "pip", "install", "--upgrade", "uv"], quiet=True) != 0:
        warn("That didn't work. See https://docs.astral.sh/uv/getting-started/installation/")
        return False
    return shutil.which("uv") is not None


def sync_backend(auto: bool) -> None:
    """Installs the backend's Python packages, so the demo data and scripts can run."""
    uv = shutil.which("uv")
    if uv is None:
        return
    marker = ROOT / "backend" / ".venv"
    if marker.exists():
        ok("Backend packages are installed.")
        return
    if not ask("Install the backend's Python packages? About 200 MB.", "y", auto):
        return
    note("Installing. The first time takes a few minutes...")
    if run([uv, "sync", "--project", str(ROOT / "backend")], quiet=True) == 0:
        ok("Backend packages installed.")
    else:
        warn("That didn't finish. Demo accounts and the scripts may not work.")


# Paths the stack cannot start without. A zip taken from the web interface of a branch, a clone
# that was interrupted, or a .gitignore rule that matched a source folder all leave a tree that
# looks complete until Docker is three minutes into a build. A directory here must also be
# non-empty: git stores no empty directories, so a missing package often survives as a bare folder.
REQUIRED = [
    "backend/app/models",
    "backend/app/api",
    "backend/app/core",
    "backend/app/db",
    "backend/app/risk_engine",
    "backend/app/country_packs",
    "backend/alembic/versions",
    "backend/synthetic",
    "backend/pyproject.toml",
    "backend/uv.lock",
    "backend/Dockerfile",
    "frontend/app",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/Dockerfile",
    "infra/docker-compose.yml",
    "scripts/generate_env.py",
    "scripts/seed_demo.py",
]


def check_download() -> bool:
    """Confirms the download is complete, and names what's missing if it isn't."""
    missing = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.exists() or (path.is_dir() and not any(path.iterdir())):
            missing.append(relative)
    if not missing:
        return True

    bad(f"This copy of {PROJECT} is incomplete, so it can't start.")
    say()
    say("  These are missing or empty:")
    for relative in missing:
        say(f"      {red()}{glyph(CROSS, 'X')}{reset()} {relative}")
    say()
    say(f"  {bold()}Get a complete copy:{reset()}")
    say("      git clone <the repository URL> samvid")
    say("      cd samvid")
    say("      python Run_Samvid.py")
    say()
    say(f"  {dim()}If you already have a clone here, 'git pull' is enough. If you downloaded a")
    say("  zip instead, download it again from the repository's main page: a zip saved from a")
    say(f"  file listing holds only part of the project.{reset()}")
    return False


def prerequisites(auto: bool) -> bool:
    """Checks what's installed, installs what it safely can, and says what's optional."""
    step("What's installed")
    say(
        f"  {dim()}Docker is required. uv is needed for the demo accounts. The rest is optional.{reset()}"
    )
    say()

    if docker_ready():
        ok("Docker is installed and running.")
    elif start_docker_desktop():
        pass
    else:
        bad("Docker isn't available.")
        say()
        say("  Samvid runs as containers, so Docker does the rest of the installing for you:")
        say("  it builds Python, Node, PostgreSQL, Redis, Keycloak and OpenFGA inside the project.")
        say()
        say(
            f"  {bold()}Install Docker Desktop:{reset()} https://www.docker.com/products/docker-desktop/"
        )
        say(f"  {dim()}Start it, wait for the whale icon to settle, then run this again.{reset()}")
        return False

    if shutil.which("uv") is None:
        warn("uv isn't installed. It runs the demo accounts and the project's scripts.")
        if install_uv(auto):
            ok("uv installed.")
        else:
            warn("Going on without it: the app will run, but with no demo accounts.")
    else:
        ok("uv is installed.")
    sync_backend(auto)

    if shutil.which("node") is None:
        say(
            f"  {dim()}Node.js isn't installed. Only the browser tests need it; the web app is built"
        )
        say(f"  inside Docker. https://nodejs.org if you want to run those tests.{reset()}")
    else:
        ok("Node.js is installed, so the browser tests can run.")

    if get("http://127.0.0.1:11434/api/tags") == 200:
        ok("Ollama is running, so answers can be drafted on this machine, privately.")
    else:
        say(f"  {dim()}Ollama isn't running. It's optional: with it, an AI model drafts answers")
        say(f"  without anything leaving your computer. https://ollama.com, then:{reset()}")
        say(f"      {bold()}ollama pull qwen2.5:3b{reset()}")
        say(
            f"  {dim()}Without it, Samvid uses Gemini if you add a key, or its reviewed text.{reset()}"
        )
    return True


# --- Settings and the AI key -----------------------------------------------------------------------


def ensure_env() -> None:
    # Creates infra/.env on a first run, and fills in settings added since. Never changes a value.
    run([sys.executable, str(ROOT / "scripts" / "generate_env.py")], quiet=True)


def read_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    lines = ENV_FILE.read_text("utf-8").splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))


def setting(name: str, default: str = "") -> str:
    """Your environment first, then infra/.env, the same order Docker Compose uses."""
    return os.environ.get(name) or read_env().get(name, "") or default


def write_env(name: str, value: str) -> None:
    """Replaces one setting in infra/.env, keeping every other line as it is."""
    lines = ENV_FILE.read_text("utf-8").splitlines() if ENV_FILE.exists() else []
    replaced = False
    for index, line in enumerate(lines):
        if line.startswith(f"{name}="):
            lines[index] = f"{name}={value}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{name}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gemini_status(key: str) -> int:
    """The HTTP status Google gives this key. 0 means we couldn't reach them."""
    request = urllib.request.Request(GEMINI_PROBE, headers={"x-goog-api-key": key})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - fixed https URL
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except OSError:
        return 0


def ai_setup(auto: bool, force: bool) -> None:
    """Asks for a Gemini key once, checks it with Google, and saves it to infra/.env."""
    step("AI model")
    existing = setting("GEMINI_API_KEY")
    if existing:
        _SECRETS.add(existing)
        code = gemini_status(existing)
        if code == 200:
            ok("A Gemini key is already set, and Google accepts it.")
            if not force:
                return
        else:
            warn(f"The Gemini key already set is rejected by Google (status {code}).")
    say(f"  {dim()}Gemini drafts explanations and double-checks which questions need a person.")
    say("  It is optional. Without it Samvid uses Ollama if it's running, then its reviewed text,")
    say(f"  and every safety rule still applies. Only redacted words are ever sent.{reset()}")
    say()
    say(
        f"  Get a free key at {bold()}https://aistudio.google.com/apikey{reset()} {dim()}(it starts with AIza){reset()}"
    )
    say()
    if auto or not sys.stdin.isatty():
        say(
            f"  {dim()}Not asking, since nobody can answer. Set GEMINI_API_KEY later, or run --setup.{reset()}"
        )
        return
    for attempt in range(3):
        try:
            key = getpass.getpass("  Paste your Gemini API key (or press Enter to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            say()
            return
        if not key:
            say(f"  {dim()}Skipped. Samvid will use Ollama or its reviewed text.{reset()}")
            return
        _SECRETS.add(key)
        if not GEMINI_KEY_SHAPE.match(key):
            warn(
                "That doesn't look like an AI Studio key, which starts with AIza. Checking anyway..."
            )
        note("Checking it with Google...")
        code = gemini_status(key)
        if code == 200:
            write_env("GEMINI_API_KEY", key)
            # Compose reads the shell environment before infra/.env, so set it here too, or an old
            # key already in your environment would keep winning.
            os.environ["GEMINI_API_KEY"] = key
            ok("Google accepts it. Saved to infra/.env, which git never commits.")
            return
        if code in (400, 401, 403):
            bad(f"Google rejected that key (status {code}).")
            if attempt < 2 and not ask("Try pasting it again?", "y"):
                break
        else:
            warn(f"Couldn't reach Google (status {code}). Check your connection.")
            if ask("Save the key anyway and carry on?", "y"):
                write_env("GEMINI_API_KEY", key)
                os.environ["GEMINI_API_KEY"] = key
                ok("Saved to infra/.env.")
            return
    say(f"  {dim()}Carrying on without Gemini.{reset()}")


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
                note(f"  gemini    {yellow()}no key set, so it's skipped{reset()}")
                continue
            _SECRETS.add(key)
            code = gemini_status(key)
            if code == 200:
                note(
                    f"  gemini    {green()}ready{reset()}, model {setting('GEMINI_MODEL', 'gemini-2.5-flash')}"
                )
            elif code in (400, 401, 403):
                note(
                    f"  gemini    {red()}Google rejected the key (status {code}){reset()}. "
                    "Make one at aistudio.google.com/apikey, then run --setup."
                )
            else:
                note(f"  gemini    {yellow()}not reachable from here (status {code}){reset()}")
        elif provider == "ollama":
            tag = setting("OLLAMA_MODEL", "qwen2.5:3b")
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:11434/api/tags", timeout=3
                ) as response:  # noqa: S310 - local only
                    names = [m.get("name") for m in json.load(response).get("models", [])]
            except (OSError, ValueError):
                note(f"  ollama    {yellow()}not running on this machine{reset()}")
                continue
            if tag in names:
                note(f"  ollama    {green()}ready{reset()}, model {tag}, on this machine only")
            else:
                note(
                    f"  ollama    {yellow()}running, but {tag} isn't pulled. Run: ollama pull {tag}{reset()}"
                )
        elif provider != "template":
            note(f"  {provider:<9} configured in infra/.env")


# --- Starting --------------------------------------------------------------------------------------


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


def build_and_start(build: bool) -> bool:
    step("Building and starting the project")
    say(f"  {dim()}Eight services: the web app, the API, two workers, PostgreSQL, Redis, Keycloak")
    say(
        f"  for sign-in and OpenFGA for permissions. Docker installs everything they need.{reset()}"
    )
    if build:
        say(
            f"  {dim()}A first build takes a few minutes. Later starts take under a minute.{reset()}"
        )
    say()
    command = [*COMPOSE, "up", "-d", "--wait"]
    if build:
        command.insert(len(COMPOSE) + 2, "--build")
    if run(command) != 0:
        return False
    say()
    for name, url in (
        ("web app", f"{WEB}/en"),
        ("API", f"{API}/v1/ready"),
        ("sign-in", "http://127.0.0.1:8080/realms/samvid"),
    ):
        status_code = get(url)
        state = (
            f"{green()}ready{reset()}"
            if 200 <= status_code < 400
            else f"{red()}status {status_code}{reset()}"
        )
        note(f"  {name:<9} {state}  {dim()}{url}{reset()}")
    if port_shadowed(3000):
        warn(
            "Something else is answering on [::1]:3000, probably an old `next start`. "
            "Browsers may reach it instead of this app."
        )
    return True


def demo_data() -> None:
    step("Demo accounts and synthetic data")
    uv = shutil.which("uv")
    if uv is None:
        warn("uv isn't installed, so there are no demo accounts. See docs/runbook_local_stack.md.")
        return
    backend = ROOT / "backend"
    if not (backend / "synthetic" / "out" / "ae-abu-dhabi" / "personas" / "fatima.json").exists():
        note("Generating the synthetic population. Seeded, so it comes out the same every time...")
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
        warn("Demo accounts couldn't be created. The app still runs.")
        return
    ok("Demo accounts ready.")
    note("Adding synthetic programme activity, so the metrics dashboard has something to show...")
    if (
        run([*COMPOSE, "exec", "-T", "api", "python", "-m", "app.ops.seed_metrics"], quiet=True)
        != 0
    ):
        warn("The synthetic metrics couldn't be added. The dashboard will show mostly '<10'.")
    else:
        ok("Synthetic programme activity added.")


def where_to_look(show_password: bool) -> None:
    step("Where to go")
    password = read_env().get("DEMO_PASSWORD", "")
    if password:
        _SECRETS.add(password)
    panel(
        "Open these",
        [
            f"{bold()}{label:<24}{reset()} {colour('web')}{url:<38}{reset()} {dim()}{hint}{reset()}"
            for label, url, hint in PLACES
        ],
    )
    shown = password if show_password else "in infra/.env as DEMO_PASSWORD (or use --show-password)"
    panel(
        "Demo accounts",
        [
            *[
                f"{colour('web')}{name:<18}{reset()} {dim()}{what}{reset()}"
                for name, what in DEMO_ACCOUNTS
            ],
            "",
            f'Sign in from the web app with {bold()}"Start privately"{reset()}.',
            f"Password for all of them: {bold()}{shown}{reset()}",
        ],
    )


# --- Live view -------------------------------------------------------------------------------------


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
    tone = red() if level in {"ERROR", "CRITICAL"} else yellow() if level == "WARNING" else ""
    if msg == "request" and service == "api":
        if ctx.get("route") in QUIET_ROUTES and not verbose:
            return None
        status_code = ctx.get("status")
        mark = (
            red()
            if isinstance(status_code, int) and status_code >= 500
            else yellow()
            if isinstance(status_code, int) and status_code >= 400
            else ""
        )
        arrow = glyph(ARROW, "->")
        return (
            f"{mark}{ctx.get('method')} /v1{ctx.get('route')} {arrow} {status_code}{reset()}  "
            f"{dim()}{ctx.get('duration_ms')} ms{reset()}"
        )
    if service == "web":
        if msg == "page":
            who = "signed in" if ctx.get("signed_in") else "visitor"
            renewed = "  token renewed" if ctx.get("renewed") else ""
            return f"{ctx.get('method')} {ctx.get('path')}  {dim()}{who}{renewed}{reset()}"
        if msg == "api_call":
            status_code = ctx.get("status")
            mark = red() if isinstance(status_code, int) and status_code >= 500 else ""
            arrow = glyph(ARROW, "->")
            return (
                f"{mark}browser {arrow} {ctx.get('method')} {ctx.get('path')} {arrow} "
                f"{status_code}{reset()}  {dim()}{ctx.get('duration_ms')} ms{reset()}"
            )
        details = " ".join(f"{k}={v}" for k, v in ctx.items())
        return f"{bold()}{msg.replace('_', ' ')}{reset()} {dim()}{details}{reset()}"
    if service in {"worker", "beat"} and any(task in msg for task in ROUTINE_TASKS) and not verbose:
        quiet_words = ("succeeded", "received", "Sending")
        return None if any(word in msg for word in quiet_words) else f"{tone}{msg}{reset()}"
    details = " ".join(f"{k}={v}" for k, v in ctx.items())
    return f"{tone}{msg}{reset()} {dim()}{details}{reset()}".strip()


def follow(verbose: bool) -> None:
    services = APP_SERVICES + (["postgres", "redis"] if verbose else [])
    step("Live activity")
    say(f"  {dim()}Every page opened, every call the browser makes, and every API request, as they")
    say("  happen. Health checks and routine background jobs are hidden; --verbose shows them.")
    say(f"  No identifier, token or invitation code is ever printed.{reset()}")
    say(f"  {bold()}Press Ctrl+C to stop.{reset()}")
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
                stamp = f"{dim()}{datetime.now():%H:%M:%S}{reset()}"
                say(f"{stamp} {colour(service)}{service:<9}{reset()} {shown}")
    finally:
        process.terminate()


# --- Checks ----------------------------------------------------------------------------------------


def uv_run(script: str, *args: str) -> int:
    """A project script, run in the backend's environment."""
    uv = shutil.which("uv")
    if uv is None:
        warn(f"uv isn't installed, so {script} can't run.")
        return 1
    backend = ROOT / "backend"
    return run(
        [uv, "run", "--project", str(backend), "python", str(ROOT / "scripts" / script), *args],
        cwd=backend,
    )


def first_model() -> str | None:
    """The model --eval should use: Gemini if its key works, else Ollama if it's running."""
    key = setting("GEMINI_API_KEY")
    if key and gemini_status(key) == 200:
        return "gemini"
    if get("http://127.0.0.1:11434/api/tags") == 200:
        return "ollama"
    return None


def evaluate() -> int:
    note("Safety evaluations. Reports go to docs/evaluation/, with every failure listed.")
    worst = 0
    for script in ("eval_router.py", "eval_answers.py"):
        note(f"{script}, templates and rules only...")
        worst = max(worst, uv_run(script))
    chosen = first_model()
    if chosen is None:
        warn("No AI model reachable, so only the templates-only runs were done.")
        return worst
    for script in ("eval_router.py", "eval_answers.py"):
        note(f"{script} with {chosen}. A local model takes about half an hour...")
        worst = max(worst, uv_run(script, "--model", chosen))
    ok("Done. See docs/evaluation/ for the per-language tables.")
    return worst


def security() -> int:
    """Every scanner, with outputs saved for the submission (V6.3.1)."""
    scans = ROOT / "docs" / "security" / "scans"
    scans.mkdir(parents=True, exist_ok=True)
    uv = shutil.which("uv")
    results: list[tuple[str, int]] = []

    def saved(name: str, command: list[str], cwd: Path) -> None:
        done = subprocess.run(  # noqa: S603 - fixed commands from this file only
            command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        (scans / name).write_text(done.stdout + done.stderr, encoding="utf-8")
        results.append((name, done.returncode))

    if uv:
        backend = ROOT / "backend"
        saved("bandit.txt", [uv, "run", "bandit", "-r", "app", "-c", "pyproject.toml"], backend)
        saved("pip_audit.txt", [uv, "run", "pip-audit"], backend)
    npm = shutil.which("npm")
    if npm:
        saved("npm_audit.txt", [npm, "audit"], ROOT / "frontend")
    saved(
        "gitleaks_history.txt",
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{ROOT}:/repo:ro",
            "zricethezav/gitleaks:v8.21.2",
            "git",
            "/repo",
            "--redact",
            "--no-banner",
        ],
        ROOT,
    )
    for image in ("samvid-backend:dev", "samvid-web:dev"):
        saved(
            f"trivy_{image.split(':')[0]}.txt",
            [
                "docker",
                "run",
                "--rm",
                "-v",
                "//var/run/docker.sock:/var/run/docker.sock",
                "-v",
                "samvid-trivy-cache:/root/.cache",
                "aquasec/trivy:0.58.1",
                "image",
                "--quiet",
                "--severity",
                "HIGH,CRITICAL",
                "--ignore-unfixed",
                "--format",
                "table",
                image,
            ],
            ROOT,
        )
    for name, code in results:
        state = (
            f"{green()}clean{reset()}"
            if code == 0
            else f"{red()}findings or error (exit {code}){reset()}"
        )
        note(f"  {name:<28} {state}")
    ok("Saved in docs/security/scans/.")
    return max((code for _, code in results), default=0)


def verify() -> int:
    """Stack-level checks after a start: the smoke test, the load test, and the log scan."""
    scans = ROOT / "docs" / "security" / "scans"
    scans.mkdir(parents=True, exist_ok=True)
    worst = 0
    note("Smoke test on the real stack (it stops and restarts OpenFGA on purpose)...")
    worst = max(worst, uv_run("smoke_stack.py"))
    note("Load test: non-AI routes, p95 target 300 ms...")
    worst = max(worst, uv_run("load_smoke.py"))
    note("Scanning every service's logs for IDs, genes, names, tokens and emails...")
    done = subprocess.run(  # noqa: S603 - fixed command from this file only
        [sys.executable, str(ROOT / "scripts" / "scan_logs.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (scans / "log_scan.txt").write_text(done.stdout + done.stderr, encoding="utf-8")
    say(done.stdout)
    return max(worst, done.returncode)


def status() -> int:
    return run([*COMPOSE, "ps", "--format", "table {{.Service}}\t{{.Status}}"])


# --- Main ------------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the whole of Samvid with one command.",
        epilog="On a first run this sets everything up. Logs are written to logs/.",
    )
    for flag, help_text in (
        ("--setup", "walk through the first-run setup again"),
        ("--status", "show what's running and which AI model answers"),
        ("--stop", "stop everything, keeping the data"),
        ("--reset", "stop everything and delete all data"),
        ("--check", "start, then the end-to-end smoke check"),
        ("--verify", "start, then the smoke test, load test and log scan"),
        ("--eval", "run the safety evaluations, then exit"),
        ("--security", "run every scanner and save outputs, then exit"),
        ("--no-build", "don't rebuild the images"),
        ("--no-seed", "don't create demo accounts"),
        ("--keep-running", "leave everything running after Ctrl+C"),
        ("--verbose", "show every log line, including infrastructure"),
        ("--open", "open the web app in a browser"),
        ("--show-password", "print the demo password"),
        ("--yes", "accept every prompt, for an unattended run"),
        ("--no-colour", "plain text, no colour"),
    ):
        parser.add_argument(flag, action="store_true", help=help_text)
    return parser


def prepare_terminal(no_colour: bool) -> None:
    global _COLOUR, _WIDE
    if os.name == "nt":
        os.system("")  # noqa: S605, S607 - turns on colour in the Windows console
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _COLOUR = (
        not no_colour
        and os.environ.get("NO_COLOR") is None
        and os.environ.get("TERM") != "dumb"
        and sys.stdout.isatty()
    )
    try:
        (BOX_TL + TICK + ARROW).encode(sys.stdout.encoding or "utf-8")
        _WIDE = True
    except (UnicodeEncodeError, LookupError):
        _WIDE = False


def main() -> int:
    global _STEPS_TOTAL
    args = build_parser().parse_args()
    prepare_terminal(args.no_colour)
    open_log()

    first_run = not ENV_FILE.exists()
    full_setup = first_run or args.setup
    short = any([args.status, args.stop, args.reset, args.eval, args.security])
    welcome(brief=not full_setup or short)

    if not check_download():
        return 1

    if short:
        if not docker_ready() and not start_docker_desktop():
            return fail("Docker isn't available. Start Docker Desktop, then run this again.")
        ensure_env()
        if args.status:
            models()
            return status()
        if args.eval:
            return evaluate()
        if args.security:
            return security()
        if args.stop:
            note("Stopping everything. Your data is kept.")
            return run([*COMPOSE, "stop"])
        answer = input(
            "This deletes every database, account and demo record. Type 'delete' to go on: "
        )
        if answer.strip() != "delete":
            return fail("Nothing was deleted.")
        return run([*COMPOSE, "down", "-v"])

    # Steps: installed, settings, AI model, build, demo data, where to go, live activity.
    _STEPS_TOTAL = (7 if full_setup else 4) - (1 if args.no_seed else 0)
    if full_setup:
        if not prerequisites(args.yes):
            return 1
        step("Settings")
        ensure_env()
        ok("infra/.env is ready. It holds this machine's passwords and keys, and git ignores it.")
        ai_setup(args.yes, args.setup)
        models()
    else:
        if not docker_ready() and not start_docker_desktop():
            return fail("Docker isn't available. Start Docker Desktop, then run this again.")
        ensure_env()

    if not build_and_start(build=not args.no_build):
        return fail(
            "Something didn't start. The messages above say which. See docs/runbook_local_stack.md."
        )
    if not full_setup:
        models()
    if not args.no_seed:
        demo_data()
    where_to_look(args.show_password)
    if args.verify:
        verify()
    elif args.check:
        note("Running the end-to-end smoke check...")
        uv_run("smoke_stack.py")
    if args.open:
        webbrowser.open(f"{WEB}/en")

    try:
        follow(args.verbose)
    except KeyboardInterrupt:
        say()
    if _LOG is not None:
        note(f"{dim()}This run was logged to logs/{Path(_LOG.name).name}{reset()}")
    if args.keep_running:
        ok("Left running. Stop it later with: python Run_Samvid.py --stop")
        return 0
    note(
        "Stopping everything. Your data is kept. Start again with: python Run_Samvid.py --no-build"
    )
    return run([*COMPOSE, "stop"], quiet=True)


if __name__ == "__main__":
    sys.exit(main())
