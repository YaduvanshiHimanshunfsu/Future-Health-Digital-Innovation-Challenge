"""Check that this copy of the project is complete, and that git can keep it that way.

Two different faults look identical to someone who has just downloaded the project and got a
ModuleNotFoundError out of a container: a download that lost files, and a .gitignore rule that
quietly excluded a source folder. This checks for both.

The second check is the one worth running in CI. `backend/app/models/` was absent from every clone
because .gitignore carried an unanchored `models/`, written for downloaded model weights. Nothing
failed on the machine the code was written on, because there the files were present.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from Run_Samvid import REQUIRED  # noqa: E402 - needs ROOT on sys.path first

# Where hand-written code lives. A file under one of these must never be ignored.
SOURCE_ROOTS = ("backend/", "frontend/", "infra/", "scripts/", "docs/")
SOURCE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml", ".sql", ".toml")


def out(text: str = "") -> None:
    sys.stdout.write(f"{text}\n")


def tracked_files() -> list[str]:
    result = subprocess.run(  # noqa: S603 - fixed argument list
        ["git", "ls-files"],  # noqa: S607 - git is found on PATH, as everywhere else here
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def missing_paths() -> list[str]:
    """Required paths that are absent, or are directories with nothing in them.

    Git stores no empty directories, so a package lost this way often survives as a bare folder
    left behind by an earlier run.
    """
    gone = []
    for relative in REQUIRED:
        path = ROOT / relative
        if not path.exists() or (path.is_dir() and not any(path.iterdir())):
            gone.append(relative)
    return gone


def ignored_source() -> list[str]:
    """Tracked source files that .gitignore would exclude if they were added again today.

    `--no-index` makes git apply the ignore rules to paths it already tracks, which it otherwise
    skips. That is the blind spot: a file committed before the rule existed keeps working, while
    anything added next to it afterwards is dropped without a word.
    """
    candidates = [
        path
        for path in tracked_files()
        if path.startswith(SOURCE_ROOTS) and path.endswith(SOURCE_SUFFIXES)
    ]
    if not candidates:
        return []
    # Bytes, not text: on Windows a text-mode pipe rewrites each newline as CR+LF, and git would
    # then test paths with a trailing carriage return and match nothing.
    result = subprocess.run(  # noqa: S603 - fixed argument list
        ["git", "check-ignore", "--no-index", "--stdin"],  # noqa: S607 - git from PATH
        cwd=ROOT,
        input="\n".join(candidates).encode(),
        capture_output=True,
        check=False,
    )
    return [line for line in result.stdout.decode().splitlines() if line]


def main() -> int:
    problems = 0

    gone = missing_paths()
    if gone:
        problems += 1
        out("Missing or empty, and the stack needs every one of these:")
        for relative in gone:
            out(f"  - {relative}")
        out()
        out("This copy is incomplete. Clone the repository again, or run 'git pull'.")
        out()
    else:
        out(f"All {len(REQUIRED)} required paths are present.")

    ignored = ignored_source()
    if ignored:
        problems += 1
        out("These source files are tracked, but .gitignore excludes them:")
        for path in ignored:
            out(f"  - {path}")
        out()
        out("Anything added next to one of these would be skipped without a word. Anchor the")
        out("rule in .gitignore: '/models/' matches only the root, where 'models/' matches at")
        out("every depth.")
        out()
    else:
        out("No .gitignore rule matches a source file.")

    if problems:
        return 1
    out("This copy is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
